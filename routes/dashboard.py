"""
routes/dashboard.py ─ 대시보드 요청·응답만 담당
"""

from flask import Blueprint, render_template, session
from services import atm_service, transaction_service, auth_service
from routes.auth import login_required

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def index():
    is_super  = (session.get("admin_role") == "슈퍼")
    branch_id = session.get("branch_id")

    try:
        return render_template("dashboard.html",
            atm_status   = atm_service.get_status_summary(is_super, branch_id),
            cash_alerts  = atm_service.get_cash_alerts(is_super, branch_id),
            today_stats  = transaction_service.get_today_stats(is_super, branch_id),
            error_count  = auth_service.get_unresolved_error_count(is_super, branch_id),
            is_super     = is_super,
        )
    except Exception as e:
        return render_template("dashboard.html",
            atm_status  = {"정상": 0, "점검중": 0, "장애": 0},
            cash_alerts = [], today_stats = {}, error_count = 0,
            is_super    = False, db_error = str(e),
        )