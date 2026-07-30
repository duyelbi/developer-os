---
created: 2026-07-29 16:00
scope: "Master project instructions — Sapo Invoice (context, workflow, conventions cho Claude/Cursor)"
---

# Project Instructions — Sapo Invoice

Migrate và cập nhật từ `ai-workspace/rules/claude-instructions.md`. Đây là bản chính thức — khi có thay đổi, sửa ở đây trước, không sửa file cũ bên `ai-workspace`.

## Trạng thái migrate (đọc trước)

- **Đã chuyển hẳn vào đây:** context dự án, tech stack, workflow tổng quát, conventions review/bug/communication (nội dung bên dưới).
- **Vẫn còn ở `ai-workspace/` (chưa migrate, dùng khi cần):** thư viện prompt theo bước (`prompts/01-ba-analysis` → `prompts/10-api-browser-test`), template `SELFTEST_CHECKLIST.md`, BMAD agents/skills. Những phần này chưa được dùng đủ thường xuyên để đáng chuyển ngay — chuyển dần khi thực sự cần (Evolutionary Design), xem `ARCHITECTURE.md` §12.3.
- **`invoice-docs` vẫn là nguồn SRS chính thức** do BA phụ trách — không migrate, chỉ tham chiếu.

## Context

Tôi (Duy) là developer tại Sapo, làm việc trên hệ thống **hoá đơn điện tử** (e-invoice). Dự án gồm nhiều repo: `invoice-app` (hybrid monolith), `sapo-invoice-admin-frontend`, `sapo-invoice-admin-service`, `sapo-pay-service`, `invoice-docs` — xem danh sách đầy đủ ở [[10_Projects/sapo-invoice/README]].

## Tech Stack thực tế

**Backend (invoice-app + admin-service + pay-service):**
- Java 17 + Spring Boot 3.3.x + Gradle (Kotlin DSL) — `sapo-pay-service` dùng JHipster + Maven
- Architecture: **DDD Layered** (interfaces → application → domain → infrastructure)
- MariaDB + JPA/Hibernate 6.x — **KHÔNG có Flyway** (manual SQL migrations)
- Elasticsearch 8.8.x, Redis, Kafka, RabbitMQ, Quartz JDBC
- Multi-tenancy: `@EmbeddedId {long id, long tenantId}` cho mọi entity
- Format: Palantir Java via Spotless
- Chi tiết đầy đủ: [[10_Projects/sapo-invoice/ai/rules-backend]]

**Frontend (invoice-app + admin-frontend):**
- React 18 + TypeScript 5.3 (strict)
- Redux Toolkit + **RTK Query** (ONE `api.ts` instance — KHÔNG split)
- `@sapo/ui-components` (proprietary UI library — KHÔNG dùng Storybook, Tailwind)
- React Hook Form + Yup + `useCustomForm` pattern
- `@sapo/app-bridge-react` (iframe/Sapo Admin integration)
- Admin frontend: thêm Preact Signals, @dnd-kit, Sentry
- Chi tiết đầy đủ: [[10_Projects/sapo-invoice/ai/rules-frontend]]

**Docs (invoice-docs — repo ngoài, BA giữ):**
- Workflow SRS: `invoice-docs` repo với BMAD agents + custom skills
- Templates: `srs-uc.md` (UI features) hoặc `srs-domain.md` (backend/integration)
- Ngôn ngữ: Tiếng Việt, giữ thuật ngữ kỹ thuật tiếng Anh
- **Một số task không có SRS trong `invoice-docs`** (task nhỏ, không qua BA) — với các task này, tự viết spec ngắn bằng template `SRS.md` ngay trong `10_Projects/sapo-invoice/` (developer-os), không chờ BA.

## Workflow của tôi

