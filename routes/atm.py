"""
routes/atm.py ─ ATM 관련 HTTP 요청·응답 처리
──────────────────────────────────────────────────────────────────────
[역할 분리 원칙]
  ✅ 이 파일에서 해야 할 것 : request 파싱, session 읽기, flash, render_template, redirect
  ❌ 이 파일에서 하면 안 됨 : SQL 작성, 업무 규칙 검증
                              (그 역할은 services/atm_service.py가 담당)

[URL 구조]  (app.py에서 url_prefix="/atm"으로 등록됨)
  GET  /atm/list                  → ATM 목록 페이지
  GET  /atm/<atm_id>              → ATM 상세 페이지
  POST /atm/<atm_id>/status       → ATM 상태 변경
  POST /atm/<atm_id>/refill       → 현금 보충
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from services import atm_service
from routes.auth import login_required

atm_bp = Blueprint("atm", __name__)


@atm_bp.route("/list")
@login_required  # 미로그인 시 /login으로 자동 redirect
def atm_list():
    """
    ATM 목록 페이지를 렌더링한다.

    [URL 예시]
      /atm/list          → 전체 목록
      /atm/list?status=장애 → 장애 ATM만 필터링

    [권한별 동작]
      슈퍼관리자 : 전 은행/지점 ATM 전체 조회
      일반관리자 : 자신의 소속 지점 ATM만 조회
    """
    is_super      = (session.get("admin_role") == "슈퍼")
    branch_id     = session.get("branch_id")
    bank_id       = session.get("bank_id")
    status_filter = request.args.get("status", "")  # URL 쿼리파라미터에서 상태 필터 추출

    try:
        # 빈 문자열은 None으로 변환하여 service에 전달 (None = 전체 조회)
        atms = atm_service.get_atm_list(is_super, branch_id, status=status_filter or None, bank_id=bank_id)
        return render_template("atm_list.html",
            atm_list      = atms,
            status_filter = status_filter,  # 현재 선택된 필터를 템플릿에 전달 (드롭다운 선택 유지)
            is_super      = is_super,
        )
    except Exception as e:
        # DB 오류 등 예상치 못한 에러 발생 시 빈 목록으로 폼백
        flash(f"ATM 목록 조회 실패: {e}", "error")
        return render_template("atm_list.html", atm_list=[], status_filter="", is_super=False)


@atm_bp.route("/<int:atm_id>")
@login_required
def atm_detail(atm_id):
    """
    ATM 상세 페이지를 렌더링한다.

    [표시 내용]
      - ATM 기본 정보 (상태, 현금잔량, 경고임계값, 소속 지점/은행)
      - 장애로그 목록 (최근 10건)
      - 거래내역 목록 (최근 10건)
      - 현금보충 이력 (최근 5건)

    [데이터셋 Issue 8 참고]
      현재 ATM 상태가 "장애"여도 거래내역에 과거 성공 기록이 있을 수 있음.
      이는 ATM 상태가 현재 시점 데이터이고, 거래내역은 2024~2025 전체 기간이기 때문.

    [파라미터]
      atm_id : URL에서 자동 추출되는 ATM PK (int 타입으로 변환됨)
    """
    try:
        # service에서 ATM 정보 + 관련 로그들을 모두 묶어서 가져옴
        data = atm_service.get_atm_detail(atm_id)

        if data is None:
            # 존재하지 않는 ATM_ID로 접근한 경우
            flash("존재하지 않는 ATM입니다.", "error")
            return redirect(url_for("atm.atm_list"))

        # **data 언패킹으로 { atm, error_logs, transactions, refill_logs }를 템플릿에 전달
        return render_template("atm_detail.html", **data)

    except Exception as e:
        flash(f"ATM 상세 조회 실패: {e}", "error")
        return redirect(url_for("atm.atm_list"))


@atm_bp.route("/<int:atm_id>/status", methods=["POST"])
@login_required
def update_status(atm_id):
    """
    ATM 상태를 변경한다. (POST 전용)

    [처리 흐름]
      폼에서 new_status 값 추출
      → service.change_status()에 위임 (유효성 검증 + DB 업데이트 + 트랜잭션)
      → 성공/실패 flash 메시지 표시
      → ATM 상세 페이지로 redirect

    [데이터셋 Issue 2]
      service에서 "정상"으로 변경 시 미처리 장애로그를 자동으로 처리완료 처리함.
      이 라우트는 단순히 service를 호출만 하면 됨.

    [HTTP 메서드]
      상태 변경은 서버 데이터를 수정하므로 GET이 아닌 POST 사용.
      HTML form의 method="POST"로 전송.
    """
    new_status = request.form.get("new_status", "").strip()

    try:
        atm_service.change_status(atm_id, new_status)
        flash(f"ATM-{atm_id} 상태를 [{new_status}]로 변경했습니다.", "success")
    except ValueError as e:
        # "올바르지 않은 상태값" 등 업무 규칙 위반 에러
        flash(str(e), "error")
    except Exception as e:
        # DB 오류 등 예상치 못한 에러
        flash(f"상태 변경 실패: {e}", "error")

    # 성공/실패 모두 ATM 상세 페이지로 돌아감
    return redirect(url_for("atm.atm_detail", atm_id=atm_id))


@atm_bp.route("/<int:atm_id>/refill", methods=["POST"])
@login_required
def refill(atm_id):
    """
    ATM 현금을 보충한다. (POST 전용)

    [처리 흐름]
      폼에서 amount 값 추출 → int 변환
      → service.process_refill()에 위임 (은행 권한 체크 + 이력 INSERT + 잔량 UPDATE)
      → 성공/실패 flash 메시지 표시
      → ATM 상세 페이지로 redirect

    [데이터셋 Issue 3]
      service.process_refill()에서 관리자 소속 은행과 ATM 소속 은행을 비교함.
      타 은행 ATM에 보충 시도 시 ValueError가 발생하여 이 라우트에서 catch됨.

    [int() 변환 주의]
      request.form에서 꺼낸 값은 문자열이므로 int()로 변환 필요.
      숫자가 아닌 문자열이 들어오면 ValueError가 발생하여 except에서 처리됨.
    """
    try:
        amount   = int(request.form.get("amount", 0))  # 폼 값은 str → int 변환
        admin_id = session.get("admin_id")
        is_super = (session.get("admin_role") == "슈퍼")

        # service에서 은행 권한 체크 + 이력 INSERT + 잔량 UPDATE를 트랜잭션으로 처리
        atm_service.process_refill(atm_id, admin_id, amount, is_super=is_super)
        flash(f"현금 {amount:,}원 보충 완료!", "success")
    except ValueError as e:
        # 금액 유효성 오류 또는 타 은행 접근 차단 메시지
        flash(str(e), "error")
    except Exception as e:
        flash(f"현금 보충 실패: {e}", "error")

    return redirect(url_for("atm.atm_detail", atm_id=atm_id))
