-- ============================================
-- ATM 관리 시스템 DAO 쿼리 (최종본)
-- DBMS: MariaDB
-- 파라미터: ? 로 표시
-- ============================================
USE atm_system;


-- ============================================
-- [atm_dao]
-- ============================================

-- atm_dao.find_all(conn, branch_id=None, status=None, bank_id=None)
SELECT a.ATM_ID AS ATM_id, a.상태, a.현금잔량, a.경고임계값,
       a.ATM현금상태, a.최종갱신일시, b.지점명, b.은행ID, c.은행명
FROM ATM a
JOIN 지점 b ON a.지점ID = b.지점ID
JOIN 은행 c ON b.은행ID = c.은행ID
WHERE (? IS NULL OR a.지점ID = ?)
  AND (? IS NULL OR a.상태   = ?)
  AND (? IS NULL OR b.은행ID = ?)
ORDER BY a.ATM_ID;

-- atm_dao.find_by_id(conn, atm_id)
SELECT a.*, b.지점명, b.은행ID, c.은행명
FROM ATM a
JOIN 지점 b ON a.지점ID = b.지점ID
JOIN 은행 c ON b.은행ID = c.은행ID
WHERE a.ATM_ID = ?;

-- atm_dao.find_cash_alerts(conn, branch_id=None, bank_id=None)
SELECT a.ATM_ID AS ATM_id, a.상태, a.현금잔량, a.경고임계값, a.ATM현금상태,
       b.지점명, c.은행명
FROM ATM a
JOIN 지점 b ON a.지점ID = b.지점ID
JOIN 은행 c ON b.은행ID = c.은행ID
WHERE a.현금잔량 <= a.경고임계값
  AND (? IS NULL OR a.지점ID = ?)
  AND (? IS NULL OR b.은행ID = ?)
ORDER BY (a.현금잔량 / a.경고임계값);

-- atm_dao.count_by_status(conn, branch_id=None, bank_id=None)
SELECT 상태, COUNT(*) AS cnt
FROM ATM a
JOIN 지점 b ON a.지점ID = b.지점ID
WHERE (? IS NULL OR a.지점ID = ?)
  AND (? IS NULL OR b.은행ID = ?)
GROUP BY 상태;

-- atm_dao.update_status(conn, atm_id, new_status)
UPDATE ATM
SET 상태 = ?, 최종갱신일시 = NOW()
WHERE ATM_ID = ?;

-- atm_dao.update_cash_amount(conn, atm_id, amount)
-- 파라미터 순서: (amount, amount, atm_id)
UPDATE ATM
SET 현금잔량    = 현금잔량 + ?,
    ATM현금상태 = CASE
                     WHEN (현금잔량 + ?) > 경고임계값 THEN '정상'
                     ELSE '현금부족경고'
                 END,
    최종갱신일시 = NOW()
WHERE ATM_ID = ?;

-- atm_dao.insert_refill(conn, atm_id, admin_id, amount)
INSERT INTO 현금보충 (ATM_ID, 관리자ID, 보충금액, 보충일시)
VALUES (?, ?, ?, NOW());

-- atm_dao.find_refill_logs(conn, atm_id, limit=5)
SELECT r.보충ID, r.보충금액, r.보충일시, ad.이름 AS 담당자명
FROM 현금보충 r
JOIN 관리자 ad ON r.관리자ID = ad.관리자ID
WHERE r.ATM_ID = ?
ORDER BY r.보충일시 DESC
LIMIT ?;

-- atm_dao.find_maintenance_logs(conn, atm_id, limit=10)
SELECT m.이력ID, m.점검내용, m.점검일시,
       ad.이름 AS 담당자명,
       e.장애유형
FROM 유지보수이력 m
JOIN 관리자 ad ON m.관리자ID = ad.관리자ID
LEFT JOIN ATM장애로그 e ON m.장애ID = e.장애ID
WHERE m.ATM_ID = ?
ORDER BY m.점검일시 DESC
LIMIT ?;

-- atm_dao.find_bank_id_by_atm(conn, atm_id)
SELECT b.은행ID
FROM ATM a
JOIN 지점 b ON a.지점ID = b.지점ID
WHERE a.ATM_ID = ?;


