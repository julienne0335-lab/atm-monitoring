"""
routes/dashboard.py ─ 대시보드 요청·응답 처리
──────────────────────────────────────────────────────────────────────
[역할 분리 원칙]
  ✅ 이 파일에서 해야 할 것 : session 읽기, 여러 service 호출, render_template
  ❌ 이 파일에서 하면 안 됨 : SQL 작성, 업무 규칙 검증

[URL 구조]  (app.py에서 url_prefix="/"로 등록됨)
  GET /dashboard → 대시보드 메인 페이지

[대시보드 표시 항목]
  - ATM 상태별 요약 (정상/점검중/장애 대수)
  - 현금 경고 ATM 목록 (현금잔량 <= 경고임계값)
  - 오늘 거래 통계 (총건수/성공/실패/총금액)
  - 미처리 장애 건수 (경고 배지)
"""

from flask import Blueprint, render_template, session
from services import atm_service, transaction_service, auth_service
from routes.auth import login_required

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required  # 미로그인 시 /login으로 자동 redirect
def index():
    """
    대시보드 메인 페이지를 렌더링한다.

    [권한별 동작]
      슈퍼관리자 (admin_role == "슈퍼") : 전 은행/지점 합산 데이터 표시
      일반관리자                         : 자신의 소속 지점 데이터만 표시

    [템플릿 전달 변수]
      atm_status  : dict {"정상": N, "점검중": N, "장애": N}
      cash_alerts : list  현금 경고 ATM 목록
      today_stats : dict  오늘 거래 통계
      error_count : int   미처리 장애 건수 (0보다 크면 경고 배지 표시)
      is_super    : bool  슈퍼관리자 여부 (템플릿에서 UI 분기에 사용)

    [에러 처리]
      DB 연결 실패 등 예외 발생 시 빈 값으로 폼백하여 페이지 자체는 정상 렌더링.
      db_error 변수를 템플릿에 전달하여 오류 메시지를 사용자에게 표시할 수 있음.
    """
    is_super  = (session.get("admin_role") == "슈퍼")
    branch_id = session.get("branch_id")
    bank_id   = session.get("bank_id")

    try:
        return render_template("dashboard.html",
            # ATM 상태별 대수 집계 (대시보드 상단 요약 카드)
            atm_status  = atm_service.get_status_summary(is_super, branch_id, bank_id=bank_id),

            # 현금잔량 <= 경고임계값인 ATM 목록 (경고 섹션)
            cash_alerts = atm_service.get_cash_alerts(is_super, branch_id, bank_id=bank_id),

            # 장애 ATM 목록 (대시보드 장애 섹션)
            faulty_atms  = atm_service.get_atm_list(is_super, branch_id, status="장애",   bank_id=bank_id),
            # 점검중 ATM 목록 (대시보드 점검중 섹션)
            pending_atms = atm_service.get_atm_list(is_super, branch_id, status="점검중", bank_id=bank_id),

            # 오늘 날짜 기준 거래 통계 (오늘 현황 카드)
            today_stats = transaction_service.get_today_stats(is_super, branch_id, bank_id=bank_id),

            # 미처리 장애 건수 (상단 네비게이션 경고 배지)
            error_count = auth_service.get_unresolved_error_count(is_super, branch_id, bank_id=bank_id),

            is_super    = is_super,
        )
    except Exception as e:
        # DB 오류 등 발생 시 빈 값으로 폼백 (대시보드 페이지는 항상 보여야 함)
        return render_template("dashboard.html",
            atm_status   = {"정상": 0, "점검중": 0, "장애": 0},
            cash_alerts  = [],
            faulty_atms  = [],
            pending_atms = [],
            today_stats  = {},
            error_count  = 0,
            is_super     = False,
            db_error     = str(e),
        )
