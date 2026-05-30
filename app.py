"""
app.py ─ Flask 애플리케이션 메인 진입점
──────────────────────────────────────────────────────────────────────
[이 파일의 역할]
  Flask 앱 객체를 생성하고, 각 기능 모듈(Blueprint)을 앱에 연결하는 역할.
  실행 명령: python app.py  또는  flask run

[프로젝트 구조 요약]
  routes/   ─ HTTP 요청·응답 처리 (URL → 함수 연결)
  services/ ─ 업무 규칙 검증, 트랜잭션 처리
  dao/      ─ SQL 쿼리 모음
  db.py     ─ DB 연결 객체 반환 함수 (db.example.py를 복사해서 만들기) 
"""
import os
from flask import Flask, redirect, url_for, session

# Blueprint: 기능별로 라우트를 분리하는 Flask 모듈화 도구
# 예) ATM 관련 라우트는 routes/atm.py에만 모아두고, 여기서 한 번에 등록
from routes.dashboard import dashboard_bp
from routes.atm import atm_bp
from routes.transaction import transaction_bp
from routes.auth import auth_bp
from routes.error import error_bp

# Flask 앱 객체 생성
app = Flask(__name__)

# 세션(로그인 상태 유지)에 사용하는 암호화 키
# Flask는 세션 데이터를 이 키로 서명하여 쿠키에 저장함
# ⚠️ 실제 서비스에서는 코드에 하드코딩하지 말고 환경변수(os.environ)로 관리할 것
app.secret_key = os.environ.get("SECRET_KEY", "atm-system-secret-key-change-this")

# ── Blueprint 등록 ──────────────────────────────────────────────────
# url_prefix: 해당 Blueprint의 모든 라우트 앞에 자동으로 붙는 경로
app.register_blueprint(auth_bp)                            # /login, /logout
app.register_blueprint(dashboard_bp, url_prefix="/")       # /dashboard
app.register_blueprint(atm_bp,       url_prefix="/atm")    # /atm/list, /atm/<id>, ...
app.register_blueprint(transaction_bp, url_prefix="/transaction")  # /transaction/list, /transaction/stats
app.register_blueprint(error_bp,       url_prefix="/error")         # /error/branch, /error/bank


@app.after_request
def no_cache_for_authenticated(response):
    # 로그인 상태 페이지는 브라우저 캐시에 저장하지 않도록 함
    # 없으면 로그아웃 후 뒤로가기 시 캐시된 페이지가 그대로 표시됨
    if "admin_id" in session:
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


@app.route("/")
def index():
    """
    사이트 루트(/) 접속 처리.
      - 로그인 상태  → 대시보드(/dashboard)로 이동
      - 미로그인 상태 → 로그인 페이지(/login)로 이동
    """
    if "admin_id" in session:  # 세션에 관리자 ID가 있으면 로그인된 상태
        return redirect(url_for("dashboard.index"))
    return redirect(url_for("auth.login"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False) 
