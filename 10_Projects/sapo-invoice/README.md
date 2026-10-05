---
created: 2026-07-29 15:10
status: Active
---

# Sapo Invoice

Hệ thống hoá đơn điện tử của Sapo. Workspace code thật nằm ngoài vault này, tại `/Users/sapo/invoice/` — Developer OS không copy **code** vào đây. Riêng **tài liệu nghiệp vụ (SRS, epic, story)** thì từ 2026-08-11 developer-os **là nguồn chính** (xem lý do ở mục "SRS, Decision, Bug" bên dưới) — không còn nguyên tắc "chỉ link, không copy" cho phần này nữa.

## Repo con

| Repo (path trong `/Users/sapo/invoice/`) | Vai trò                                                                                                                                                 | Stack                            |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------- |
| `invoice-app/`                           | Merchant app nhúng trong Sapo                                                                                                                           | React (Vite) + Java (Gradle)     |
| `sapo-invoice-admin-frontend/`           | Admin UI                                                                                                                                                | React + TypeScript + Vite + pnpm |
| `sapo-invoice-admin-service/`            | Admin API                                                                                                                                               | Java + Gradle                    |
| `sapo-pay-service/`                      | Payment service                                                                                                                                         | Java (JHipster) + Maven          |
| `invoice-docs/`                          | ~~SRS, BMAD docs~~, tài liệu TVAN — **không còn là nguồn chính cho SRS/epic/story** (xem dưới); vẫn dùng cho tài liệu TVAN và các việc khác của team BA | Markdown                         |
| `ai-workspace/`                          | Toolbox AI cho toàn bộ dự án — prompts, rules, templates theo stack Java/React cụ thể của dự án này                                                     | Git repo riêng                   |

`servers/` trong cùng workspace là bản clone tham khảo của `@modelcontextprotocol/servers`, không thuộc sản phẩm Sapo Invoice.

### Phía Sapo Omni (core) — tiêu thụ Sapo Invoice như một provider

Hai repo dưới đây **không** thuộc nhóm `sapo-money/sapo-invoice`, mà là phía Omni gọi sang. Trong tài liệu của chúng, **`SI` = SapoInvoice**, tức chính sản phẩm ở bảng trên.

| Repo                     | Vai trò                                                                                                     | Stack                                              | Remote group                   |
| ------------------------ | ----------------------------------------------------------------------------------------------------------- | -------------------------------------------------- | ------------------------------ |
| `sapo-einvoice-service/` | Microservice hóa đơn điện tử của Omni; tích hợp 4 provider: MeInvoice, SInvoice, VnInvoice, **SapoInvoice** | Java 11 + Spring Boot 2.1 + Maven + **SQL Server** | `sapo-core/sapo-microservices` |
| `sapo-frontend-v3/`      | SPA admin của Omni (toàn bộ nghiệp vụ bán hàng); phần hóa đơn chỉ là page `EInvoice` + `InvoiceQR`          | React 16 + Webpack 5 + MUI 4 + Node 14             | `sapo-presentation`            |

## AI context của dự án này (`ai/`)

Developer OS thay thế `ai-workspace` (AI toolkit riêng trước đây của dự án) cho phần đang thực sự dùng:

- [[10_Projects/sapo-invoice/ai/project-instructions]] — context, workflow, conventions tổng thể (bắt đầu từ đây)
- [[10_Projects/sapo-invoice/ai/rules-backend]] — rules Java/Spring Boot
- [[10_Projects/sapo-invoice/ai/rules-frontend]] — rules React/TypeScript
- [[10_Projects/sapo-invoice/ai/daily-report]] — format daily/standup ngắn theo epic

Phần chưa migrate (thư viện prompt theo bước, template `SELFTEST_CHECKLIST.md`, BMAD skills — ít dùng hơn) vẫn ở `ai-workspace/` bên ngoài, chuyển dần khi thực sự cần thay vì chuyển hết một lần.

## SRS, Decision, Bug của dự án này

**Cập nhật 2026-08-11 (quyết định của user): `invoice-docs` không còn là nguồn chính cho SRS/epic/story.** Lý do trực tiếp: vướng quyền ghi GitLab issue trên project `invoice-docs` khi làm epic #61, và user chốt chuyển hẳn sang developer-os thay vì chỉ vá lỗi quyền. Từ nay:

- **SRS/epic/story (kể cả khi có bản gốc từ BA ở `invoice-docs`):** viết **đầy đủ nội dung** trực tiếp vào `10_Projects/sapo-invoice/` — không chỉ link/tóm tắt rồi trỏ sang `invoice-docs` nữa. `invoice-docs` (nếu còn được BA cập nhật) chỉ là tham chiếu lịch sử, không phải nguồn để dựa vào khi làm việc.
- **Quyết định kỹ thuật (ADR) và Bug cụ thể của dự án này:** ghi trực tiếp trong `10_Projects/sapo-invoice/` bằng template `Decision.md`/`Bug.md` — không ghi rải rác ở `ai-workspace` hay `invoice-docs` nữa.
- Bài học đủ tổng quát cho dự án khác → promote sang [[20_Knowledge/README|20_Knowledge]] hoặc [[30_AI/Rules/senior-engineering-practices]].

