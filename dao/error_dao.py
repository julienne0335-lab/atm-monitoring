"""
dao/error_dao.py ─ ATM·지점·은행 장애로그 테이블 담당 쿼리 모음
──────────────────────────────────────────────────────────────────────
[역할 분리 원칙]
  ✅ 이 파일에서 해야 할 것 : SQL 작성, cursor.execute(), fetchall()/fetchone()
  ❌ 이 파일에서 하면 안 됨 : 업무 규칙 검증, Flask request/session 접근

[담당 테이블]
  ATM장애로그, 지점장애로그, 은행장애로그
"""


# ============================================================
# ATM 장애로그
# ============================================================

def find_atm_error_logs(conn, atm_id, limit=10):
    """
    특정 ATM의 장애로그를 최근 N건 조회한다. (ATM 상세 페이지 장애 이력 탭)

    [데이터셋 Issue 2 관련]
      장애 상태인 ATM은 미처리 장애로그가 최소 1건 존재해야 함.
      이 쿼리 결과에서 처리상태='미처리' 인 건이 있으면 대시보드 경고 카운터가 올라감.

    [반환값]
      list of dict
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.장애ID, e.장애유형, e.상세내용, e.처리상태,
               e.발생일시, e.처리완료일시, ad.이름 AS 담당자명
        FROM ATM장애로그 e
        LEFT JOIN 관리자 ad ON e.관리자ID = ad.관리자ID
        WHERE e.ATM_ID = %s
        ORDER BY e.발생일시 DESC
        LIMIT %s
    """, (atm_id, limit))
    return cursor.fetchall()


def resolve_atm_error_logs(conn, atm_id):
    """
    ATM 복구(장애→정상) 시, 해당 ATM의 미처리 장애로그를 일괄 처리완료 처리한다.

    [데이터셋 Issue 2 핵심 해결 함수]
      service.change_status()가 "정상"으로 변경할 때만 이 함수를 호출.
      ATM 상태 컬럼과 장애로그 처리상태가 항상 동기화되도록 보장하는 로직.
      처리완료일시도 NOW()로 함께 기록하여 장애로그 시각 정합성(Issue 0) 유지.
    """
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE ATM장애로그
        SET 처리상태 = '처리완료', 처리완료일시 = NOW()
        WHERE ATM_ID = %s
          AND 처리상태 = '미처리'
    """, (atm_id,))


def find_atm_ids_by_branch(conn, branch_id):
    """지점 소속 ATM_ID 목록 반환 (BR-11용)"""
    cursor = conn.cursor()
    cursor.execute("SELECT ATM_ID FROM ATM WHERE 지점ID = %s", (branch_id,))
    return [row["ATM_ID"] for row in cursor.fetchall()]


def find_atm_ids_by_bank(conn, bank_id):
    """은행 소속 전체 ATM_ID 목록 반환 (BR-12용)"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.ATM_ID FROM ATM a
        JOIN 지점 b ON a.지점ID = b.지점ID
        WHERE b.은행ID = %s
    """, (bank_id,))
    return [row["ATM_ID"] for row in cursor.fetchall()]


def bulk_insert_atm_errors(conn, atm_ids, error_type, detail):
    """ATM 장애로그 일괄 INSERT (BR-11, BR-12용)"""
    cursor = conn.cursor()
    for atm_id in atm_ids:
        cursor.execute("""
            INSERT INTO ATM장애로그 (ATM_ID, 장애유형, 상세내용, 처리상태, 발생일시)
            VALUES (%s, %s, %s, '미처리', NOW())
        """, (atm_id, error_type, detail))


def find_branch_id_by_branch_error(conn, branch_error_id):
    """지점장애ID로 소속 지점ID 조회 (BR-14용)"""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 지점ID FROM 지점장애로그 WHERE 지점장애ID = %s", (branch_error_id,)
    )
    row = cursor.fetchone()
    return row["지점ID"] if row else None


def find_bank_id_by_bank_error(conn, bank_error_id):
    """은행장애ID로 소속 은행ID 조회 (BR-13용)"""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 은행ID FROM 은행장애로그 WHERE 은행장애ID = %s", (bank_error_id,)
    )
    row = cursor.fetchone()
    return row["은행ID"] if row else None


def find_unresolved_atm_error_count(conn, branch_id=None):
    """
    미처리 ATM 장애 건수를 집계한다. (대시보드 경고 배지 숫자 전용)

    [데이터셋 Issue 2 관련]
      이 값이 0보다 크면 대시보드에 빨간 경고 배지 표시.
      슈퍼관리자(branch_id=None)는 전 은행 합산 건수,
      일반관리자는 자신의 지점 소속 ATM 장애 건수만 조회.

    [반환값]
      int  예) 5
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) AS cnt
        FROM ATM장애로그 e
        JOIN ATM a ON e.ATM_ID = a.ATM_ID
        WHERE e.처리상태 = '미처리'
          AND (%s IS NULL OR a.지점ID = %s)
    """, (branch_id, branch_id))
    row = cursor.fetchone()
    return row["cnt"]


# ============================================================
# 지점 장애로그
# ============================================================

def insert_branch_error(conn, branch_id, error_type, detail):
    """
    지점 장애로그를 INSERT한다.
    """
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO 지점장애로그 (지점ID, 관리자ID, 장애유형, 상세내용, 처리상태, 발생일시)
        VALUES (%s, NULL, %s, %s, '미처리', NOW())
    """, (branch_id, error_type, detail))