```
1.  [invoice-docs]  BA analysis → SRS (nếu có BA cho task này)
    [developer-os]  Nếu task KHÔNG có SRS từ BA → tự viết spec ngắn bằng template SRS.md
2.  [Tôi]          QA với BA team (nếu có) → confirm requirements
3.  [Claude]        Phân tích SRS/spec → requirements summary + câu hỏi cần làm rõ
4.  [Claude]        Thiết kế backend (DDD + SQL + API) — theo rules-backend
5.  [Claude]        Thiết kế frontend (components + RTK Query) — theo rules-frontend
6.  [Cursor]        Implement theo thiết kế ở bước 4-5
7.  [Claude]        Review code — theo tiêu chí ở mục "Khi tôi share code để review"
8.  [Claude]        Phân tích bug nếu có → root cause + phương án fix
9.  [Cursor]        Fix theo phương án đã chọn
10. [Claude]        Test API + browser, xác nhận fix
11. ✅ Ship
```

**Release `invoice-app` staging → master:** không tự merge/đề xuất merge master chỉ vì staging build xanh — cần tester + BA duyệt trên staging trước, leader mới là người merge. Bug trên staging → sửa ở feature branch gốc rồi lên lại staging (MR mới hoặc merge thẳng). Chi tiết: [[10_Projects/sapo-invoice/invoice-app-staging-master-release-flow]].

Bug, quyết định kỹ thuật, bài học rút ra trong quá trình trên → ghi vào `10_Projects/sapo-invoice/` bằng template `Bug.md`/`Decision.md` (developer-os), không ghi rải rác nơi khác — xem cách lưu chủ động ở mục dưới. Bài học đủ tổng quát cho dự án khác → promote sang [[20_Knowledge/README|20_Knowledge]] hoặc [[30_AI/Rules/senior-engineering-practices]].

## Lưu artifact lâu dài — chủ động, không chờ Duy làm thủ công

Duy không muốn phải tự mở Obsidian hay vào repo `developer-os` để lưu lại — Claude/Cursor tự làm việc này. Áp dụng cho **mọi thứ đáng giữ lâu dài**, không chỉ Bug/Decision: implementation plan/spec (đặc biệt task không có SRS chính thức từ BA — xem mục "Docs" ở trên), root-cause analysis, kết quả research kỹ thuật, prompt Cursor gắn liền với 1 plan cụ thể. Mặc định: **không để các file này ở scratchpad/tmp hay chỉ tồn tại trong chat** — lưu vào `developer-os` ngay khi nội dung đã đủ ổn định để tham chiếu lại sau.

1. Ngay sau khi xác nhận đã fix xong một bug, chốt một quyết định kỹ thuật đáng nhớ (tiêu chí ở `WORKFLOW.md` §3/§4), hoặc vừa hoàn thiện một implementation plan/spec đủ chi tiết để đưa cho Cursor implement → đề xuất ngắn gọn, vd *"Lưu vào developer-os nhé?"*. Nếu ngữ cảnh đã rõ ràng (Duy đã nói kiểu "nhớ lưu lại", "lưu lâu dài"), không cần hỏi lại, làm luôn.
2. Sau khi Duy xác nhận (hoặc không phản đối) → **tự tạo file trực tiếp**, không yêu cầu Duy làm tay:
   - Path: `/Users/sapo/developer-os/10_Projects/sapo-invoice/<ten-file-kebab-case>.md` (đặt phẳng, không vào subfolder `ai/` — `ai/` chỉ chứa rules/prompt, không chứa instance Bug/Decision/Plan)
   - Tên file: mô tả ngắn gọn nội dung, kebab-case (`CONVENTION.md` §2) — vd `invoice-tenant-id-race-condition.md`, `epic-65-auto-invoice-order-name.md`
   - Frontmatter đúng schema `METADATA.md`: `Bug.md` cần `created`, `status`, `priority` (tuỳ), `project: "[[10_Projects/sapo-invoice/README]]"`; `Decision.md` cần `created`, `status`; implementation plan/spec không có SRS chính thức → dùng schema `SRS.md` (`created`, `status: Draft|Approved|Implemented`), có thể kèm `project` cho nhất quán.
   - Prompt Cursor gắn liền với 1 plan cụ thể (không phải rule/prompt tái sử dụng nhiều task) → gộp làm 1 section trong cùng note với plan đó (nguyên tắc Atomic Notes: đây vẫn là cùng một khái niệm), không tạo file riêng.
3. Báo ngắn gọn đã lưu ở đâu sau khi tạo xong — không cần Duy xác nhận lại lần hai.

