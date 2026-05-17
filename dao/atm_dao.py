"""
dao/atm_dao.py ─ ATM, 현금보충, 장애로그 테이블 담당 쿼리 모음
──────────────────────────────────────────────────────────────────────
[역할 분리 원칙]
  ✅ 이 파일에서 해야 할 것 : SQL 작성, cursor.execute(), fetchall()/fetchone()
  ❌ 이 파일에서 하면 안 됨 : if/else 업무 규칙, Flask request/session 접근

[사용법]
  모든 함수는 첫 번째 인자로 conn(DB 연결 객체)을 받음.
  연결 열기(get_connection)와 닫기(conn.close)는 service 계층이 담당.
  SQL을 수정할 때는 이 파일만 수정하면 됨.
"""


def find_all(conn, branch_id=None, status=None):
    """
    ATM 전체 목록을 조회한다.

    [파라미터]
      conn      : DB 연결 객체 (pymysql.connect 반환값)
      branch_id : 일반 관리자용 지점 필터. None이면 전체(슈퍼관리자).
      status    : 상태 필터. None이면 전체 / "정상"·"점검중"·"장애" 중 하나.

    [반환값]
      list of dict
      예) [{"ATM_ID": 1, "지점명": "강남", "상태": "정상", "현금잔량": 5000000, ...}, ...]

    [참조 테이블]
      ATM, 지점 (JOIN으로 지점명을 함께 가져옴)

    [SQL 예시]
      SELECT a.ATM_ID, a.상태, a.현금잔량, a.경고임계값,
             a.최종갱신일시, b.지점명, b.은행ID
      FROM ATM a
      JOIN 지점 b ON a.지점ID = b.지점ID
      WHERE (%(branch_id)s IS NULL OR a.지점ID = %(branch_id)s)
        AND (%(status)s   IS NULL OR a.상태     = %(status)s)
      ORDER BY a.ATM_ID
    """
    pass


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

    [SQL 예시]
      SELECT a.*, b.지점명, b.은행ID, c.은행명
      FROM ATM a
      JOIN 지점 b ON a.지점ID = b.지점ID
      JOIN 은행  c ON b.은행ID  = c.은행ID
      WHERE a.ATM_ID = %(atm_id)s
    """
    pass


def find_cash_alerts(conn, branch_id=None):
    """
    현금잔량이 경고임계값 이하인 ATM 목록을 조회한다. (대시보드 경고 카드 전용)

    [데이터셋 Issue 7 관련]
      이 쿼리가 "현금잔량 <= 경고임계값" 조건을 걸어 경고 ATM을 찾는 핵심 SQL.
      데이터셋에 의도적으로 포함된 경고 케이스(ATM-1, ATM-6 등)가 여기서 조회됨.
      프론트엔드에서는 조회 결과가 있으면 경고 아이콘(노란/빨간)을 표시해야 함.

    [반환값]
      list of dict
      예) [{"ATM_ID": 1, "현금잔량": 300000, "경고임계값": 500000, "지점명": "강남"}, ...]

    [SQL 예시]
      SELECT a.ATM_ID, a.현금잔량, a.경고임계값, b.지점명
      FROM ATM a
      JOIN 지점 b ON a.지점ID = b.지점ID
      WHERE a.현금잔량 <= a.경고임계값
        AND (%(branch_id)s IS NULL OR a.지점ID = %(branch_id)s)
      ORDER BY (a.현금잔량 / a.경고임계값)  -- 위험도 낮은 순(가장 위험한 ATM 먼저)
    """
    pass


def count_by_status(conn, branch_id=None):
    """
    상태별 ATM 대수를 집계한다. (대시보드 요약 카드에 사용)

    [반환값]
      dict  예) {"정상": 21, "점검중": 6, "장애": 3}
      ※ 조회 결과가 없는 상태는 키가 없을 수 있으므로,
         service나 template에서 .get("정상", 0) 형태로 접근 권장.

    [SQL 예시]
      SELECT 상태, COUNT(*) AS cnt
      FROM ATM a
      JOIN 지점 b ON a.지점ID = b.지점ID
      WHERE (%(branch_id)s IS NULL OR a.지점ID = %(branch_id)s)
      GROUP BY 상태
    """
    pass


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

    [SQL 예시]
      UPDATE ATM
      SET 상태 = %(new_status)s, 최종갱신일시 = NOW()
      WHERE ATM_ID = %(atm_id)s
    """
    pass


