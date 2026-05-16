"""
services/transaction_service.py ─ 거래내역 목록, 통계, 오늘 거래 집계 비즈니스 로직 
"""

from db import get_connection
from dao import transaction_dao

PER_PAGE = 50  # 페이지당 표시 건수


def get_transaction_list(is_super, branch_id,
                         tx_type=None, tx_status=None,
                         date_from=None, date_to=None, page=1):
    """
    거래내역 목록 + 페이지 정보 반환
    반환값 : dict { transactions, total, page, total_pages }
    """
    bid    = None if is_super else branch_id
    offset = (page - 1) * PER_PAGE

    conn = get_connection()
    try:
        total = transaction_dao.count_all(
            conn, branch_id=bid,
            tx_type=tx_type, tx_status=tx_status,
            date_from=date_from, date_to=date_to,
        )
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
            "total_pages":  max(1, (total + PER_PAGE - 1) // PER_PAGE),
        }
    finally:
        conn.close()


def get_stats(is_super, branch_id):
    """통계 페이지용 데이터 묶음 반환"""
    bid = None if is_super else branch_id

    conn = get_connection()
    try:
        return {
            "branch_stats": transaction_dao.find_branch_stats(conn, bid),
            "type_stats":   transaction_dao.find_type_stats(conn, bid),
            "top_atms":     transaction_dao.find_top_atms(conn, bid),
        }
    finally:
        conn.close()


def get_today_stats(is_super, branch_id):
    """대시보드용 오늘 거래 통계"""
    conn = get_connection()
    try:
        bid = None if is_super else branch_id
        return transaction_dao.find_today_stats(conn, branch_id=bid)
    finally:
        conn.close() 