-- ============================================
-- [auth_dao]
-- ============================================

-- auth_dao.find_by_login_id(conn, login_id)
SELECT ad.관리자ID, ad.이름, ad.로그인아이디, ad.비밀번호해시, ad.권한등급,
       ad.지점ID AS 지점_id, b.은행ID
FROM 관리자 ad
LEFT JOIN 지점 b ON ad.지점ID = b.지점ID
WHERE ad.로그인아이디 = ?;

-- auth_dao.find_bank_id_by_admin(conn, admin_id)
SELECT b.은행ID
FROM 관리자 ad
JOIN 지점 b ON ad.지점ID = b.지점ID
WHERE ad.관리자ID = ?;


-- ============================================
-- [transaction_dao]
-- ============================================

-- transaction_dao.find_all(conn, branch_id=None, tx_type=None, tx_status=None, date_from=None, date_to=None, bank_id=None, limit=50, offset=0)
SELECT t.거래ID, t.ATM_ID AS ATM_id, b.지점명, ac.계좌번호,
       t.거래유형, t.거래금액, t.수수료, t.처리상태, t.거래일시,
       CASE WHEN ac.은행ID = b.은행ID THEN '자행' ELSE '타행' END AS 자행타행
FROM 거래내역 t
JOIN ATM a   ON t.ATM_ID = a.ATM_ID
JOIN 지점 b  ON a.지점ID = b.지점ID
JOIN 계좌 ac ON t.계좌ID = ac.계좌ID
WHERE (? IS NULL OR a.지점ID        = ?)
  AND (? IS NULL OR t.거래유형       = ?)
  AND (? IS NULL OR t.처리상태       = ?)
  AND (? IS NULL OR DATE(t.거래일시) >= ?)
  AND (? IS NULL OR DATE(t.거래일시) <= ?)
  AND (? IS NULL OR b.은행ID         = ?)
ORDER BY t.거래일시 DESC
LIMIT ? OFFSET ?;

-- transaction_dao.count_all(conn, branch_id=None, tx_type=None, tx_status=None, date_from=None, date_to=None, bank_id=None)
SELECT COUNT(*) AS cnt
FROM 거래내역 t
JOIN ATM a  ON t.ATM_ID = a.ATM_ID
JOIN 지점 b ON a.지점ID = b.지점ID
WHERE (? IS NULL OR a.지점ID        = ?)
  AND (? IS NULL OR t.거래유형       = ?)
  AND (? IS NULL OR t.처리상태       = ?)
  AND (? IS NULL OR DATE(t.거래일시) >= ?)
  AND (? IS NULL OR DATE(t.거래일시) <= ?)
  AND (? IS NULL OR b.은행ID         = ?);

-- transaction_dao.find_today_stats(conn, branch_id=None, bank_id=None)
SELECT
    COUNT(*) AS 총건수,
    SUM(CASE WHEN t.처리상태 = '성공' THEN 1 ELSE 0 END) AS 성공건수,
    SUM(CASE WHEN t.처리상태 = '실패' THEN 1 ELSE 0 END) AS 실패건수,
    COALESCE(SUM(CASE WHEN t.처리상태 = '성공' THEN t.거래금액 ELSE 0 END), 0) AS 총거래금액,
    COALESCE(SUM(CASE WHEN t.처리상태 = '성공' THEN t.수수료 ELSE 0 END), 0) AS 총수수료
FROM 거래내역 t
JOIN ATM a  ON t.ATM_ID = a.ATM_ID
JOIN 지점 b ON a.지점ID = b.지점ID
WHERE DATE(t.거래일시) = CURDATE()
  AND (? IS NULL OR a.지점ID = ?)
  AND (? IS NULL OR b.은행ID = ?);

-- transaction_dao.find_recent_by_atm(conn, atm_id, limit=10)
SELECT t.거래ID, t.거래유형, t.거래금액, t.수수료, t.처리상태, t.거래일시,
       ac.계좌번호
FROM 거래내역 t
JOIN 계좌 ac ON t.계좌ID = ac.계좌ID
WHERE t.ATM_ID = ?
ORDER BY t.거래일시 DESC
LIMIT ?;