def update_cash_amount(conn, atm_id, amount):
    """
    ATM 현금잔량을 지정된 금액만큼 증가시킨다. (현금 보충 시 사용)

    [주의]
      amount는 '추가할 금액'이지 '새로운 총액'이 아님.
      예) 현재 잔량 500만 + amount 300만 → 결과 800만 (덮어쓰기가 아닌 누적)

    [SQL 예시]
      UPDATE ATM
      SET 현금잔량 = 현금잔량 + %(amount)s, 최종갱신일시 = NOW()
      WHERE ATM_ID = %(atm_id)s
    """
    pass


def insert_refill(conn, atm_id, admin_id, amount):
    """
    현금보충 이력을 현금보충 테이블에 INSERT한다.

    [데이터셋 Issue 3 관련]
      service.process_refill()에서 관리자-ATM 소속 은행 일치 검증 후
      이 함수가 호출됨. 타 은행 관리자가 시도하면 service에서 ValueError가
      발생하므로, 이 INSERT까지 도달하는 레코드는 모두 유효한 데이터임.

    [SQL 예시]
      INSERT INTO 현금보충 (ATM_ID, 관리자ID, 보충금액, 보충일시)
      VALUES (%(atm_id)s, %(admin_id)s, %(amount)s, NOW())
    """
    pass


def find_refill_logs(conn, atm_id, limit=5):
    """
    특정 ATM의 현금보충 이력을 최근 N건 조회한다. (ATM 상세 페이지 하단 탭)

    [파라미터]
      limit : 기본값 5건. ATM 상세 페이지에서 최근 5건만 미리보기 형태로 표시.

    [SQL 예시]
      SELECT r.보충ID, r.보충금액, r.보충일시, ad.이름 AS 담당자명
      FROM 현금보충 r
      JOIN 관리자 ad ON r.관리자ID = ad.관리자ID
      WHERE r.ATM_ID = %(atm_id)s
      ORDER BY r.보충일시 DESC
      LIMIT %(limit)s
    """
    pass


def find_error_logs(conn, atm_id, limit=10):
    """
    특정 ATM의 장애로그를 최근 N건 조회한다. (ATM 상세 페이지 장애 이력 탭)

    [데이터셋 Issue 2 관련]
      장애 상태인 ATM은 미처리 장애로그가 최소 1건 존재해야 함.
      이 쿼리 결과에서 처리상태='미처리' 인 건이 있으면 대시보드 경고 카운터가 올라감.

    [SQL 예시]
      SELECT e.장애ID, e.장애유형, e.상세내용, e.처리상태,
             e.발생일시, e.처리완료일시, ad.이름 AS 담당자명
      FROM 장애로그 e
      LEFT JOIN 관리자 ad ON e.관리자ID = ad.관리자ID
      WHERE e.ATM_ID = %(atm_id)s
      ORDER BY e.발생일시 DESC
      LIMIT %(limit)s
    """
    pass


def resolve_error_logs(conn, atm_id):
    """
    ATM 복구(장애→정상) 시, 해당 ATM의 미처리 장애로그를 일괄 처리완료 처리한다.

    [데이터셋 Issue 2 핵심 해결 함수]
      service.change_status()가 "정상"으로 변경할 때만 이 함수를 호출.
      ATM 상태 컬럼과 장애로그 처리상태가 항상 동기화되도록 보장하는 로직.
      처리완료일시도 NOW()로 함께 기록하여 장애로그 시각 정합성(Issue 0) 유지.

    [SQL 예시]
      UPDATE 장애로그
      SET 처리상태 = '처리완료', 처리완료일시 = NOW()
      WHERE ATM_ID = %(atm_id)s
        AND 처리상태 = '미처리'
    """
    pass


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

    [SQL 예시]
      SELECT b.은행ID
      FROM ATM a
      JOIN 지점 b ON a.지점ID = b.지점ID
      WHERE a.ATM_ID = %(atm_id)s
    """
    pass
