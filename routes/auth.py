"""
routes/auth.py ─ 로그인/로그아웃 요청·응답만 담당
비즈니스 로직은 auth_service로 위임
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from services import auth_service

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "admin_id" in session:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        login_id = request.form.get("login_id", "").strip()
        password = request.form.get("password", "").strip()

        try:
            # 검증 + DB 조회는 service에 위임
            admin_info = auth_service.login(login_id, password)

            # 세션에 저장
            session.update(admin_info)

            flash(f"{admin_info['admin_name']} 님, 환영합니다!", "success")
            return redirect(url_for("dashboard.index"))

        except ValueError as e:
            # service에서 발생한 에러 메시지를 그대로 flash
            flash(str(e), "error")

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("로그아웃되었습니다.", "info")
    return redirect(url_for("auth.login"))


def login_required(f):
    """로그인 확인 데코레이터 — 미로그인 시 /login 으로 이동"""
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        if "admin_id" not in session:
            flash("로그인이 필요합니다.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated 