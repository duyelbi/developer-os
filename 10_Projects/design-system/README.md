---
created: 2026-07-29 17:00
status: Active
---

# Design System (Sapo Finance)

Thư viện UI/token/tài nguyên thiết kế dùng chung cho các sản phẩm Sapo Finance (bao gồm Sapo Invoice). Workspace thật nằm ngoài vault, tại `/Users/sapo/Design-System/` — developer-os chỉ index và link tới, không copy code/tài liệu vào đây (One Source of Truth).

## Repo con

| Repo (path trong `/Users/sapo/Design-System/`) | Vai trò | GitLab |
|---|---|---|
| `design-system/` | Mono-repo chính (pnpm workspace): `packages/tokens`, `packages/components` (React), `packages/mcp-ds` (MCP server nội bộ cho AI agent) | `sapo-money/design-system/design-system` |
| `docs/` | Tài liệu governance/charter/decision-engine/pattern-library, đánh số 00→12 | `sapo-money/design-system/docs` |
| `config/` | Shareable config: oxlint/oxfmt/tsconfig cho các dự án Sapo Finance (`@sapo-finance/config`) | `sapo-money/design-system/config` |
| `resources/` | Icon, illustration, logo, font (`@sapo-finance/resources`) | `sapo-money/design-system/resources` |

Publish qua GitLab Package Registry, scope `@sapo-finance`. Stack: Node ≥22, pnpm, TypeScript, oxlint/oxfmt (không dùng ESLint/Prettier), Storybook, Changesets.

## Khác với Sapo Invoice — không migrate rules vào đây

Không giống `ai-workspace` (đã migrate vào `10_Projects/sapo-invoice/ai/`), hệ thống AI của design-system đã rất trưởng thành và **tự khai báo single source of truth rõ ràng**: theo `design-system/AGENTS.md`, "các file `.cursor/skills/*` là nguồn sự thật duy nhất". Copy nội dung này vào developer-os sẽ vi phạm chính nguyên tắc One Source of Truth mà developer-os theo đuổi — nên **không tạo** `10_Projects/design-system/ai/`.

Muốn xem rules/skill thật, vào thẳng:
- Context + skill routing: `design-system/AGENTS.md`, `design-system/CLAUDE.md`
- Rule package component: `design-system/packages/components/AGENTS.md`
- Quy trình 2 pha tạo component mới: `figma-to-spec` → `spec-to-component` → `component-review` (skills trong `design-system/.cursor/skills/`)
- Config chia sẻ: `config/AGENTS.md`, `config/.cursor/rules/sapo-config.mdc`
- Tài nguyên (icon/font/logo): `resources/AGENTS.md`

developer-os ở đây chỉ giữ: quyết định kỹ thuật, bug, bài học **từ góc nhìn của Duy khi tích hợp/dùng design-system trong các dự án khác** (vd Sapo Invoice) — dùng `Decision.md`/`Bug.md` đặt phẳng ngay trong `10_Projects/design-system/`.

## Quan hệ với @sapo/ui-components (đã xác nhận)

`@sapo/ui-components` (dùng trong `rules-frontend.md` của Sapo Invoice) là thư viện UI **cũ**, riêng của Invoice. `@sapo-finance/components` (package chính của repo này) là thư viện **mới**, dùng chung cho nhiều service Sapo Finance — mục tiêu tối ưu và đồng bộ hơn giữa các service của công ty. Sapo Invoice đang migrate dần sang thư viện này — xem quyết định: `10_Projects/sapo-invoice/migrate-ui-components-sang-design-system.md`.

## Note của dự án

| Note | Nội dung |
|---|---|
| [[10_Projects/design-system/audit-coverage-invoice]] | Audit độ phủ DS ↔ nhu cầu thật của invoice: backlog DS xếp theo trọng số sử dụng, kết luận React 19, thứ tự migrate |

## Liên kết

- Bên tiêu thụ chính: [[10_Projects/sapo-invoice/README]] — kế hoạch refactor: [[10_Projects/sapo-invoice/refactor-frontend-performance]]