## Note của dự án

| Note                                                                                                                    | Nội dung                                                                                                                                                                                                                                                                                 |
| ----------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [[10_Projects/sapo-invoice/refactor-frontend-performance]]                                                              | Refactor `sapo-invoice-admin-frontend`: nguyên nhân gốc của duplicate call + waterfall, giải pháp từng hạng mục, đánh giá SSR                                                                                                                                                            |
| [[10_Projects/sapo-invoice/refactor-playbook-theo-man-hinh]]                                                            | Cách thực thi refactor đó theo slice dọc: lõi ngang không cắt được, 5 khuôn màn hình, checklist per-slice, thứ tự màn hình                                                                                                                                                               |
| [[10_Projects/sapo-invoice/migrate-ui-components-sang-design-system]]                                                   | ADR: `@sapo/ui-components` → `@sapo-finance/components`                                                                                                                                                                                                                                  |
| [[10_Projects/sapo-invoice/duong-ong-uispec-si]]                                                                        | Nghiên cứu chuyển `@sapo/ui-components` → DS cho SI: đo lại độ phủ 20-08 (81% dùng lại được, khung trang chặn 21/24 module), triage pattern SA ↔ SI, đề xuất `legacy-map` + skill `ds-migrate-screen`, khung template SRS                                                                |
| [[10_Projects/sapo-invoice/invoice-app-staging-master-release-flow]]                                                    | Quy trình release staging → master                                                                                                                                                                                                                                                       |
| [[10_Projects/sapo-invoice/merge-feature-branch-vao-staging-truoc-master]]                                              | Chiều merge feature branch                                                                                                                                                                                                                                                               |
| [[10_Projects/sapo-invoice/epic-65-auto-invoice-order-name/epic-65-auto-invoice-order-name\|Epic 65]]                   | Epic 65                                                                                                                                                                                                                                                                                  |
| [[10_Projects/sapo-invoice/qr-quiet-zone-80-tren-100]]                                                                  | Mã QR thanh toán: tăng quiet zone (QR thật 80×80 trong ảnh 100×100) — chưa sửa code                                                                                                                                                                                                      |
| [[10_Projects/sapo-invoice/bug-template-thu-vien-layout-va-huy-vien]]                                                   | Bug template editor: lệch layout khi chọn thư viện hình nền/viền (ternary Tabs×mobile từ !188) + Hủy viền không revert iframe (debounce + early-return `isStateRestored` trên create) — đã fix local                                                                                     |
| [[10_Projects/sapo-invoice/omni-einvoice-service-tong-quan]]                                                            | `sapo-einvoice-service`: kiến trúc, 4 provider, luồng chính, quy tắc code, nợ kỹ thuật; cảnh báo DB là SQL Server chứ không phải PostgreSQL như docs trong repo ghi                                                                                                                      |
| [[10_Projects/sapo-invoice/omni-frontend-v3-einvoice-tong-quan]]                                                        | `sapo-frontend-v3`: stack cũ (React 16/Webpack/Node 14), cách nối backend, page `EInvoice`, API surface, luồng QR công khai, CI theo tên branch                                                                                                                                          |
| [[10_Projects/sapo-invoice/omni-einvoice-dieu-tra-su-co-prod]]                                                          | Điều tra auto-invoice trên prod: mapping shard theo `tenantId`, quy tắc UTC, 9 gate chặn xuất hóa đơn, cạm bẫy `received_status`                                                                                                                                                         |
| [[10_Projects/sapo-invoice/omni-chay-local-service-va-frontend]]                                                        | Chạy local `sapo-frontend-v3` với BE staging (mô hình thực tế của team): host `phuongnt-dev2.mysapo.vn:4200`, FE chạy tốt trên Node 24 dù Volta ghim 14, cần hosts entry + HTTPS; phụ lục cách dựng service local nếu phải debug backend                                                 |
| [[10_Projects/sapo-invoice/epic-61-phi-van-chuyen-hoa-don-v2/epic-61-phi-van-chuyen-hoa-don-v2\|Epic 61 — SRS]]         | Epic phí vận chuyển hóa đơn V2: module `invoice-core-v2` (group sapo-money/sapo-invoice) thực ra code ở `sapo-einvoice-service`/`sapo-frontend-v3`; SRS v0.6, `delivery_fee` xác nhận là mảng (2026-08-12) — code hiện tại cần đổi `OrderResponse.deliveryFee` từ object đơn sang `List` |
| [[10_Projects/sapo-invoice/epic-61-phi-van-chuyen-hoa-don-v2/epic-61-cursor-prompt-implement\|Epic 61 — Cursor prompt]] | Prompt Cursor implement epic #61 — đã đọc code thật, có số dòng chính xác chỗ chèn logic (`setOrderData` dòng 2057-2061), chưa chạy                                                                                                                                                      |
| [[10_Projects/sapo-invoice/epic-61-phi-van-chuyen-hoa-don-v2/epic-61-test-cases\|Epic 61 — Test cases]]                 | Test case dựng trước khi Cursor implement — 5 nhóm (cấu hình, dựng dòng phí, đổi provider, điều chỉnh tự động, regression), có đánh dấu case còn gap cần hỏi BA/dev                                                                                                                      |
| [[10_Projects/sapo-invoice/epic-87-popup-xac-nhan-mtt/epic-87-plan\|Epic 87 — Plan]]                                 | Popup xác nhận trách nhiệm khi lập HĐ điều chỉnh cho HĐ MTT (SI admin-frontend): gate tại `AdjustInvoiceModal`, `charAt(4)==='M'`, không BE, không áp nhập file                                                                                                                          |
| [[10_Projects/sapo-invoice/epic-87-popup-xac-nhan-mtt/epic-87-test-cases\|Epic 87 — Test cases]]                     | Test case epic #87 — 4 nhóm (gate popup, copy/textlink, không hồi quy, biên series)                                                                                                                                                                                                      |
| [[10_Projects/sapo-invoice/epic-95-khoi-tong-vat-import-hddc/epic-95-plan\|Epic 95 — Plan]] | Import HĐ điều chỉnh bỏ tick: khối `AT–AW` theo file; cờ `invoices.is_vats_from_file` để XML `THTTLTSuat` dùng bảng đã lưu (cả mẫu 1 thuế suất); chốt BA note_784732 |
| [[10_Projects/sapo-invoice/epic-95-khoi-tong-vat-import-hddc/epic-95-cursor-prompt-implement\|Epic 95 — Cursor prompt]] | Prompt Cursor 2 phiên (BE #191 → FE #61), chưa chạy |
| [[10_Projects/sapo-invoice/epic-95-khoi-tong-vat-import-hddc/epic-95-test-results\|Epic 95 — Test results]] | Kết quả unit (67/67) + E2E trên dev: import, validate, A2-b, XML sau phát hành (CQT test cấp mã); danh sách case chưa chạy |
| [[10_Projects/sapo-invoice/epic-102-phi-giao-hang-theo-nguon-don-v2/epic-102-plan\|Epic 102 — Plan]] | Phí giao hàng V2 theo nguồn đơn: `order_source_ids` trong JSON `shipping_fee_setting`, gate tại `setOrderData`; chốt giống V3 ("Tất cả" = list đầy đủ, null = legacy) nhưng lưu id — lệch SRS BR3/BR4 |
| [[10_Projects/sapo-invoice/epic-102-phi-giao-hang-theo-nguon-don-v2/epic-102-cursor-prompt-implement\|Epic 102 — Cursor prompt]] | Prompt Cursor 2 phiên (BE `sapo-einvoice-service` → FE `sapo-frontend-v3`, đã gắn Figma `979:50171`), chưa chạy |
| [[10_Projects/sapo-invoice/epic-102-phi-giao-hang-theo-nguon-don-v2/epic-102-test-cases\|Epic 102 — Test cases]] | Test case epic #102 — cấu hình, dựng dòng phí, thời điểm áp dụng/HĐĐC, unit BE, regression |
| [[10_Projects/sapo-invoice/epic-102-phi-giao-hang-theo-nguon-don-v2/epic-102-cursor-prompt-fix-review\|Epic 102 — Cursor prompt fix review]] | Fix sau review lần 1: tên chip nguồn ngừng áp dụng (fetch theo `ids`), giữ `null` khi chưa tải được nguồn, bỏ FQN trong test |
| [[10_Projects/sapo-invoice/epic-102-phi-giao-hang-theo-nguon-don-v2/epic-102-test-results\|Epic 102 — Test results]] | Unit 51/51 (JDK 11) + staging: cấu hình C/F pass, dựng dòng phí D1/D3 pass (`EIN08987`/`EIN08988`); còn C8/F7, E, R, Auto Invoice riêng |
| [[10_Projects/sapo-invoice/epic-100-nhat-ky-hoat-dong/epic-100-plan\|Epic 100 — Plan]] | Nhật ký hoạt động: phụ thuộc BE (dev/master), lệch SRS v0.21 ↔ API !14, hợp đồng API, DS vs thư viện cũ, Figma, FE #24 (màn danh sách + mock, test Chrome), BE #20 (CDC `invoice_mistake_logs`/`invoice_statement_logs`), câu hỏi mở |

## Liên kết

- Entry point AI cho toàn bộ workspace ngoài vault: `/Users/sapo/invoice/AGENTS.md`
- Nguyên tắc AI tổng quát (nhiều dự án): [[30_AI/Rules/senior-engineering-practices]]
- Thư viện UI dùng chung (đang migrate tới): [[10_Projects/design-system/README]] — độ phủ DS ↔ nhu cầu invoice: [[10_Projects/design-system/audit-coverage-invoice]]

## Ghi chú

Dự án đang active, vận hành qua nhiều repo độc lập. Developer OS giờ là nơi lưu quyết định kỹ thuật, bài học, bug, và AI context đặc thù của dự án này — thay vì rải rác giữa `ai-workspace` và ghi chú tạm.
