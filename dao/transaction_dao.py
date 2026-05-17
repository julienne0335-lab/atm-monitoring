"""
dao/transaction_dao.py ─ 거래내역(통계 쿼리 포함) 관련 SQL 쿼리 모음
──────────────────────────────────────────────────────────────────────
[역할 분리 원칙]
  ✅ 이 파일에서 해야 할 것 : SQL 작성, cursor.execute(), fetchall()/fetchone()
  ❌ 이 파일에서 하면 안 됨 : 페이지네이션 계산, Flask request 처리
                              (그 역할은 services/transaction_service.py가 담당)

[데이터셋 Issue 5 관련 주의]
  거래내역 조회 시 실패한 거래도 함께 조회됨.
  "실패" 거래의 수수료는 0이어야 하는데 데이터셋에 6건 오류가 있으므로,
  프론트엔드 표시 시 처리상태='실패' 인 행의 수수료는 0으로 override 권장.
"""


def find_all(conn, branch_id=None, tx_type=None,
             tx_status=None, date_from=None, date_to=None,
             limit=50, offset=0):
    """
    거래내역 목록을 조건 필터 + 페이지네이션으로 조회한다.

    [파라미터]
      branch_id  : 지점 필터 (None = 전체)
      tx_type    : 거래유형 필터 예) "출금" / "입금" / "이체(출금)" / "이체(입금)"
      tx_status  : 처리상태 필터 예) "성공" / "실패"
      date_from  : 조회 시작일 예) "2024-01-01"
      date_to    : 조회 종료일 예) "2025-12-31"
      limit      : 한 페이지당 건수 (기본 50)
      offset     : 건너뛸 건수 (page-1)*limit 으로 service에서 계산해서 전달

    [반환값]
      list of dict  (각 row에 거래ID, ATM_ID, 지점명, 계좌번호, 거래유형, 거래금액, 수수료, 처리상태, 거래일시 포함)

    [SQL 예시]
      SELECT t.거래ID, t.ATM_ID, b.지점명, ac.계좌번호,
             t.거래유형, t.거래금액, t.수수료, t.처리상태, t.거래일시
      FROM 거래내역 t
      JOIN ATM a   ON t.ATM_ID  = a.ATM_ID
      JOIN 지점 b  ON a.지점ID   = b.지점ID
      JOIN 계좌 ac ON t.계좌ID   = ac.계좌ID
      WHERE (%(branch_id)s IS NULL OR a.지점ID    = %(branch_id)s)
        AND (%(tx_type)s   IS NULL OR t.거래유형   = %(tx_type)s)
        AND (%(tx_status)s IS NULL OR t.처리상태   = %(tx_status)s)
        AND (%(date_from)s IS NULL OR DATE(t.거래일시) >= %(date_from)s)
        AND (%(date_to)s   IS NULL OR DATE(t.거래일시) <= %(date_to)s)
      ORDER BY t.거래일시 DESC
      LIMIT %(limit)s OFFSET %(offset)s
    """
    pass


def count_all(conn, branch_id=None, tx_type=None,
              tx_status=None, date_from=None, date_to=None):
    """
    거래내역 전체 건수를 조회한다. (페이지네이션의 total_pages 계산 전용)

    [주의]
      find_all()과 WHERE 조건이 정확히 일치해야 페이지 수가 맞음.
      조건을 수정할 때는 두 함수를 항상 함께 수정할 것.

    [반환값]
      int  예) 500

    [SQL 예시]
      SELECT COUNT(*) AS cnt
      FROM 거래내역 t
      JOIN ATM a ON t.ATM_ID = a.ATM_ID
      WHERE (%(branch_id)s IS NULL OR a.지점ID  = %(branch_id)s)
        AND (%(tx_type)s   IS NULL OR t.거래유형 = %(tx_type)s)
        AND (%(tx_status)s IS NULL OR t.처리상태 = %(tx_status)s)
        AND (%(date_from)s IS NULL OR DATE(t.거래일시) >= %(date_from)s)
        AND (%(date_to)s   IS NULL OR DATE(t.거래일시) <= %(date_to)s)
    """
    pass


def find_today_stats(conn, branch_id=None):
    """
    오늘 발생한 거래 통계를 조회한다. (대시보드 오늘 거래 현황 카드 전용)

    [반환값]
      dict  예) {
        "총건수":  42,
        "성공건수": 39,
        "실패건수": 3,
        "총거래금액": 85000000
      }

    [SQL 예시]
      SELECT
        COUNT(*) AS 총건수,
        SUM(CASE WHEN 처리상태 = '성공' THEN 1 ELSE 0 END) AS 성공건수,
        SUM(CASE WHEN 처리상태 = '실패' THEN 1 ELSE 0 END) AS 실패건수,
        COALESCE(SUM(CASE WHEN 처리상태 = '성공' THEN 거래금액 ELSE 0 END), 0) AS 총거래금액
      FROM 거래내역 t
      JOIN ATM a ON t.ATM_ID = a.ATM_ID
      WHERE DATE(t.거래일시) = CURDATE()
        AND (%(branch_id)s IS NULL OR a.지점ID = %(branch_id)s)
    """
    pass


