"""
routes/auth.py ─ 로그인 / 로그아웃 요청·응답 처리
──────────────────────────────────────────────────────────────────────
[역할 분리 원칙]
  ✅ 이 파일에서 해야 할 것 : request 파싱, session 저장, flash, redirect
  ❌ 이 파일에서 하면 안 됨 : SQL 직접 작성, 비밀번호 해시 비교
                              (그 역할은 services/auth_service.py가 담당)

[이 파일에서 제공하는 데코레이터]
  @login_required : 로그인이 필요한 모든 라우트에 붙임.
                    다른 routes 파일(atm.py, dashboard.py 등)에서 import해서 사용.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from services import auth_service

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    로그인 페이지를 표시하고, 로그인 폼을 처리한다.

    [GET 요청]
      이미 로그인된 상태면 대시보드로 이동.
      아니면 로그인 폼(login.html)을 렌더링.

    [POST 요청]
      1. 폼에서 login_id, password를 받아서 strip()으로 앞뒤 공백 제거
      2. auth_service.login()에 위임 → 검증 + DB 조회
      3. 성공 시 세션에 저장 후 대시보드로 redirect
      4. 실패(ValueError) 시 에러 메시지를 flash로 표시 후 폼 재렌더링
    """
    # 이미 로그인된 상태라면 로그인 페이지를 다시 보여줄 필요 없음
    if "admin_id" in session:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        # 폼 데이터 추출 (strip으로 불필요한 공백 제거)
        login_id = request.form.get("login_id", "").strip()
        password = request.form.get("password", "").strip()

        try:
            # 검증 + DB 조회는 service에 완전히 위임
            admin_info = auth_service.login(login_id, password)

            # 로그인 성공: 세션에 관리자 정보 저장
            # admin_info = {"admin_id": ..., "admin_name": ..., "admin_role": ..., "branch_id": ...}
            session.update(admin_info)

            flash(f"{admin_info['admin_name']} 님, 환영합니다!", "success")
            return redirect(url_for("dashboard.index"))

        except ValueError as e:
            # service에서 발생한 에러 메시지(아이디/비번 불일치 등)를 flash로 표시
            flash(str(e), "error")

    # GET 요청이거나 POST 실패 시 로그인 폼 재렌더링
    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    """
    로그아웃 처리. 세션 전체를 비우고 로그인 페이지로 이동.

    [주의]
      session.pop("admin_id") 대신 session.clear()를 사용하여
      세션에 저장된 모든 정보(admin_id, admin_name, branch_id 등)를 한 번에 삭제.
    """
    session.clear()
    flash("로그아웃되었습니다.", "info")
    return redirect(url_for("auth.login"))


def login_required(f):
    """
    로그인 인증 데코레이터.

    [사용 방법]
      로그인이 필요한 라우트 함수 바로 위에 @login_required를 붙임.
      예)
        @atm_bp.route("/list")
        @login_required
        def atm_list():
            ...

    [동작]
      세션에 "admin_id"가 없으면(= 미로그인) /login으로 redirect.
      있으면 원래 요청한 뷰 함수를 정상 실행.

    [functools.wraps 필요성]
      데코레이터로 감싸면 함수 이름이 "decorated"로 바뀌는 문제가 생김.
      @wraps(f)를 붙이면 원래 함수 이름과 docstring이 유지됨.
      Flask 내부에서 함수 이름으로 엔드포인트를 식별하므로 반드시 필요.
    """
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        if "admin_id" not in session:
            flash("로그인이 필요합니다.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)  # 로그인 상태면 원래 함수 실행

    return decorated
