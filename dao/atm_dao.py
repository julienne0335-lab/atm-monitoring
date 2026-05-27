"""
dao/atm_dao.py ─ ATM, 현금보충 테이블 담당 쿼리 모음
──────────────────────────────────────────────────────────────────────
[역할 분리 원칙]
  ✅ 이 파일에서 해야 할 것 : SQL 작성, cursor.execute(), fetchall()/fetchone()
  ❌ 이 파일에서 하면 안 됨 : if/else 업무 규칙, Flask request/session 접근

[사용법]
  모든 함수는 첫 번째 인자로 conn(DB 연결 객체)을 받음.
  연결 열기(get_connection)와 닫기(conn.close)는 service 계층이 담당.
  SQL을 수정할 때는 이 파일만 수정하면 됨.

[장애로그 관련 함수]
  ATM 장애로그 쿼리는 dao/error_dao.py 로 이동됨.
  (find_atm_error_logs, resolve_atm_error_logs)
"""


def find_all(conn, branch_id=None, status=None, bank_id=None):
    """
    ATM 전체 목록을 조회한다.

    [파라미터]
      conn      : DB 연결 객체 (pymysql.connect 반환값)
      branch_id : 일반관리자용 지점 필터. None이면 전체.
      status    : 상태 필터. None이면 전체 / "정상"·"점검중"·"장애" 중 하나.
      bank_id   : 슈퍼관리자용 은행 필터. None이면 전체.

    [반환값]
      list of dict
      예) [{"ATM_ID": 1, "지점명": "강남", "상태": "정상", "현금잔량": 5000000, ...}, ...]

    [참조 테이블]
      ATM, 지점 (JOIN으로 지점명을 함께 가져옴)
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.ATM_ID AS ATM_id, a.상태, a.현금잔량, a.경고임계값,
               a.ATM현금상태, a.최종갱신일시, b.지점명, b.은행ID, c.은행명
        FROM ATM a
        JOIN 지점 b ON a.지점ID = b.지점ID
        JOIN 은행  c ON b.은행ID  = c.은행ID
        WHERE (%s IS NULL OR a.지점ID = %s)
          AND (%s IS NULL OR a.상태   = %s)
          AND (%s IS NULL OR b.은행ID = %s)
        ORDER BY a.ATM_ID
    """, (branch_id, branch_id, status, status, bank_id, bank_id))
    return cursor.fetchall()


def find_by_id(conn, atm_id):
    """
    ATM 단건 상세 조회. (ATM 상세 페이지에서 사용)

    [파라미터]
      atm_id : 조회할 ATM의 PK

    [반환값]
      dict  예) {"ATM_ID": 1, "지점명": "강남", "은행명": "A은행", "상태": "정상", ...}
      존재하지 않으면 None 반환 → route에서 404 처리에 활용.

    [참조 테이블]
      ATM, 지점, 은행 (JOIN으로 지점명·은행명 함께 조회)
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.ATM_ID AS ATM_id, a.지점ID, a.상태, a.현금잔량,
               a.경고임계값, a.ATM현금상태, a.최종갱신일시,
               b.지점명, b.주소, b.은행ID, c.은행명
        FROM ATM a
        JOIN 지점 b ON a.지점ID = b.지점ID
        JOIN 은행  c ON b.은행ID  = c.은행ID
        WHERE a.ATM_ID = %s
    """, (atm_id,))
    return cursor.fetchone()


def find_cash_alerts(conn, branch_id=None, bank_id=None):
    """
    현금잔량이 경고임계값 이하인 ATM 목록을 조회한다. (대시보드 경고 카드 전용)

    [데이터셋 Issue 7 관련]
      이 쿼리가 "현금잔량 <= 경고임계값" 조건을 걸어 경고 ATM을 찾는 핵심 SQL.
      데이터셋에 의도적으로 포함된 경고 케이스(ATM-1, ATM-6 등)가 여기서 조회됨.
      프론트엔드에서는 조회 결과가 있으면 경고 아이콘(노란/빨간)을 표시해야 함.

    [반환값]
      list of dict
      예) [{"ATM_ID": 1, "현금잔량": 300000, "경고임계값": 500000, "지점명": "강남"}, ...]
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.ATM_ID AS ATM_id, a.상태, a.현금잔량, a.경고임계값, a.ATM현금상태,
               b.지점명, c.은행명
        FROM ATM a
        JOIN 지점 b ON a.지점ID = b.지점ID
        JOIN 은행  c ON b.은행ID  = c.은행ID
        WHERE a.현금잔량 <= a.경고임계값
          AND (%s IS NULL OR a.지점ID = %s)
          AND (%s IS NULL OR b.은행ID = %s)
        ORDER BY (a.현금잔량 / a.경고임계값)
    """, (branch_id, branch_id, bank_id, bank_id))
    return cursor.fetchall()


def count_by_status(conn, branch_id=None, bank_id=None):
    """
    상태별 ATM 대수를 집계한다. (대시보드 요약 카드에 사용)

    [반환값]
      dict  예) {"정상": 21, "점검중": 6, "장애": 3}
      ※ 조회 결과가 없는 상태는 키가 없을 수 있으므로,
         service나 template에서 .get("정상", 0) 형태로 접근 권장.
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 상태, COUNT(*) AS cnt
        FROM ATM a
        JOIN 지점 b ON a.지점ID = b.지점ID
        WHERE (%s IS NULL OR a.지점ID = %s)
          AND (%s IS NULL OR b.은행ID = %s)
        GROUP BY 상태
    """, (branch_id, branch_id, bank_id, bank_id))
    rows = cursor.fetchall()
    return {row["상태"]: row["cnt"] for row in rows}


def update_status(conn, atm_id, new_status):
    """
    ATM의 상태 컬럼을 업데이트한다.

    [데이터셋 Issue 2 관련]
      이 함수는 service의 change_status()에서 호출됨.
      장애 → 정상 복구 시 resolve_error_logs()와 함께 트랜잭션으로 묶여 실행됨.
      즉, ATM 상태와 장애로그 처리상태가 항상 동기화되도록 service가 보장함.
      최종갱신일시도 함께 NOW()로 갱신하는 것이 핵심.

    [파라미터]
      new_status : "정상" / "점검중" / "장애" 중 하나
                   service.change_status()에서 유효성 검증 완료된 값만 전달됨. 
    """
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE ATM
        SET 상태 = %s, 최종갱신일시 = NOW()
        WHERE ATM_ID = %s
    """, (new_status, atm_id))


def update_cash_amount(conn, atm_id, amount):
    """
    ATM 현금잔량을 지정된 금액만큼 증가시키고, ATM현금상태를 자동 갱신한다.

    [주의]
      amount는 '추가할 금액'이지 '새로운 총액'이 아님.
      예) 현재 잔량 500만 + amount 300만 → 결과 800만 (덮어쓰기가 아닌 누적)

    [ATM현금상태 자동 갱신]
      보충 후 잔량이 경고임계값을 초과하면 '정상',
      여전히 이하이면 '현금부족경고'로 자동 업데이트.
      CASE WHEN에서 amount를 한 번 더 참조하므로 파라미터를 두 번 전달함.
    """
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE ATM
        SET 현금잔량    = 현금잔량 + %s,
            ATM현금상태 = CASE
                              WHEN (현금잔량 + %s) > 경고임계값 THEN '정상'
                              ELSE '현금부족경고'
                          END,
            최종갱신일시 = NOW()
        WHERE ATM_ID = %s
    """, (amount, amount, atm_id))


def insert_refill(conn, atm_id, admin_id, amount):
    """
    현금보충 이력을 현금보충 테이블에 INSERT한다.

    [데이터셋 Issue 3 관련]
      service.process_refill()에서 관리자-ATM 소속 은행 일치 검증 후
      이 함수가 호출됨. 타 은행 관리자가 시도하면 service에서 ValueError가
      발생하므로, 이 INSERT까지 도달하는 레코드는 모두 유효한 데이터임. 
    """
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO 현금보충 (ATM_ID, 관리자ID, 보충금액, 보충일시)
        VALUES (%s, %s, %s, NOW())
    """, (atm_id, admin_id, amount))


def find_refill_logs(conn, atm_id, limit=5):
    """
    특정 ATM의 현금보충 이력을 최근 N건 조회한다. (ATM 상세 페이지 하단 탭)

    [파라미터]
      limit : 기본값 5건. ATM 상세 페이지에서 최근 5건만 미리보기 형태로 표시. 
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.보충ID, r.보충금액, r.보충일시, ad.이름 AS 담당자명
        FROM 현금보충 r
        JOIN 관리자 ad ON r.관리자ID = ad.관리자ID
        WHERE r.ATM_ID = %s
        ORDER BY r.보충일시 DESC
        LIMIT %s
    """, (atm_id, limit))
    return cursor.fetchall()


def find_maintenance_logs(conn, atm_id, limit=5):
    """
    특정 ATM의 유지보수이력을 최근 N건 조회한다. (ATM 상세 페이지 전용)

    [참조 테이블]
      유지보수이력, 관리자, ATM장애로그 (LEFT JOIN - 장애 없는 정기점검도 포함)

    [반환값]
      list of dict  예) [{"이력ID": 1, "점검내용": "정기 점검", "담당자명": "김관리", ...}, ...]
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.이력ID, m.점검내용, m.점검일시,
               ad.이름 AS 담당자명,
               e.장애유형
        FROM 유지보수이력 m
        JOIN 관리자 ad ON m.관리자ID = ad.관리자ID
        LEFT JOIN ATM장애로그 e ON m.장애ID = e.장애ID
        WHERE m.ATM_ID = %s
        ORDER BY m.점검일시 DESC
        LIMIT %s
    """, (atm_id, limit))
    return cursor.fetchall()


def find_bank_id_by_atm(conn, atm_id):
    """
    ATM이 속한 은행ID를 조회한다.

    [데이터셋 Issue 3 해결을 위한 함수]
      현금보충 API에서 관리자 소속 은행과 ATM 소속 은행이 일치하는지 확인하기 위해
      service 계층의 process_refill()에서 호출됨.
      auth_dao.find_bank_id_by_admin()과 함께 쌍으로 사용됨.

    [반환값]
      int  예) 1  (A은행=1, B은행=2)
      ATM이 존재하지 않으면 None 반환. 
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.은행ID
        FROM ATM a
        JOIN 지점 b ON a.지점ID = b.지점ID
        WHERE a.ATM_ID = %s
    """, (atm_id,))
    row = cursor.fetchone()
    return row["은행ID"] if row else None
