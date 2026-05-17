"""
services/transaction_service.py ─ 거래내역 목록, 통계, 오늘 거래 집계 비즈니스 로직
──────────────────────────────────────────────────────────────────────
[역할 분리 원칙]
  ✅ 이 파일에서 해야 할 것 : 페이지네이션 계산, 권한 분기, dao 호출
  ❌ 이 파일에서 하면 안 됨 : SQL 직접 작성, Flask request/session/flash 접근

[이 서비스가 다루는 데이터]
  거래내역 테이블 (500건, 2024~2025년)
  유형: 출금, 입금, 이체(출금), 이체(입금)
  상태: 성공, 실패

[데이터셋 Issue 5 참고]
  실패 거래 6건에 수수료 1,000원이 잘못 부과된 데이터가 있음.
  이 서비스는 조회만 담당하므로 직접 수정하지 않음.
  프론트엔드 표시 시 처리상태='실패'인 행의 수수료를 0으로 override하거나,
  DB 담당자가 해당 6건 데이터를 직접 수정해야 함.
"""

from db import get_connection
from dao import transaction_dao

# 한 페이지당 표시할 거래 건수 (50건으로 고정)
PER_PAGE = 50


def get_transaction_list(is_super, branch_id,
                         tx_type=None, tx_status=None,
                         date_from=None, date_to=None, page=1):
    """
    거래내역 목록과 페이지 정보를 함께 반환한다.

    [페이지네이션 계산 방식]
      offset = (page - 1) * PER_PAGE
      예) page=2, PER_PAGE=50 → offset=50 → 51~100번째 행 조회

    [반환값]
      dict {
        "transactions" : list of dict  (현재 페이지 거래 목록)
        "total"        : int           (필터 조건 전체 건수)
        "page"         : int           (현재 페이지 번호)
        "total_pages"  : int           (전체 페이지 수, 최소 1)
      }

    [파라미터]
      is_super   : True면 전체 지점, False면 branch_id 지점만
      tx_type    : "출금" / "입금" / "이체(출금)" / "이체(입금)" / None(전체)
      tx_status  : "성공" / "실패" / None(전체)
      date_from  : 시작일 문자열 "YYYY-MM-DD" / None
      date_to    : 종료일 문자열 "YYYY-MM-DD" / None
      page       : 요청 페이지 번호 (1부터 시작)
    """
    bid    = None if is_super else branch_id
    offset = (page - 1) * PER_PAGE  # 건너뛸 행 수 계산

    conn = get_connection()
    try:
        # 페이지네이션을 위해 전체 건수를 먼저 조회 (total_pages 계산용)
        total = transaction_dao.count_all(
            conn, branch_id=bid,
            tx_type=tx_type, tx_status=tx_status,
            date_from=date_from, date_to=date_to,
        )

        # 현재 페이지에 해당하는 데이터 조회
        rows = transaction_dao.find_all(
            conn, branch_id=bid,
            tx_type=tx_type, tx_status=tx_status,
            date_from=date_from, date_to=date_to,
            limit=PER_PAGE, offset=offset,
        )

        return {
            "transactions": rows,
            "total":        total,
            "page":         page,
            # 올림 나눗셈으로 total_pages 계산, 결과가 0이면 최소 1페이지
            "total_pages":  max(1, (total + PER_PAGE - 1) // PER_PAGE),
        }
    finally:
        conn.close()


def get_stats(is_super, branch_id):
    """
    통계 페이지에 필요한 데이터를 모두 묶어서 반환한다.

    [반환값]
      dict {
        "branch_stats" : 지점별 자행/타행 집계 list
        "type_stats"   : 거래유형별 건수/금액 집계 list
        "top_atms"     : 거래량 상위 ATM list (기본 5건)
      }
    """
    bid = None if is_super else branch_id

    conn = get_connection()
    try:
        return {
            "branch_stats": transaction_dao.find_branch_stats(conn, bid),
            "type_stats":   transaction_dao.find_type_stats(conn, bid),   # 유형별 집계
            "top_atms":     transaction_dao.find_top_atms(conn, bid),
        }
    finally:
        conn.close()


def get_today_stats(is_super, branch_id):
    """
    대시보드용 오늘 거래 통계를 반환한다.

    [반환값]
      dict {
        "총건수"   : int,
        "성공건수" : int,
        "실패건수" : int,
        "총거래금액": int
      }
    """
    conn = get_connection()
    try:
        bid = None if is_super else branch_id
        return transaction_dao.find_today_stats(conn, branch_id=bid)
    finally:
        conn.close()
