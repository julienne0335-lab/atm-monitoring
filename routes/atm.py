"""
routes/atm.py ─ ATM 요청·응답만 담당
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from services import atm_service
from routes.auth import login_required

atm_bp = Blueprint("atm", __name__)


@atm_bp.route("/list")
@login_required
def atm_list():
    is_super      = (session.get("admin_role") == "슈퍼")
    branch_id     = session.get("branch_id")
    status_filter = request.args.get("status", "")

    try:
        atms = atm_service.get_atm_list(is_super, branch_id, status=status_filter or None)
        return render_template("atm_list.html",
            atm_list      = atms,
            status_filter = status_filter,
            is_super      = is_super,
        )
    except Exception as e:
        flash(f"ATM 목록 조회 실패: {e}", "error")
        return render_template("atm_list.html", atm_list=[], status_filter="", is_super=False)


@atm_bp.route("/<int:atm_id>")
@login_required
def atm_detail(atm_id):
    try:
        data = atm_service.get_atm_detail(atm_id)

        if data is None:
            flash("존재하지 않는 ATM입니다.", "error")
            return redirect(url_for("atm.atm_list"))

        return render_template("atm_detail.html", **data)
        # **data 가 { atm, error_logs, transactions, refill_logs } 를 풀어서 전달

    except Exception as e:
        flash(f"ATM 상세 조회 실패: {e}", "error")
        return redirect(url_for("atm.atm_list"))


@atm_bp.route("/<int:atm_id>/status", methods=["POST"])
@login_required
def update_status(atm_id):
    new_status = request.form.get("new_status", "").strip()

    try:
        atm_service.change_status(atm_id, new_status)
        flash(f"ATM-{atm_id} 상태를 [{new_status}]로 변경했습니다.", "success")
    except ValueError as e:
        flash(str(e), "error")
    except Exception as e:
        flash(f"상태 변경 실패: {e}", "error")

    return redirect(url_for("atm.atm_detail", atm_id=atm_id))


@atm_bp.route("/<int:atm_id>/refill", methods=["POST"])
@login_required
def refill(atm_id):
    try:
        amount   = int(request.form.get("amount", 0))
        admin_id = session.get("admin_id")
        atm_service.process_refill(atm_id, admin_id, amount)
        flash(f"현금 {amount:,}원 보충 완료!", "success")
    except ValueError as e:
        flash(str(e), "error")
    except Exception as e:
        flash(f"현금 보충 실패: {e}", "error")

    return redirect(url_for("atm.atm_detail", atm_id=atm_id))