def find_recent_by_atm(conn, atm_id, limit=10):
    """
    특정 ATM의 최근 거래내역을 N건 조회한다. (ATM 상세 페이지 거래 탭)

    [데이터셋 Issue 8 관련]
      현재 ATM 상태가 "장애"나 "점검중"이더라도 과거 거래 성공 기록이 조회될 수 있음.
      이는 ATM 상태가 현재 시점 기준이고, 거래내역은 2024~2025년 전체 기간 데이터이기 때문.
      프론트엔드에서 이 데이터를 표시할 때 "장애인데 왜 성공 거래가 있지?" 하고 오해하지 말 것.

    [반환값]
      list of dict  최근 10건의 거래 목록

    [SQL 예시]
      SELECT t.거래ID, t.거래유형, t.거래금액, t.수수료, t.처리상태, t.거래일시,
             ac.계좌번호
      FROM 거래내역 t
      JOIN 계좌 ac ON t.계좌ID = ac.계좌ID
      WHERE t.ATM_ID = %(atm_id)s
      ORDER BY t.거래일시 DESC
      LIMIT %(limit)s
    """
    pass


def find_branch_stats(conn, branch_id=None):
    """
    지점별 자행/타행 거래 집계를 조회한다. (통계 페이지 전용)

    [반환값]
      list of dict  예) [
        {"지점명": "강남", "자행건수": 80, "타행건수": 20, "자행금액": 40000000, ...},
        ...
      ]

    [자행/타행 판별 기준]
      계좌의 은행ID == ATM 소속 지점의 은행ID → 자행
      계좌의 은행ID != ATM 소속 지점의 은행ID → 타행

    [SQL 예시]
      SELECT b.지점명,
        SUM(CASE WHEN ac.은행ID = b.은행ID THEN 1 ELSE 0 END) AS 자행건수,
        SUM(CASE WHEN ac.은행ID != b.은행ID THEN 1 ELSE 0 END) AS 타행건수
      FROM 거래내역 t
      JOIN ATM a  ON t.ATM_ID = a.ATM_ID
      JOIN 지점 b ON a.지점ID = b.지점ID
      JOIN 계좌 ac ON t.계좌ID = ac.계좌ID
      WHERE (%(branch_id)s IS NULL OR a.지점ID = %(branch_id)s)
      GROUP BY b.지점ID, b.지점명
      ORDER BY b.지점명
    """
    pass


def find_type_stats(conn, branch_id=None):
    """
    거래유형별 건수와 금액을 집계한다. (통계 페이지 파이차트/막대차트 전용)

    [반환값]
      list of dict  예) [
        {"거래유형": "출금",      "건수": 200, "총금액": 500000000},
        {"거래유형": "입금",      "건수": 150, "총금액": 300000000},
        {"거래유형": "이체(출금)", "건수": 71,  "총금액": 142000000},
        {"거래유형": "이체(입금)", "건수": 71,  "총금액": 142000000},
      ]

    [데이터셋 이체 쌍(Pair) 참고]
      이체(출금) 건수와 이체(입금) 건수는 항상 동일해야 함.
      이 쿼리 결과에서 두 값이 다르면 데이터 정합성 오류.

    [SQL 예시]
      SELECT t.거래유형,
             COUNT(*) AS 건수,
             COALESCE(SUM(t.거래금액), 0) AS 총금액
      FROM 거래내역 t
      JOIN ATM a ON t.ATM_ID = a.ATM_ID
      WHERE (%(branch_id)s IS NULL OR a.지점ID = %(branch_id)s)
      GROUP BY t.거래유형
      ORDER BY 건수 DESC
    """
    pass


def find_top_atms(conn, branch_id=None, limit=5):
    """
    거래량(건수) 상위 ATM 목록을 조회한다. (통계 페이지 리더보드)

    [반환값]
      list of dict  예) [
        {"ATM_ID": 3, "지점명": "강남", "거래건수": 35, "총거래금액": 88000000},
        ...
      ]

    [SQL 예시]
      SELECT a.ATM_ID, b.지점명,
             COUNT(*) AS 거래건수,
             COALESCE(SUM(t.거래금액), 0) AS 총거래금액
      FROM 거래내역 t
      JOIN ATM a  ON t.ATM_ID = a.ATM_ID
      JOIN 지점 b ON a.지점ID = b.지점ID
      WHERE (%(branch_id)s IS NULL OR a.지점ID = %(branch_id)s)
      GROUP BY a.ATM_ID, b.지점명
      ORDER BY 거래건수 DESC
      LIMIT %(limit)s
    """
    pass
