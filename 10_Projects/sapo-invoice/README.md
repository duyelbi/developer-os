---
created: 2026-07-29 15:10
status: Active
---

# Sapo Invoice

Hệ thống hoá đơn điện tử của Sapo. Workspace thật nằm ngoài vault này, tại `/Users/sapo/invoice/` — Developer OS chỉ index và link tới, không copy code/tài liệu vào đây (One Source of Truth).

## Repo con

| Repo (path trong `/Users/sapo/invoice/`) | Vai trò | Stack |
|---|---|---|
| `invoice-app/` | Merchant app nhúng trong Sapo | React (Vite) + Java (Gradle) |
| `sapo-invoice-admin-frontend/` | Admin UI | React + TypeScript + Vite + pnpm |
| `sapo-invoice-admin-service/` | Admin API | Java + Gradle |
| `sapo-pay-service/` | Payment service | Java (JHipster) + Maven |
| `invoice-docs/` | SRS, BMAD docs, workflow, tài liệu TVAN | Markdown |
| `ai-workspace/` | Toolbox AI cho toàn bộ dự án — prompts, rules, templates theo stack Java/React cụ thể của dự án này | Git repo riêng |

`servers/` trong cùng workspace là bản clone tham khảo của `@modelcontextprotocol/servers`, không thuộc sản phẩm Sapo Invoice.

## AI context của dự án này (`ai/`)

Developer OS thay thế `ai-workspace` (AI toolkit riêng trước đây của dự án) cho phần đang thực sự dùng:

- [[10_Projects/sapo-invoice/ai/project-instructions]] — context, workflow, conventions tổng thể (bắt đầu từ đây)
- [[10_Projects/sapo-invoice/ai/rules-backend]] — rules Java/Spring Boot
- [[10_Projects/sapo-invoice/ai/rules-frontend]] — rules React/TypeScript

Phần chưa migrate (thư viện prompt theo bước, template `SELFTEST_CHECKLIST.md`, BMAD skills — ít dùng hơn) vẫn ở `ai-workspace/` bên ngoài, chuyển dần khi thực sự cần thay vì chuyển hết một lần.

## SRS, Decision, Bug của dự án này

- **Có SRS từ BA:** nằm trong `invoice-docs/` (repo ngoài, BA giữ) — developer-os chỉ link tới, không copy.
- **Không có SRS từ BA** (task nhỏ, không qua BA): tự viết spec ngắn ngay trong `10_Projects/sapo-invoice/` bằng template `SRS.md`.
- **Quyết định kỹ thuật (ADR) và Bug cụ thể của dự án này:** ghi trực tiếp trong `10_Projects/sapo-invoice/` bằng template `Decision.md`/`Bug.md` — không ghi rải rác ở `ai-workspace` hay `invoice-docs` nữa.
- Bài học đủ tổng quát cho dự án khác → promote sang [[20_Knowledge/README|20_Knowledge]] hoặc [[30_AI/Rules/senior-engineering-practices]].

## Liên kết

- Entry point AI cho toàn bộ workspace ngoài vault: `/Users/sapo/invoice/AGENTS.md`
- Nguyên tắc AI tổng quát (nhiều dự án): [[30_AI/Rules/senior-engineering-practices]]
- Thư viện UI dùng chung (đang migrate tới): [[10_Projects/design-system/README]] — xem quyết định [[10_Projects/sapo-invoice/migrate-ui-components-sang-design-system]]

## Ghi chú

Dự án đang active, vận hành qua nhiều repo độc lập. Developer OS giờ là nơi lưu quyết định kỹ thuật, bài học, bug, và AI context đặc thù của dự án này — thay vì rải rác giữa `ai-workspace` và ghi chú tạm.
