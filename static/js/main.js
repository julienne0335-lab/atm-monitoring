/*
  main.js ─ 공통 JavaScript
  Bootstrap 로드 이후 실행 (base.html 하단에 배치)
*/

document.addEventListener("DOMContentLoaded", function () {

    // ── 1. Flash 알림 메시지 3초 후 자동 닫기 ──────────
    const alerts = document.querySelectorAll(".alert.alert-dismissible");
    alerts.forEach(function (alert) {
        setTimeout(function () {
            // Bootstrap Alert 인스턴스를 가져와서 close() 호출
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }, 3000); // 3초
    });


    // ── 2. ATM 상태 '장애'로 변경 시 확인 다이얼로그 ──
    // .status-change-form 클래스가 붙은 폼에만 적용
    const statusForms = document.querySelectorAll(".status-change-form");
    statusForms.forEach(function (form) {
        form.addEventListener("submit", function (e) {
            const select = form.querySelector("select[name='new_status']");
            if (select && select.value === "장애") {
                if (!confirm("ATM 상태를 '장애'로 변경하시겠습니까?")) {
                    e.preventDefault(); // 취소하면 폼 전송 막기
                }
            }
        });
    });

});