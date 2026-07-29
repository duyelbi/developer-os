---
created: 2026-07-29 17:15
status: Accepted
---

# Migrate UI library: @sapo/ui-components → @sapo-finance/components

## Context

Frontend Sapo Invoice (`invoice-app`, `sapo-invoice-admin-frontend`) hiện dùng `@sapo/ui-components` — thư viện UI cũ, riêng của Sapo Invoice. Công ty đang xây `@sapo-finance/components` (mono-repo [[10_Projects/design-system/README]], scope `@sapo-finance`) làm thư viện UI/token dùng chung cho nhiều service Sapo Finance, không chỉ riêng Invoice.

## Decision

Migrate dần từ `@sapo/ui-components` sang `@sapo-finance/components`. `@sapo/ui-components` là legacy, không phát triển thêm tính năng mới; `@sapo-finance/components` là thư viện đích.

## Consequences

- Component/màn hình mới (đã xác nhận thuộc phạm vi migrate) ưu tiên dùng `@sapo-finance/components` thay vì `@sapo/ui-components` — xem `10_Projects/sapo-invoice/ai/rules-frontend.md`.
- Trong giai đoạn chuyển tiếp, codebase tồn tại song song 2 thư viện — cần rõ ràng phần nào đã migrate, phần nào chưa, tránh trộn lẫn 2 hệ token/component trong cùng 1 màn hình.
- Rules/convention chi tiết của `@sapo-finance/components` không lặp lại ở đây — xem `design-system/packages/components/AGENTS.md` (single source of truth riêng, theo [[10_Projects/design-system/README]]).
- Chưa có timeline/phạm vi migrate cụ thể (module nào trước, module nào sau) — bổ sung khi có kế hoạch rõ, không suy đoán trước.

## Alternatives

- Giữ nguyên `@sapo/ui-components`, không migrate — bị loại vì không đồng bộ với các service khác của công ty, đi ngược mục tiêu chuẩn hóa.
