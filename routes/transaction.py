"""
routes/transaction.py ─ 거래내역 / 거래 통계 요청·응답 처리
──────────────────────────────────────────────────────────────────────
[역할 분리 원칙]
  ✅ 이 파일에서 해야 할 것 : request 파싱, session 읽기, flash, render_template, redirect
  ❌ 이 파일에서 하면 안 됨 : SQL 작성, 페이지네이션 계산, 업무 규칙 검증
                              (그 역할은 services/transaction_service.py가 담당)

[URL 구조]  (app.py에서 url_prefix="/transaction"으로 등록됨)
  GET /transaction/list    → 거래내역 목록 페이지 (필터 + 페이지네이션)
  GET /transaction/stats   → 거래 통계 페이지 (차트용 집계 데이터)

[데이터셋 Issue 5 참고]
  실패 거래 6건(거래ID: 108, 166, 339, 416, 439, 456)에 수수료 1,000원 오류 존재.
  DB 담당자가 직접 수정하거나, 템플릿에서 처리상태='실패'인 행의 수수료를 0으로 표시 권장.
"""

from flask import Blueprint, render_template, request, session, flash
from services import transaction_service
from routes.auth import login_required

transaction_bp = Blueprint("transaction", __name__)


@transaction_bp.route("/list")
@login_required  # 미로그인 시 /login으로 자동 redirect
def transaction_list():
    """
    거래내역 목록 페이지를 렌더링한다.

    [URL 예시]
      /transaction/list                              → 전체 목록 1페이지
      /transaction/list?tx_type=출금                → 출금 거래만
      /transaction/list?tx_status=실패&page=2       → 실패 거래 2페이지
      /transaction/list?date_from=2024-01-01&date_to=2024-12-31 → 2024년 전체

    [지원 필터]
      tx_type   : 거래유형 ("출금" / "입금" / "이체(출금)" / "이체(입금)")
      tx_status : 처리상태 ("성공" / "실패")
      date_from : 시작일 "YYYY-MM-DD"
      date_to   : 종료일 "YYYY-MM-DD"
      page      : 페이지 번호 (기본 1)

    [권한별 동작]
      슈퍼관리자 : 전 은행/지점 거래내역 조회
      일반관리자 : 자신의 소속 지점 ATM 거래내역만 조회

    [템플릿 전달 변수]
      result.transactions : 현재 페이지 거래 목록 (list of dict)
      result.total        : 전체 건수 (총 N건 표시에 사용)
      result.page         : 현재 페이지 번호
      result.total_pages  : 전체 페이지 수 (페이지 버튼 생성에 사용)
      filters             : 현재 필터 값 dict (필터 폼 선택 유지에 사용)
    """
    is_super  = (session.get("admin_role") == "슈퍼")
    branch_id = session.get("branch_id")

    # URL 쿼리파라미터에서 필터 값 추출 (없으면 빈 문자열 또는 1)
    tx_type   = request.args.get("tx_type",   "").strip() or None
    tx_status = request.args.get("tx_status", "").strip() or None
    date_from = request.args.get("date_from", "").strip() or None
    date_to   = request.args.get("date_to",   "").strip() or None

    # 페이지 번호는 int로 변환하고, 1 미만이면 1로 보정
    try:
        page = max(1, int(request.args.get("page", 1)))
    except ValueError:
        page = 1  # 숫자가 아닌 page 파라미터가 들어온 경우 1페이지로 처리

    try:
        result = transaction_service.get_transaction_list(
            is_super, branch_id,
            tx_type=tx_type, tx_status=tx_status,
            date_from=date_from, date_to=date_to,
            page=page,
        )

        # 필터 현재 값을 템플릿에 전달하여 폼의 선택 상태 유지
        filters = {
            "tx_type":   tx_type   or "",
            "tx_status": tx_status or "",
            "date_from": date_from or "",
            "date_to":   date_to   or "",
        }

        return render_template("transaction_list.html",
            **result,     # transactions, total, page, total_pages 언패킹
            filters=filters,
            is_super=is_super,
        )
    except Exception as e:
        flash(f"거래내역 조회 실패: {e}", "error")
        return render_template("transaction_list.html",
            transactions=[], total=0, page=1, total_pages=1,
            filters={}, is_super=is_super,
        )


@transaction_bp.route("/stats")
@login_required
def transaction_stats():
    """
    거래 통계 페이지를 렌더링한다.

    [표시 내용]
      - 지점별 자행/타행 거래 집계 (막대 차트용)
      - 거래유형별 건수/금액 집계 (파이 차트용)
      - 거래량 상위 ATM 순위 (TOP 5)

    [자행/타행 판별 기준]
      계좌 소속 은행 == ATM 소속 은행 → 자행 (수수료 0원)
      계좌 소속 은행 != ATM 소속 은행 → 타행 (수수료 1,000원)

    [데이터셋 이체 쌍 검증 힌트]
      type_stats에서 "이체(출금)" 건수와 "이체(입금)" 건수가 동일해야 정상.
      다르면 데이터 정합성 오류이므로 DB 담당자에게 알릴 것.
    """
    is_super  = (session.get("admin_role") == "슈퍼")
    branch_id = session.get("branch_id")

    try:
        stats = transaction_service.get_stats(is_super, branch_id)
        return render_template("transaction_stats.html",
            **stats,       # branch_stats, type_stats, top_atms 언패킹
            is_super=is_super,
        )
    except Exception as e:
        flash(f"통계 조회 실패: {e}", "error")
        return render_template("transaction_stats.html",
            branch_stats=[], type_stats=[], top_atms=[],
            is_super=is_super,
        )