**Điều kiện kỹ thuật:** Claude Code chạy trong repo khác (`invoice-app`, `sapo-invoice-admin-frontend`...) cần quyền ghi ra ngoài project root của repo đó. Đã cấu hình bằng `permissions.additionalDirectories: ["/Users/sapo/developer-os"]` trong `.claude/settings.local.json` của từng repo. Nếu Claude Code vẫn hỏi xác nhận ghi file mỗi lần, kiểm tra lại file này còn đúng cấu hình không.

## Khi tôi hỏi về planning/analysis

- Specific: file paths cụ thể, class names, method signatures
- Follow **DDD layers**: controller → service → domain → repository → infra
- **Multi-tenancy** luôn được consider: tenantId trong mọi query
- Flag assumptions với ⚠️ ASSUMPTION + risk level
- Risk levels: 🔴 HIGH (DB migration, breaking API) / 🟡 MED (logic change) / 🟢 LOW (UI only)
- Break tasks theo dependency order
- Include TypeScript interfaces và Java records/DTOs trong specs

## Khi tôi share code để review

So sánh với spec VÀ kiểm tra project-specific rules:

**Backend:**
- `jakarta.*` — KHÔNG `javax.*`
- `findByIdAndTenantId()` — KHÔNG `findById()` đơn thuần
- Services return DTOs — KHÔNG domain entities
- `@Transactional(readOnly=true)` đúng chỗ
- `apache.commons` — KHÔNG Spring utils
- Factory methods — KHÔNG direct state copy từ request

**Frontend:**
- ONE `createApi()` instance — KHÔNG split API files
- `useCustomForm` — KHÔNG `useForm` trực tiếp
- `@sapo/ui-components` — KHÔNG tạo lại components
- `NO any` TypeScript
- Component dưới 200 lines

Priority: security > correctness > performance > readability
Severity: 🔴 Critical (blocker) / 🟡 Major (should fix) / 🟢 Minor (nice to have)

## Khi tôi báo bug

- Hypothesis root cause đầu tiên, kèm confidence level (X% confident)
- 2-3 fix options với effort + risk tradeoffs
- Cursor-ready implementation instructions
- Regression tests cần chạy sau fix
- Tự tạo `Bug.md` trong `10_Projects/sapo-invoice/` sau khi fix xong và xác nhận — xem mục "Lưu Bug/Decision" ở trên, không chờ Duy làm tay

## Conventions quan trọng

**Java:**
- Primary keys: `long` EmbeddedId `{long id, long tenantId}` — KHÔNG UUID
- Migrations: `V{n}__{description}.sql` — apply thủ công
- API path: `/api/` không có `/v1/`
- Business methods: `publish()`, `cancel()` — KHÔNG setters
- Lombok: `@RequiredArgsConstructor`, `@Slf4j`, `@Getter` — KHÔNG `@Data`
- `var` keyword: local variables only

**React:**
- TypeScript strict (no any)
- RTK Query: ONE `api.ts` — KHÔNG tách file
- Forms: `useCustomForm` + Yup
- Error: `transformErrors` (form) / `handleErrorApiV2` (toast) / `Sentry` (unexpected)
- UI: `@sapo/ui-components`

## Communication style

- ⚠️ warnings/assumptions | ✅ confirmed/good | ❌ issues/problems
- Structured với clear headers
- Code examples hơn là descriptions
- Tiếng Việt cho giải thích, Tiếng Anh cho code/technical terms
- Ngắn gọn — không summary dài dòng cuối response

## Domain context (invoice điện tử VN)

- Tuân theo quy định thuế VN (Thông tư 78/2021/TT-BTC)
- CQT = Cơ quan thuế (Tax Authority)
- TVAN = đơn vị trung gian truyền nhận hoá đơn với CQT
- Hoá đơn lifecycle: draft → published → provided → accepted/rejected
- Digital signing (chữ ký số): EasyCA, HiLoca certificates
- Multi-tenant: mỗi store/merchant là một tenant riêng biệt

---

_Nguồn: `ai-workspace/rules/claude-instructions.md`, cập nhật cho quyết định "developer-os thay ai-workspace cho phần đang dùng thật" (2026-07-29)._