-- transaction_dao.find_branch_stats(conn, branch_id=None, bank_id=None, date_from=None, date_to=None)
SELECT b.지점명,
    SUM(CASE WHEN ac.은행ID = b.은행ID THEN 1 ELSE 0 END) AS 자행건수,
    SUM(CASE WHEN ac.은행ID != b.은행ID THEN 1 ELSE 0 END) AS 타행건수,
    SUM(CASE WHEN ac.은행ID = b.은행ID THEN t.거래금액 ELSE 0 END) AS 자행금액,
    SUM(CASE WHEN ac.은행ID != b.은행ID THEN t.거래금액 ELSE 0 END) AS 타행금액
FROM 거래내역 t
JOIN ATM a   ON t.ATM_ID = a.ATM_ID
JOIN 지점 b  ON a.지점ID = b.지점ID
JOIN 계좌 ac ON t.계좌ID = ac.계좌ID
WHERE (? IS NULL OR a.지점ID        = ?)
  AND (? IS NULL OR b.은행ID         = ?)
  AND (? IS NULL OR DATE(t.거래일시) >= ?)
  AND (? IS NULL OR DATE(t.거래일시) <= ?)
GROUP BY b.지점ID, b.지점명
ORDER BY b.지점명;

-- transaction_dao.find_type_stats(conn, branch_id=None, bank_id=None, date_from=None, date_to=None)
SELECT t.거래유형,
       COUNT(*) AS 건수,
       COALESCE(SUM(t.거래금액), 0) AS 총금액
FROM 거래내역 t
JOIN ATM a  ON t.ATM_ID = a.ATM_ID
JOIN 지점 b ON a.지점ID = b.지점ID
WHERE (? IS NULL OR a.지점ID        = ?)
  AND (? IS NULL OR b.은행ID         = ?)
  AND (? IS NULL OR DATE(t.거래일시) >= ?)
  AND (? IS NULL OR DATE(t.거래일시) <= ?)
GROUP BY t.거래유형
ORDER BY 건수 DESC;

-- transaction_dao.find_top_atms(conn, branch_id=None, bank_id=None, date_from=None, date_to=None, limit=5)
SELECT a.ATM_ID, b.지점명,
       COUNT(*) AS 거래건수,
       COALESCE(SUM(t.거래금액), 0) AS 총거래금액
FROM 거래내역 t
JOIN ATM a  ON t.ATM_ID = a.ATM_ID
JOIN 지점 b ON a.지점ID = b.지점ID
WHERE (? IS NULL OR a.지점ID        = ?)
  AND (? IS NULL OR b.은행ID         = ?)
  AND (? IS NULL OR DATE(t.거래일시) >= ?)
  AND (? IS NULL OR DATE(t.거래일시) <= ?)
GROUP BY a.ATM_ID, b.지점명
ORDER BY 거래건수 DESC
LIMIT ?;


-- ============================================
-- [error_dao] — ATM장애로그 관련
-- ============================================

-- error_dao.find_atm_error_logs(conn, atm_id, limit=10)
SELECT e.장애ID, e.장애유형, e.상세내용, e.처리상태,
       e.발생일시, e.처리완료일시, ad.이름 AS 담당자명
FROM ATM장애로그 e
LEFT JOIN 관리자 ad ON e.관리자ID = ad.관리자ID
WHERE e.ATM_ID = ?
ORDER BY e.발생일시 DESC
LIMIT ?;

-- error_dao.resolve_atm_error_logs(conn, atm_id)
UPDATE ATM장애로그
SET 처리상태 = '처리완료', 처리완료일시 = NOW()
WHERE ATM_ID = ?
  AND 처리상태 = '미처리';

-- error_dao.find_unresolved_atm_error_count(conn, branch_id=None, bank_id=None)
SELECT COUNT(*) AS cnt
FROM ATM장애로그 e
JOIN ATM a ON e.ATM_ID = a.ATM_ID
JOIN 지점 b ON a.지점ID = b.지점ID
WHERE e.처리상태 = '미처리'
  AND (? IS NULL OR a.지점ID = ?)
  AND (? IS NULL OR b.은행ID = ?);


