"""
dao/transaction_dao.py ─ 거래내역(통계 쿼리 포함) 관련 SQL 쿼리 모음
"""


def find_all(conn, branch_id=None, tx_type=None,
             tx_status=None, date_from=None, date_to=None,
             limit=50, offset=0):
    """거래내역 목록 조회. SQL 대기중""" 
    pass


def count_all(conn, branch_id=None, tx_type=None,
              tx_status=None, date_from=None, date_to=None):
    """거래내역 전체 건수. SQL 대기중"""
    pass 


def find_today_stats(conn, branch_id=None):
    """오늘 거래 통계 (대시보드용). SQL 대기중"""
    pass 
   

def find_recent_by_atm(conn, atm_id, limit=10):
    """ATM 상세 페이지용 최근 거래내역. SQL 대기중""" 
    pass 
   

def find_branch_stats(conn, branch_id=None):
    """지점별 자행/타행 거래 집계 (통계 페이지). SQL 대기중"""
    pass 
     

def find_top_atms(conn, branch_id=None, limit=5):
    """거래량 상위 ATM. SQL 대기중"""
    pass 