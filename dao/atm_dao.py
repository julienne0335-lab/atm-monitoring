"""
dao/atm_dao.py ─ ATM, 현금보충, 장애로그, 유지보수이력 테이블 담당 쿼리 모음 
──────────────────────────────────────────
✅ SQL, cursor.execute, fetch
❌ if/else 비즈니스 로직, Flask request/session 

SQL 짤 때 이 파일만 수정하면 됨. 
모든 함수는 conn(DB 연결 객체)을 첫 번째 인자로 받음.
연결 열고 닫기는 service에서 담당.
""" 

 
def find_all(conn, branch_id=None, status=None):
    """ATM 전체 목록 조회. SQL 대기중"""
    pass


def find_by_id(conn, atm_id):
    """ATM 단건 조회. SQL 대기중"""
    pass


def find_cash_alerts(conn, branch_id=None):
    """현금 경고 ATM 목록. SQL 대기중"""
    pass


def count_by_status(conn, branch_id=None):
    """상태별 ATM 대수 집계. SQL 대기중"""
    pass


def update_status(conn, atm_id, new_status):
    """ATM 상태 변경. SQL 대기중"""
    pass


def update_cash_amount(conn, atm_id, amount):
    """현금잔량 증가. SQL 대기중"""
    pass


def insert_refill(conn, atm_id, admin_id, amount):
    """현금보충 이력 INSERT. SQL 대기중"""
    pass


def find_refill_logs(conn, atm_id, limit=5):
    """현금보충 이력 조회. SQL 대기중"""
    pass


def find_error_logs(conn, atm_id, limit=10):
    """장애로그 조회. SQL 대기중"""
    pass


def resolve_error_logs(conn, atm_id):
    """장애→정상 복구 시 처리완료 처리. SQL 대기중""" 
    pass