def resolve_branch_error(conn, branch_error_id, admin_id):
    """
    지점 장애로그를 처리완료 처리한다.
    """
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE 지점장애로그
        SET 관리자ID = %s,
            처리상태 = '처리완료',
            처리완료일시 = NOW()
        WHERE 지점장애ID = %s
    """, (admin_id, branch_error_id))


def find_unresolved_branch_errors(conn):
    """
    미처리 지점 장애로그 목록을 조회한다.

    [반환값]
      list of dict  예) [{"지점장애ID": 1, "지점명": "강남", "장애유형": "통신", ...}, ...]
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.지점장애ID, e.지점ID, e.장애유형, e.상세내용,
               e.처리상태, e.발생일시, j.지점명
        FROM 지점장애로그 e
        JOIN 지점 j ON e.지점ID = j.지점ID
        WHERE e.처리상태 = '미처리'
        ORDER BY e.발생일시 DESC
    """)
    return cursor.fetchall()


def find_all_branch_errors(conn):
    """
    지점 장애로그 전체를 조회한다. (처리완료 포함)

    [반환값]
      list of dict
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.지점장애ID, e.지점ID, e.관리자ID, e.장애유형,
               e.상세내용, e.처리상태, e.발생일시, e.처리완료일시,
               j.지점명, ad.이름 AS 담당자명
        FROM 지점장애로그 e
        JOIN 지점 j ON e.지점ID = j.지점ID
        LEFT JOIN 관리자 ad ON e.관리자ID = ad.관리자ID
        ORDER BY e.발생일시 DESC
    """)
    return cursor.fetchall()


# ============================================================
# 은행 장애로그
# ============================================================

def insert_bank_error(conn, bank_id, error_type, detail):
    """
    은행 장애로그를 INSERT한다.
    """
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO 은행장애로그 (은행ID, 관리자ID, 장애유형, 상세내용, 처리상태, 발생일시)
        VALUES (%s, NULL, %s, %s, '미처리', NOW())
    """, (bank_id, error_type, detail))


def resolve_bank_error(conn, bank_error_id, admin_id):
    """
    은행 장애로그를 처리완료 처리한다.
    """
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE 은행장애로그
        SET 관리자ID = %s,
            처리상태 = '처리완료',
            처리완료일시 = NOW()
        WHERE 은행장애ID = %s
    """, (admin_id, bank_error_id))


def find_unresolved_bank_errors(conn):
    """
    미처리 은행 장애로그 목록을 조회한다.

    [반환값]
      list of dict  예) [{"은행장애ID": 1, "은행명": "A은행", "장애유형": "전산", ...}, ...]
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.은행장애ID, e.은행ID, e.장애유형, e.상세내용,
               e.처리상태, e.발생일시, b.은행명
        FROM 은행장애로그 e
        JOIN 은행 b ON e.은행ID = b.은행ID
        WHERE e.처리상태 = '미처리'
        ORDER BY e.발생일시 DESC
    """)
    return cursor.fetchall()


def find_all_bank_errors(conn):
    """
    은행 장애로그 전체를 조회한다. (처리완료 포함)

    [반환값]
      list of dict
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.은행장애ID, e.은행ID, e.관리자ID, e.장애유형,
               e.상세내용, e.처리상태, e.발생일시, e.처리완료일시,
               b.은행명, ad.이름 AS 담당자명
        FROM 은행장애로그 e
        JOIN 은행 b ON e.은행ID = b.은행ID
        LEFT JOIN 관리자 ad ON e.관리자ID = ad.관리자ID
        ORDER BY e.발생일시 DESC
    """)
    return cursor.fetchall()
