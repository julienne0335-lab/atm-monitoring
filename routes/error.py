"""
routes/error.py ─ 지점장애 / 은행장애 HTTP 요청·응답 처리
──────────────────────────────────────────────────────────────────────
[역할 분리 원칙]
  ✅ 이 파일에서 해야 할 것 : request 파싱, session 읽기, flash, render_template, redirect
  ❌ 이 파일에서 하면 안 됨 : SQL 작성, 업무 규칙 검증
                              (그 역할은 services/error_service.py가 담당)

[URL 구조]  (app.py에서 url_prefix="/error"로 등록됨)
  GET  /error/branch              → 지점장애 목록 페이지
  POST /error/branch/report       → 지점장애 등록
  POST /error/branch/<id>/resolve → 지점장애 처리완료
  GET  /error/bank                → 은행장애 목록 페이지 (슈퍼만)
  POST /error/bank/report         → 은행장애 등록 (슈퍼만)
  POST /error/bank/<id>/resolve   → 은행장애 처리완료 (슈퍼만)
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from services import error_service
from routes.auth import login_required

error_bp = Blueprint("error", __name__)


# ── 지점장애 ───────────────────────────────────────────────────────

@error_bp.route("/branch")
@login_required
def branch_error_list():
    """
    지점장애 목록 페이지를 렌더링한다.

    [URL 예시]
      /error/branch              → 전체 목록
      /error/branch?filter=미처리 → 미처리만 필터링

    [권한별 동작]
      슈퍼관리자 : 모든 지점 장애 조회
      일반관리자 : 모든 지점 장애 조회 (등록은 자기 지점만)
    """
    is_super      = (session.get("admin_role") == "슈퍼")
    admin_branch_id = session.get("branch_id")
    status_filter = request.args.get("filter", "")  # "미처리" or ""(전체)

    try:
        errors   = error_service.get_branch_errors(unresolved_only=(status_filter == "미처리"))
        branches = error_service.get_branch_form_data()
        return render_template(
            "error_list.html",
            error_type    = "branch",
            errors        = errors,
            branches      = branches,
            banks         = [],
            status_filter = status_filter,
            is_super      = is_super,
            admin_branch_id = admin_branch_id,
            error_types   = error_service.BRANCH_ERROR_TYPES,
        )
    except Exception as e:
        flash(f"지점장애 목록 조회 실패: {e}", "error")
        return render_template(
            "error_list.html",
            error_type="branch", errors=[], branches=[], banks=[],
            status_filter="", is_super=is_super, admin_branch_id=admin_branch_id,
            error_types=error_service.BRANCH_ERROR_TYPES,
        )


@error_bp.route("/branch/report", methods=["POST"])
@login_required
def report_branch_error():
    """
    지점장애를 등록한다. (POST 전용)

    [처리 흐름]
      폼에서 branch_id, error_type, detail 추출
      → service.report_branch_error()에 위임 (권한 검증 + INSERT + commit)
      → 성공/실패 flash → 지점장애 목록으로 redirect
    """
    branch_id    = request.form.get("branch_id", "").strip()
    error_type   = request.form.get("error_type", "").strip()
    detail       = request.form.get("detail", "").strip()
    is_super     = (session.get("admin_role") == "슈퍼")
    admin_branch_id = session.get("branch_id")

    try:
        error_service.report_branch_error(branch_id, error_type, detail, is_super, admin_branch_id)
        flash("지점장애가 등록되었습니다.", "success")
    except ValueError as e:
        flash(str(e), "error")
    except Exception as e:
        flash(f"지점장애 등록 실패: {e}", "error")

    return redirect(url_for("error.branch_error_list"))


@error_bp.route("/branch/<int:branch_error_id>/resolve", methods=["POST"])
@login_required
def resolve_branch_error(branch_error_id):
    """
    지점장애를 처리완료 처리한다. (POST 전용)
    """
    admin_id        = session.get("admin_id")
    is_super        = (session.get("admin_role") == "슈퍼")
    admin_branch_id = session.get("branch_id")

    try:
        error_service.resolve_branch_error(branch_error_id, admin_id, is_super, admin_branch_id)
        flash("지점장애가 처리완료 처리되었습니다.", "success")
    except Exception as e:
        flash(f"처리완료 처리 실패: {e}", "error")

    return redirect(url_for("error.branch_error_list"))


# ── 은행장애 ───────────────────────────────────────────────────────

@error_bp.route("/bank")
@login_required
def bank_error_list():
    """
    은행장애 목록 페이지를 렌더링한다. (슈퍼관리자만 접근)

    [URL 예시]
      /error/bank              → 전체 목록
      /error/bank?filter=미처리 → 미처리만 필터링
    """
    is_super      = (session.get("admin_role") == "슈퍼")
    status_filter = request.args.get("filter", "")

    if not is_super:
        flash("은행장애 관리는 슈퍼관리자만 접근할 수 있습니다.", "error")
        return redirect(url_for("dashboard.index"))

    try:
        errors = error_service.get_bank_errors(unresolved_only=(status_filter == "미처리"))
        banks  = error_service.get_bank_form_data()
        return render_template(
            "error_list.html",
            error_type    = "bank",
            errors        = errors,
            branches      = [],
            banks         = banks,
            status_filter = status_filter,
            is_super      = is_super,
            admin_branch_id = None,
            error_types   = error_service.BANK_ERROR_TYPES,
        )
    except Exception as e:
        flash(f"은행장애 목록 조회 실패: {e}", "error")
        return render_template(
            "error_list.html",
            error_type="bank", errors=[], branches=[], banks=[],
            status_filter="", is_super=is_super, admin_branch_id=None,
            error_types=error_service.BANK_ERROR_TYPES,
        )


@error_bp.route("/bank/report", methods=["POST"])
@login_required
def report_bank_error():
    """
    은행장애를 등록한다. (POST 전용, 슈퍼관리자만)
    """
    bank_id    = request.form.get("bank_id", "").strip()
    error_type = request.form.get("error_type", "").strip()
    detail     = request.form.get("detail", "").strip()
    is_super   = (session.get("admin_role") == "슈퍼")

    admin_id = session.get("admin_id")

    try:
        error_service.report_bank_error(bank_id, error_type, detail, is_super, admin_id)
        flash("은행장애가 등록되었습니다.", "success")
    except ValueError as e:
        flash(str(e), "error")
    except Exception as e:
        flash(f"은행장애 등록 실패: {e}", "error")

    return redirect(url_for("error.bank_error_list"))


@error_bp.route("/bank/<int:bank_error_id>/resolve", methods=["POST"])
@login_required
def resolve_bank_error(bank_error_id):
    """
    은행장애를 처리완료 처리한다. (POST 전용, 슈퍼관리자만)
    """
    admin_id = session.get("admin_id")
    is_super = (session.get("admin_role") == "슈퍼")

    try:
        error_service.resolve_bank_error(bank_error_id, admin_id, is_super)
        flash("은행장애가 처리완료 처리되었습니다.", "success")
    except ValueError as e:
        flash(str(e), "error")
    except Exception as e:
        flash(f"처리완료 처리 실패: {e}", "error")

    return redirect(url_for("error.bank_error_list"))
