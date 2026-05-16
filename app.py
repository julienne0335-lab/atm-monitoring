"""
app.py ─ Flask 애플리케이션 메인 진입점
         Flask 앱 객체를 만들고, 각 routes 파일을 연결하는 역할.
"""

from flask import Flask, redirect, url_for, session

# ── 각 기능 블루프린트(Blueprint) 불러오기 ─────────────
# Blueprint = 기능별로 라우트를 분리하는 Flask 모듈화 도구 
# 예: ATM 관련 라우트는 routes/atm.py 에만 모아둠 
from routes.dashboard import dashboard_bp
from routes.atm import atm_bp
from routes.transaction import transaction_bp
from routes.auth import auth_bp

# ── Flask 앱 생성 ───────────────────────────────────
app = Flask(__name__) # Flask 앱 생성 

# 세션(로그인 상태 유지)에 사용하는 암호화 키
# 실제 서비스에서는 절대 코드에 하드코딩하지 말고
# 환경변수(os.environ)로 관리하기!  
app.secret_key = "atm-system-secret-key-change-this"

# ── 블루프린트 등록 ──────────────────────────────────
# url_prefix: 해당 블루프린트의 모든 라우트 앞에 붙는 경로
app.register_blueprint(auth_bp)                         # /login, /logout 등록 
app.register_blueprint(dashboard_bp, url_prefix="/")    # /dashboard 등록 
app.register_blueprint(atm_bp, url_prefix="/atm")       # /atm/... 등록
app.register_blueprint(transaction_bp, url_prefix="/transaction")  # /transaction/... 등록 


# ── 루트 경로 처리 ──────────────────────────────────
@app.route("/")
def index():
    """
    사이트 루트(/) 접속 시:
    - 로그인 상태 → 대시보드로 이동
    - 미로그인 상태 → 로그인 페이지로 이동
    """
    if "admin_id" in session:  # 세션에 관리자 ID가 있으면 로그인된 상태
        return redirect(url_for("dashboard.index"))
    return redirect(url_for("auth.login"))


# ── 앱 실행 ─────────────────────────────────────────
if __name__ == "__main__":
    # debug=True: 코드 수정 시 자동 재시작, 오류 페이지 상세 표시
    # 실제 배포 시에는 debug=False 로 변경! 
    app.run(debug=True)