-- ============================================
-- [error_dao] — 지점장애로그 관련
-- ============================================

-- error_dao.insert_branch_error(conn, branch_id, error_type, detail)
INSERT INTO 지점장애로그 (지점ID, 관리자ID, 장애유형, 상세내용, 처리상태, 발생일시)
VALUES (?, NULL, ?, ?, '미처리', NOW());

-- error_dao.resolve_branch_error(conn, branch_error_id, admin_id)
UPDATE 지점장애로그
SET 관리자ID = ?,
    처리상태 = '처리완료',
    처리완료일시 = NOW()
WHERE 지점장애ID = ?;

-- error_dao.find_unresolved_branch_errors(conn)
SELECT e.지점장애ID, e.지점ID, e.장애유형, e.상세내용,
       e.처리상태, e.발생일시, j.지점명
FROM 지점장애로그 e
JOIN 지점 j ON e.지점ID = j.지점ID
WHERE e.처리상태 = '미처리'
ORDER BY e.발생일시 DESC;

-- error_dao.find_all_branch_errors(conn)
SELECT e.지점장애ID, e.지점ID, e.관리자ID, e.장애유형,
       e.상세내용, e.처리상태, e.발생일시, e.처리완료일시,
       j.지점명, ad.이름 AS 담당자명
FROM 지점장애로그 e
JOIN 지점 j ON e.지점ID = j.지점ID
LEFT JOIN 관리자 ad ON e.관리자ID = ad.관리자ID
ORDER BY e.발생일시 DESC;

-- error_dao.find_atm_ids_by_branch(conn, branch_id)  [BR-11]
SELECT ATM_ID
FROM ATM
WHERE 지점ID = ?;

-- error_dao.find_branch_id_by_branch_error(conn, branch_error_id)  [BR-14]
SELECT 지점ID
FROM 지점장애로그
WHERE 지점장애ID = ?;


-- ============================================
-- [error_dao] — 은행장애로그 관련
-- ============================================

-- error_dao.insert_bank_error(conn, bank_id, error_type, detail)
INSERT INTO 은행장애로그 (은행ID, 관리자ID, 장애유형, 상세내용, 처리상태, 발생일시)
VALUES (?, NULL, ?, ?, '미처리', NOW());

-- error_dao.resolve_bank_error(conn, bank_error_id, admin_id)
UPDATE 은행장애로그
SET 관리자ID = ?,
    처리상태 = '처리완료',
    처리완료일시 = NOW()
WHERE 은행장애ID = ?;

-- error_dao.find_unresolved_bank_errors(conn)
SELECT e.은행장애ID, e.은행ID, e.장애유형, e.상세내용,
       e.처리상태, e.발생일시, b.은행명
FROM 은행장애로그 e
JOIN 은행 b ON e.은행ID = b.은행ID
WHERE e.처리상태 = '미처리'
ORDER BY e.발생일시 DESC;

-- error_dao.find_all_bank_errors(conn)
SELECT e.은행장애ID, e.은행ID, e.관리자ID, e.장애유형,
       e.상세내용, e.처리상태, e.발생일시, e.처리완료일시,
       b.은행명, ad.이름 AS 담당자명
FROM 은행장애로그 e
JOIN 은행 b ON e.은행ID = b.은행ID
LEFT JOIN 관리자 ad ON e.관리자ID = ad.관리자ID
ORDER BY e.발생일시 DESC;

-- error_dao.find_atm_ids_by_bank(conn, bank_id)  [BR-12]
SELECT a.ATM_ID
FROM ATM a
JOIN 지점 b ON a.지점ID = b.지점ID
WHERE b.은행ID = ?;

-- error_dao.bulk_insert_atm_errors(conn, atm_id, error_type, detail)  [BR-11, BR-12]
INSERT INTO ATM장애로그 (ATM_ID, 장애유형, 상세내용, 처리상태, 발생일시)
VALUES (?, ?, ?, '미처리', NOW());

-- error_dao.find_bank_id_by_bank_error(conn, bank_error_id)  [BR-13]
SELECT 은행ID
FROM 은행장애로그
WHERE 은행장애ID = ?;
