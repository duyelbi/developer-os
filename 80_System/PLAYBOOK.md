---
created: 2026-07-29 18:00
updated: 2026-07-29 18:00
---

# Playbook — Làm việc với Claude / Cursor / Obsidian / developer-os

> **Loại tài liệu:** Hướng dẫn thao tác, theo tình huống (khác `WORKFLOW.md` — mô tả luồng chung; tài liệu này trả lời trực tiếp "tôi đang làm việc X, mở ở đâu và làm gì trước")
> **Cách dùng:** Mở đầu mỗi phiên làm việc, tìm đúng case, làm theo. Không lặp lại nội dung đã có ở `WORKFLOW.md`/`CLAUDE.md`/`CONVENTION.md` — chỉ trỏ tới.

---

## Mục lục

1. [Quyết định nhanh — mở ở đâu](#1-quyết-định-nhanh--mở-ở-đâu)
2. [Case: Task mới trong Invoice](#2-case-task-mới-trong-invoice)
3. [Case: Bug trong Invoice](#3-case-bug-trong-invoice)
4. [Case: Task implement component trong Design System](#4-case-task-implement-component-trong-design-system)
5. [Case: Fix bug component trong Design System](#5-case-fix-bug-component-trong-design-system)
6. [Case: Task trong dự án cá nhân](#6-case-task-trong-dự-án-cá-nhân)
7. [Case: Onboard một project/repo mới](#7-case-onboard-một-projectrepo-mới)
8. [Case khác](#8-case-khác)
9. [Còn để mở](#9-còn-để-mở)
10. [Changelog](#10-changelog)

---

## 1. Quyết định nhanh — mở ở đâu

| Việc cần làm | Mở ở đâu |
|---|---|
| Kiến trúc, quy ước, roadmap của chính developer-os | Chat này (Cowork/claude.ai, project developer-os) |
| Task/bug cụ thể trong repo Invoice | Claude Code, mở tại `/Users/sapo/invoice` (root, để `AGENTS.md` tự route) hoặc đúng repo con nếu chỉ sửa 1 chỗ |
| Task/bug cụ thể trong Design System | Claude Code, mở tại `/Users/sapo/Design-System` (root) hoặc đúng repo con (`design-system/`, `docs/`, `config/`, `resources/`) |
| Code trực tiếp trong IDE | Cursor, cùng root tương ứng ở trên |
| Dự án cá nhân/repo hoàn toàn mới | Xem [case 7](#7-case-onboard-một-projectrepo-mới) — cần setup 1 lần trước khi làm task đầu tiên |

Nguyên tắc chung: chi tiết đặc thù dự án (rules, spec, quy trình) luôn đọc từ **repo thật** của dự án đó (qua `AGENTS.md`/`CLAUDE.md` của repo), không đoán hay hỏi từ trí nhớ. developer-os chỉ giữ phần đã chốt là dùng chung/lâu dài (Decision, Bug, Knowledge) — xem `ARCHITECTURE.md` §2 (One Source of Truth).

---

## 2. Case: Task mới trong Invoice

1. Có SRS trong `invoice-docs` (BA viết) → đọc trực tiếp. Không có → tự viết spec ngắn bằng `SRS.md` trong `10_Projects/sapo-invoice/` (`status: Draft`) — xem [[10_Projects/sapo-invoice/ai/project-instructions]].
2. Mở Claude Code tại `/Users/sapo/invoice` (hoặc đúng repo). `AGENTS.md` tự trỏ Claude đọc `project-instructions.md` + `rules-backend.md`/`rules-frontend.md` trong developer-os.
3. Phân tích/planning: có quyết định kỹ thuật đáng nhớ (chọn lib, đổi kiến trúc) → tạo `Decision.md` (`Proposed → Accepted`). Cập nhật SRS sang `Approved`.
4. Implement (Cursor/Claude Code) theo `rules-backend`/`rules-frontend`.
5. Review code: dán diff cho Claude, theo thứ tự Security > Correctness > Performance > Readability.
6. Test, xác nhận theo SRS.
7. Push + tạo MR (GitLab, `git.dktsoft.com`) — dùng MCP GitLab nếu Claude Code có sẵn (`mcp__GitLab__create_merge_request`), hoặc thao tác tay.
8. Sau khi merge: SRS → `Implemented`. Bug/Decision/bài học phát sinh trong quá trình → Claude tự đề xuất lưu và tạo file thẳng vào `10_Projects/sapo-invoice/` (đã cấu hình ở `project-instructions.md`, không cần bạn tự làm). Bài học đủ tổng quát → promote sang [[20_Knowledge/README|20_Knowledge]] hoặc `senior-engineering-practices.md`.

---

## 3. Case: Bug trong Invoice

1. Mở Claude Code tại repo liên quan (hoặc root `/Users/sapo/invoice`). Mô tả bug.
2. Claude: hypothesis root cause + confidence, 2-3 phương án fix kèm tradeoff (theo `project-instructions.md` mục "Khi tôi báo bug").
3. Chọn phương án → Cursor implement.
4. Test lại, xác nhận không tái phát.
5. Claude tự đề xuất và tạo `Bug.md` trong `10_Projects/sapo-invoice/` (`Open → Resolved → Closed`) — không cần bạn tự vào Obsidian.
6. Root cause là pattern tái dùng được (không riêng Invoice) → thêm vào `senior-engineering-practices.md` hoặc Knowledge, link ngược từ Bug.

---

## 4. Case: Task implement component trong Design System

Design System **đã có** quy trình AI riêng, trưởng thành hơn Invoice — không lặp lại ở developer-os:

1. Mở Claude Code/Cursor tại `/Users/sapo/Design-System/design-system` (hoặc root `/Users/sapo/Design-System`).
2. Theo đúng quy trình 2 pha đã có sẵn trong repo (xem `design-system/AGENTS.md`): `figma-to-spec` (có Figma) hoặc `port-to-spec` (không Figma) → `SPEC.md` → `spec-to-component` (sinh component + stories, theo `component-showcase`) → `component-review` (gate cuối trước MR).
3. Storybook dev: `pnpm --filter @sapo-finance/components storybook` (port 6006) để so sánh visual.
4. Release: MR kèm changeset (`pnpm changeset`) — xem `RELEASING.md` trong repo.
5. developer-os **không tham gia** bước kỹ thuật này — chỉ ghi nhận nếu phát sinh quyết định/bug đáng nhớ ở mức cao hơn (vd đổi convention chung, migrate thư viện) → `Decision.md`/`Bug.md` trong `10_Projects/design-system/`, xem [[10_Projects/design-system/README]].

---

## 5. Case: Fix bug component trong Design System

1. Xử lý ngay trong repo `design-system/` — dùng test (`pnpm --filter @sapo-finance/components test`), Storybook, gate `component-review` như bình thường. Không cần qua developer-os để fix.
2. Chỉ tạo `Bug.md` trong `10_Projects/design-system/` khi bug đó đủ đáng nhớ ở mức cross-project (vd một lỗi lặp lại nhiều lần, hoặc ảnh hưởng tới cách Invoice/các consumer khác dùng thư viện) — không ghi mọi bug nhỏ vào đây, tránh trùng lặp với changelog/issue tracker riêng của repo.

---

## 6. Case: Task trong dự án cá nhân

Nếu dự án đã có entry trong `10_Projects/<ten-du-an>/` — làm y hệt case 2 (Invoice), thay path tương ứng.

Nếu là dự án cá nhân **mới, chưa có gì** — dự án cá nhân thường không có SRS từ BA hay skill riêng như Design System, nên mô hình gần với Sapo Invoice lúc mới bắt đầu (Phase 4):

1. Setup 1 lần — xem [case 7](#7-case-onboard-một-projectrepo-mới).
2. Không có BA/SRS → viết spec ngắn trực tiếp bằng `SRS.md` (hoặc bỏ qua nếu task quá nhỏ, không đáng 1 SRS).
3. Decision/Bug/Knowledge ghi trực tiếp trong `10_Projects/<ten-du-an>/`, cùng quy tắc chủ động lưu (Claude đề xuất → tự tạo file) như đã thiết lập cho Sapo Invoice — nếu chưa cấu hình, thêm hướng dẫn tương tự vào `project-instructions.md`/`CLAUDE.md` của dự án đó.

---

## 7. Case: Onboard một project/repo mới

Checklist dùng lại được — đã áp dụng cho Sapo Invoice và Design System:

1. Tạo `10_Projects/<ten-du-an>/README.md` (frontmatter `status: Active`, xem `METADATA.md` §3.5) — mô tả repo con, stack, liên kết.
2. Quyết định có cần `ai/` subfolder không:
   - Dự án có AI toolkit riêng (rules/prompt) **đang thực sự dùng**, muốn developer-os thay thế → tạo `10_Projects/<ten-du-an>/ai/`, migrate phần đang dùng (không migrate hết một lần — xem `ARCHITECTURE.md` §12.3).
   - Dự án đã có hệ thống AI riêng **trưởng thành, tự khai single source of truth** (như Design System) → **không** tạo `ai/`, chỉ index + link.
3. Claude Code: thêm `/Users/sapo/developer-os` vào `additionalDirectories` trong `.claude/settings.local.json` — ở root workspace nếu quen mở cả folder, hoặc từng repo nếu quen mở riêng lẻ.
4. Cursor: đảm bảo `filesystem` MCP (`~/.cursor/mcp.json`) có path cả project mới lẫn `/Users/sapo/developer-os` trong roots/args — sửa xong phải restart Cursor.
5. Nếu workspace có nhiều repo con, cân nhắc thêm 1 `AGENTS.md` router ở root (mẫu: `/Users/sapo/invoice/AGENTS.md`) trỏ vào rules/context trong developer-os.

---

## 8. Case khác

- **Học tiếng Nhật / tiếng Anh / công nghệ mới:** chat trực tiếp với Claude (bất kỳ đâu) để luyện/hỏi, ghi tự do vào [[70_Learning/README|70_Learning]] — không cần template. Hiểu và dùng được ít nhất 1 lần → promote sang [[20_Knowledge/README|20_Knowledge]] (`WORKFLOW.md` §5).
- **Review Inbox cuối tuần:** xem `WORKFLOW.md` §2 (Inbox Aging) — promote hoặc xóa item cũ.
- **Journal cuối ngày/tuần:** ghi vào [[60_Journal/README|60_Journal]] (`YYYY-MM-DD.md`), tách Knowledge/Project note nếu có insight đáng giữ (`WORKFLOW.md` §6).
- **Career review định kỳ:** ghi vào [[50_Career/README|50_Career]] khi review tháng/quý hoặc đổi hướng nghề.

---

## 9. Còn để mở

Case "nhiều task chạy song song trên nhiều dự án cùng lúc" (context switch) chưa có hướng dẫn riêng — bổ sung khi thực tế gặp khó khăn cụ thể, không suy đoán trước.

---

## 10. Changelog

| Phiên bản | Ngày | Thay đổi |
|---|---|---|
| v1 | 2026-07-29 | Bản đầu tiên: quyết định nhanh mở ở đâu, case Invoice (task/bug), case Design System (task/bug component), case dự án cá nhân, case onboard project/repo mới, case khác (Learning/Inbox/Journal/Career) |

---

_Tài liệu thuộc Core System. Khi có case mới lặp lại đủ nhiều lần, thêm vào đây — không thêm case suy đoán trước khi gặp thật._
