---
created: 2026-10-12 10:00
status: Active
progress: "2026-10-12 — task 0, 7, 8–10 xong (MR DS !169, docs !330). Task 11 chưa chạy agent mới. Task 12–13 xong trên working tree app, chưa commit. Task 14: đã nối xoá / cập nhật trạng thái / confirm sửa; lập phiếu xuất-nhập chưa có popup trên màn danh sách enterprise; chưa chạy route thật."
---

# Pattern màn chi tiết `detail-page@1` — việc còn lại

Kế hoạch triển khai cho agent (Cursor / Claude). Đọc hết mục **0. Bối cảnh** trước khi làm bất kỳ task nào. Mỗi task có **Đầu ra** và **Xong khi** — chưa đạt "Xong khi" thì chưa được đánh dấu xong.

Yêu cầu gốc (chia việc Hải / Duy): https://claude.ai/artifact/GKzw4gHwA6XcS7KJw58EAD — Hải làm `form-page@1`, Duy làm `detail-page@1`, theo đúng quy trình đã làm cho `list-page@1`.

---

## 0. Bối cảnh

### 0.1 Ba repo, ba nhánh

Workspace: `/Users/sapo/Design-System/`

| Repo | Thư mục | Nhánh Duy | Cắt từ | Trạng thái |
| --- | --- | --- | --- | --- |
| design-system (DS) | `design-system/` | `feature/pattern-detail-page` | `origin/master` | MR !169 (Draft) — bước 1–6 xong, có thay đổi chưa commit (task 0.1) |
| sapo-accounting-docs | `sapo-accounting-docs/` | `feature/uispec-detail-page` | `origin/feature/uispec-list-page-base` | Chưa làm gì |
| sapo-accounting-frontend | `sapo-accounting-frontend/` | `SA1/feature/detail-page` | `origin/SA1/test/list-page-base` | Có `.agents/rules/when/detail-page.md` đã viết lại, chưa commit |

Ba nhánh đã bỏ upstream mặc định — lần push đầu dùng `git push -u origin <nhánh>`.

MR DS: https://git.dktsoft.com:2008/sapo-money/design-system/design-system/-/merge_requests/169 (reviewer: Hải — `haidv2`).

Nhánh của Hải (chỉ để **đọc tham khảo**, không merge / rebase lên): `origin/feature/pattern-form-page` (DS). Form-page sẽ lên master trước.

### 0.2 Luật làm việc (bắt buộc)

- **Chỉ sửa file mang tên `detail-page`** ở cả 3 repo, cộng: 1 import + 1 dòng ở `packages/mcp/src/lib/screenPattern/registry.ts` (DS); 1 dòng bảng pattern trong `SKILL.md` (docs).
- File dùng chung — báo Hải trước, đổi nhỏ: DS `packages/patterns/src/define.ts`, `scripts/build-screens.mjs`, `screenPattern/rules.ts` · `validate.ts` · `resolve.ts`, README, `AGENTS.md`; docs phần còn lại của `SKILL.md`; app rule chung (`source-tree.md`, `feature-page-*.md`, `data-grid.md`).
- **Không đụng list-page** ở cả 3 repo.
- **Không rebase lên nhánh của Hải, không lấy commit của Hải.** Cần thống nhất thì đọc code của Hải và làm cho file dùng chung **giống từng byte** bản của Hải (git tự gộp thay đổi trùng nhau). Đã làm vậy cho `define.ts`, `build-screens.mjs`, `loadScreenPatterns.ts`.
- `docs/contracts/check.mts` và `docs/contracts/README.md`: **sửa trực tiếp** (Hải cũng sửa hai file này) — conflict thì resolve khi merge, không tách file mới.
- Commit: **không** thêm `Co-Authored-By` hay dòng "Generated with Claude Code" vào commit / MR / comment. Commit message theo kiểu `feat(patterns,mcp): …` / `fix(…)`, tiếng Việt.
- MR mở theo thứ tự **DS → docs → app**.
- App: không thêm `console`, không comment trong code production, chữ UI tiếng Việt, chỉ `pnpm`.

### 0.3 Môi trường máy

- Shell trong `/Users/sapo/Design-System` đang nhận **node v14** (nvm tự đổi) → `pnpm` lỗi `??=`. Luôn chạy với node 24:
  `export PATH=/Users/sapo/.nvm/versions/node/v24.16.0/bin:$PATH`
- `pnpm contracts:check` báo lỗi `tableCell` ở DataGrid khi `dist` của tokens cũ → chạy `pnpm --filter @sapo-finance/tokens build` một lần.
- Dev server app: `pnpm dev:ent` trong `sapo-accounting-frontend` (cần alias `sudo ifconfig lo0 alias 127.0.0.2 up` sau mỗi lần khởi động máy). Mở `https://accounting-dev.sapocorp.vn/admin/production_orders` bằng Chrome profile "Browser 1" (store **Manh DN FINAL**, có 4 LSX: LSX000001 Hoàn thành · LSX000002–4 Đang thực hiện).

### 0.4 Cổng kiểm DS (chạy trước mỗi lần push)

```bash
pnpm patterns:build
pnpm --filter @sapo-finance/mcp typecheck && pnpm --filter @sapo-finance/mcp test && pnpm --filter @sapo-finance/mcp smoke
pnpm contracts:check
pnpm rules:check && pnpm lint && pnpm format:check
```

Kỳ vọng hiện tại: `list-page@1` hash **`174b5d3b`** không đổi · `mcp test` 86/86 · các lệnh khác exit 0. Sửa pattern / MCP xong phải restart server `sapo-ds` trong app đang dùng.

### 0.5 Những gì đã có (đừng làm lại)

DS, nhánh `feature/pattern-detail-page` — commit `82ad358` (bước 3–6) + `58691d0` (sửa theo review Hải):

| Thứ | File |
| --- | --- |
| Pattern | `packages/patterns/src/screen/detail-page.ts` — vùng `header` (tiêu đề chuỗi mẫu `"Lệnh sản xuất {ref_no_finance}"`, `status`, `actions`) · `alert` · `general` · `line-items` (+ `children`) · `references` · `attachments`; state `default` · `loading` · `notFound` · `noPermission`; `uiSpec: { requiredSections: ["header","general"], nav: { required: true, menu: false } }` |
| MCP | `packages/mcp/src/lib/screenPattern/detail-page/{index,validate,metadata}.ts` — chỉ trả `metadata`, không dựng cây |
| Ca biên | `packages/mcp/test/detail-page/cases.mts` — 40 ca |
| UI Spec mẫu | `docs/contracts/fixtures/detail-page/production-order.DETAIL.uispec.yaml` |
| Đáp án code | `docs/contracts/fixtures/detail-page/production-order.DETAIL.code/` — `DetailPage/{DetailPage.tsx, index.tsx, uispec.gen.ts, uispec-cells.tsx, components/*}`, `components/DetailSkeleton.tsx`, `api.ts`, `types.ts`, `routes.tsx` (3 file cuối = trạng thái **sau khi chèn** lên đáp án list-page) |
| Rule app | `sapo-accounting-frontend/.agents/rules/when/detail-page.md` (chưa commit) — đo 40 DetailPage enterprise |

Đáp án code đã được chép tạm vào `apps/enterprise` và kiểm: phần detail 0 lỗi tsc, 0 lỗi oxlint (2 lỗi ở `ListPage/components/ProductionOrderTable.tsx(238)` có sẵn trên nhánh gốc app, không phải của detail).

---

## 1. Task 0 — Dọn trạng thái hiện tại

### 0.1 Commit phần thống nhất `uiSpec` với form-page (DS)

Working tree DS đang có thay đổi chưa commit: chép nguyên văn `define.ts`, `build-screens.mjs`, `loadScreenPatterns.ts` từ `origin/feature/pattern-form-page`; `detail-page.ts` khai `uiSpec` hình mới; bỏ kiểm `nav` tay trong `detail-page/validate.ts` (schema đã bắt); changeset bỏ đoạn hạ tầng.

- Đầu ra: một commit mới trên `feature/pattern-detail-page`, push lên MR !169.
- Xong khi: cổng kiểm §0.4 xanh; `git merge-tree --write-tree <HEAD> origin/feature/pattern-form-page` chỉ báo conflict ở `registry.ts` (dòng import — không tránh được vì formatter xếp import theo chữ cái) và `patterns.json` (file sinh). `git diff HEAD origin/feature/pattern-form-page -- packages/patterns/src/define.ts packages/patterns/scripts/build-screens.mjs packages/mcp/src/lib/loadScreenPatterns.ts` rỗng.

### 0.2 Commit rule app

- Đầu ra: commit `.agents/rules/when/detail-page.md` trên `SA1/feature/detail-page` (repo frontend). Chưa push / chưa mở MR (MR app mở sau cùng).
- Trước khi commit, cập nhật rule theo các quyết định sau review: cột STT khung code tự thêm theo vị trí dòng; không có state lỗi riêng (tải lỗi → về danh sách kèm toast `<Tên chứng từ> không tồn tại`); số lượng / tiền dùng `quantityCellProps` / `amountCellProps`; ô dựng từ `cellType` / `format` của `uispec.gen.ts`.

---

## 2. Task 7 — Skill `uispec-to-detail-page` (DS)

**Mục tiêu:** một lệnh sinh khung màn chi tiết vào repo app từ UI Spec, ra **đúng từng byte** đáp án `production-order.DETAIL.code/`.

**Khuôn tham khảo** (đọc trước khi viết):
- `.agents/skills/uispec-to-list-page/` trên master — `SKILL.md`, `list-page.mjs`, `emit.mjs`, `wire.mjs`, `check.mjs`, `lib/*`.
- `.agents/skills/uispec-to-form-page/` trên `origin/feature/pattern-form-page` (`git show origin/feature/pattern-form-page:<path>`) — **gần nhất với detail-page**: sinh lên trên feature đã có màn danh sách, chèn vào `api.ts` / `types.ts` / `routes.tsx` có sẵn (`lib/insert.mjs`), không có menu.

### 7.1 File cần tạo — `.agents/skills/uispec-to-detail-page/`

| File | Việc |
| --- | --- |
| `SKILL.md` | Frontmatter `name` + `description` (khi nào dùng / không dùng). 3 pha như list / form: **Sinh** (một lệnh `detail-page.mjs`) · **Xác nhận** (báo file ghi / chèn, id thêm / bớt, chờ user) · **Điền logic** (API, điều kiện ẩn / hiện action, modal xoá / cập nhật trạng thái / lập phiếu; kiểm bằng `check.mjs`). Bảng ranh giới sở hữu: chỉ `DetailPage/uispec.gen.ts` bị ghi đè khi sinh lại; còn lại sinh lần đầu rồi thuộc dev. Mục "Chuẩn bị máy" (`.mcp.json` trỏ repo DS). |
| `detail-page.mjs` | CLI: mở server MCP `sapo-ds` qua stdio (đọc `.mcp.json` hoặc `--mcp`), gọi `resolve_spec` bằng `spec_path` tuyệt đối, kiểm `server.stale`, chuyển `metadata` cho `emit.mjs`, rồi `wire.mjs`. Dừng không ghi khi: `blocked`, thiếu `metadata`, pattern không phải `detail-page@1`. |
| `emit.mjs` | `metadata` → file. Ghi đè `DetailPage/uispec.gen.ts` (khoá theo thứ tự cố định, kèm `builtWith: { generator: "uispec-to-detail-page@1", pattern, metadataHash }` và 4 kiểu id: `<Entity>DetailActionId`, `<Entity>GeneralFieldId`, `<Entity>LineColumnId`, `<Entity>LineChildColumnId`). Sinh lần đầu (không ghi đè nếu đã có): `DetailPage/{DetailPage.tsx, index.tsx, uispec-cells.tsx}`, `DetailPage/components/{GeneralInfoView, <Entity>LineItemsView, <Entity>ReferencesView, <Entity>AttachmentsView}.tsx` (view nào chỉ sinh khi metadata có vùng tương ứng), `components/DetailSkeleton.tsx`. **Chèn** (idempotent, chạy lại không chèn trùng): endpoint `get<Entity>` vào `api.ts`, kiểu `<Entity>DetailResponse` + kiểu dòng / dòng con vào `types.ts`, route `:id` vào `routes.tsx`. File chung lạ khuôn → dừng, không ghi. |
| `wire.mjs` | Detail không có menu và route `:id` nằm trong `routes.tsx` của feature — kiểm tra feature đã được nối vào phân hệ (màn danh sách đã làm); chưa thì báo, không tự nối menu. Nếu không cần thì bỏ file và ghi rõ trong `SKILL.md`. |
| `check.mjs` | Kiểm sau pha điền logic, theo khuôn `uispec-to-list-page/check.mjs`: `uispec.gen.ts` khớp `metadataHash`, mọi id trong `Record<…Id, …>` của dev đủ / không thừa, không còn handler `() => {}` cho action đang hiện. |
| `lib/names.mjs`, `lib/page-files.mjs`, `lib/data-files.mjs`, `lib/insert.mjs` | Tách như form-page. Được chép logic của form-page / list-page nhưng là **file riêng của detail-page** (không import chéo sang thư mục skill khác — skill được chép nguyên thư mục sang app). |

**Quy tắc sinh code (phải khớp đáp án):**
- Tiêu đề: `fillTitle(spec.title, record)` (chuỗi mẫu `{field}`).
- Action header: tối đa 2 action có icon hiện ngoài (`INLINE_ACTION_LIMIT = 2`), còn lại vào nhóm `spec.moreActionsLabel`; nhóm chỉ còn 1 thì đưa ra ngoài. Icon theo intent: `edit` → `PenLineIcon` · `clone` → `CopyIcon` · `status-change` → `RefreshIcon` · `derive` → `PlusCircleOutlineIcon` · `delete` không icon. Intent `post` / `unpost` / `print`: chọn icon có thật trong `@sapo/ui-icons` (đã kiểm: **không** có `TrashIcon`, `PrinterIcon`, `FilePlusIcon`; có `FileMinusIcon`) — chưa có thì không icon, ghi vào `SKILL.md`.
- `edit` → `url: <URL>/<id>/edit`; `clone` → `url: <URL>/create?clone_from=<id>`; còn lại `onAction: () => {}`.
- Ẩn / hiện action: import `can<Pascal(id)>` từ `../utils/row-action-visibility` (file của màn danh sách). Thiếu hàm → **chèn** `export const can<X>: RowRule = () => true;` vào file đó.
- Cột lưới: STT tự thêm đầu (`indexColumnMeta`), mỗi cột còn lại `columnMeta(column, width)`; độ rộng là `Record<ColumnId, width>` trong view (text `fill minWidth 200` cho `*_name`, `fixed 160` cho `*_sku`, `fixed 200` cho `code-name`, `fixed 100` cho `name`, `fixed 120` cho số).
- Kiểu dữ liệu sinh từ field + `cellType` / `format`: `text` / `datetime` → `string`; `number` → `number`; badge `true/false` → `boolean`; badge khác → union giá trị; `code-name` → `<x>_id`, `<x>_code`, `<x>_name`: `string`; `name` → `<x>_id`, `<x>_name`.

### 7.2 Khối kiểm trong `docs/contracts/check.mts` (sửa trực tiếp)

Theo khuôn `checkFormPage()` của Hải (`git show origin/feature/pattern-form-page:docs/contracts/check.mts`):
- `emit.mjs` sinh **lên trên** `fixtures/list-page/production-order.SCR01.code` ra đúng `fixtures/detail-page/production-order.DETAIL.code/` từng byte (output thô, chưa qua formatter app).
- Chạy lại lần 2 không đổi file nào, không chèn trùng.
- Input hỏng (`blocked`, sai pattern, thiếu metadata) và file chung lạ khuôn → dừng, không ghi.
- `detail-page.mjs` qua server stdio thật khớp đáp án.
- `pnpm contracts:update` sinh lại đáp án (chỉ dùng khi cố ý đổi đáp án).

Lưu ý: đáp án hiện tại đã qua `oxfmt` của app; emit ra "output thô" có thể khác format. Chọn một trong hai và ghi rõ: (a) emit ra đúng format như đáp án hiện tại, hoặc (b) sinh lại đáp án bằng `contracts:update` rồi kiểm lại tsc trên app (§0.5).

### 7.3 README `docs/contracts/README.md` (sửa trực tiếp)

Thêm mục `## Màn chi tiết — detail-page@1` theo khuôn mục form-page của Hải: pattern, MCP, chỉ trả `metadata` (`stats` chỉ có `metadataHash`), skill, bảng file fixture, cổng kiểm.

### 7.4 `AGENTS.md`

Thêm một dòng `uispec-to-detail-page` vào bảng skill (file dùng chung — dòng mới, không sửa dòng của người khác). Chạy `pnpm rules:adapters` nếu `rules:check` báo lệch.

**Xong khi:** cổng §0.4 xanh, có khối `detail-page` trong `contracts:check`; commit + push lên MR !169; cập nhật mô tả MR (bỏ "Bước 7" khỏi mục "Còn chờ").

---

## 3. Task 8–11 — Repo docs (`sapo-accounting-docs`, nhánh `feature/uispec-detail-page`)

Chỉ làm khi DS đã có pattern + MCP (đã có trên nhánh DS). Tạo `.mcp.json` (gitignore) ở gốc repo docs trỏ repo DS local:

```json
{
  "mcpServers": {
    "sapo-ds": {
      "type": "stdio",
      "command": "pnpm",
      "args": ["--dir", "/Users/sapo/Design-System/design-system/packages/mcp", "dev"],
      "env": {
        "SAPO_DS_MANIFEST": "/Users/sapo/Design-System/design-system/packages/components/manifest.json",
        "SAPO_DS_PATTERNS": "/Users/sapo/Design-System/design-system/packages/patterns/patterns.json"
      }
    }
  }
}
```

### 8. `reference/detail-page.md`

- File: `.agents/skills/srs-to-uispec/reference/detail-page.md`.
- Khung §0–§5 như `reference/list-page.md`; tham khảo thêm `reference/form-page.md` của Hải (giải thích bố trí, bộ chữ chuẩn kèm số đếm).
- §0: tên file `<entity>.<SCR>.uispec.yaml`, SRS không có mã màn → `DETAIL`. Mục SRS cần đọc: bảng domain (§3.1–3.3), hành vi (§3.4), BR (§4), AC "Xem chi tiết" (§5.x), AC phân quyền, mục UI màn chi tiết (§6.x), API chi tiết (§8.2.x). Bảng đối chiếu: trường header, cột bảng dòng / dòng con, action (tên, thứ tự, điều kiện), giá trị enum, tham chiếu / đính kèm, chữ không tồn tại.
- §1 chữ dựng được: tiêu đề `"<Tên chứng từ> {<field số chứng từ>}"`; `general.title` = `Thông tin chung`; `content.notFound.title` = `<Tên chứng từ> không tồn tại`; `moreActionsLabel` cố định "Thao tác khác" (không khai trong UI Spec).
- §2 tập đóng: intent header (`edit · clone · delete · status-change · derive · post · unpost · print`, chỉ `derive` được lặp), cellType ô xem, `format` (`money · quantity · code-name · name`), năng lực.
- §3 vùng và khoá; §4 state (`notFound` gồm cả tải lỗi; `noPermission` chặn ở route, không khai); §5 không được ghi (logic ẩn / hiện, STT, độ rộng cột).
- Ghi các quy ước đã chốt: "disable" trong SRS → khuôn là ẩn (rule PD ACT-1.1), ghi `open` cho BA.

### 9. `SKILL.md`

- **Thêm** dòng `| Chi tiết | detail-page@1 | [reference/detail-page.md](reference/detail-page.md) |` **ngay dưới** dòng chú thích `<!-- Chi tiết — detail-page (Duy) -->`. **Không thay** dòng chú thích (Hải đã thay dòng của form-page; thay nữa sẽ conflict). Khi cả hai nhánh đã lên thì mới bỏ các dòng chú thích HTML.
- Bước 5 (resolve_spec): Hải đã sửa thành "`stats.chars` / `unresolved` chỉ có khi pattern dựng cây" — với detail-page ghi `stats.metadataHash` vào báo cáo.

### 10. UI Spec thật

- Chạy skill `srs-to-uispec` trên `docs/enterprise/inventory/production-order/production-order.md`, màn §6.2 → `production-order.DETAIL.uispec.yaml` cạnh SRS.
- `validate_spec` (bằng `spec_path` tuyệt đối) tới **0 lỗi**; cảnh báo còn lại phải có comment tại dòng.
- Thêm đúng một dòng `> UI Spec máy đọc: [production-order.DETAIL.uispec.yaml](production-order.DETAIL.uispec.yaml)` dưới tiêu đề §6.2 của SRS.

### 11. Thử bằng agent mới

- Agent mới, chỉ cho đọc skill + SRS, viết lại UI Spec từ đầu; so với bản ở task 10. Chỗ lệch → sửa reference cho rõ.

**Xong khi:** commit + push nhánh docs, mở MR (sau MR DS).

---

## 4. Task 12–14 — Repo app (`sapo-accounting-frontend`, nhánh `SA1/feature/detail-page`)

### 12. Rule

Đã có (task 0.2). Rà lại sau khi skill xong cho khớp code sinh ra.

### 13. Chép skill

- Chép nguyên thư mục `design-system/.agents/skills/uispec-to-detail-page/` → `.agents/skills/uispec-to-detail-page/` và tạo adapter `.claude/skills/uispec-to-detail-page/SKILL.md` (frontmatter `name` + `description`, body trỏ `.agents/skills/...`) như `uispec-to-list-page`.
- Thêm một dòng vào bảng Playbook của `AGENTS.md` app.
- `.mcp.json` (gitignore) ở gốc repo app trỏ repo DS như §3.

### 14. Sinh màn LSX thật

- Chạy skill với UI Spec thật ở task 10 → sinh `apps/enterprise/src/pages/inventory/production-orders/DetailPage/` + chèn `api.ts` / `types.ts` / `routes.tsx` / `utils/row-action-visibility.ts`.
- Điền logic:
  - Xoá: `ConfirmModal` → `DELETE /admin/production_orders/{id}.json` → về danh sách; đã có phát sinh → lỗi `422 has_transaction` (BR03).
  - Cập nhật trạng thái: tái dùng modal của màn danh sách (`PUT /admin/production_orders/bulk_status.json`), ẩn khi `completed`.
  - Lập phiếu xuất / nhập: tái dùng modal / popup của màn danh sách (§6.4 / §6.5 SRS).
  - Sửa trên LSX đã có phát sinh: confirm "Lệnh sản xuất đã có phát sinh chứng từ. Bạn có muốn sửa không?" (BR09).
- Bấm số lệnh ở màn danh sách mở được màn chi tiết (hết warning `Invalid value for prop href`).
- Kiểm: `tsc` lọc theo `production-orders/` 0 lỗi mới (2 lỗi ListPage có sẵn — xem Q5), `pnpm lint` 0 lỗi; chạy trên route thật với LSX000001 (Hoàn thành: ẩn Lập phiếu, ẩn Cập nhật trạng thái) và LSX000004 (Đang thực hiện).

**Xong khi:** commit + push, mở MR app (sau MR docs).

---

## 5. Việc chờ người khác

### Khi form-page lên master

- Cập nhật nhánh DS theo **master** (không theo nhánh Hải). Conflict dự kiến: `registry.ts` → giữ cả hai import + hai dòng khai báo; `patterns.json` → `pnpm patterns:build`; `check.mts` / `README.md` contracts → giữ cả khối form-page và detail-page.
- Lấy từ form-page (đọc code của Hải, viết lại trong `detail-page/validate.ts` + ca biên): cảnh báo `LABEL_NONSTANDARD` cho nhãn nút chuẩn (Sửa · Nhân bản · Xóa…); đối chiếu cách Hải kiểm `FIELD_DUPLICATE` cho lưới con với bản của detail-page.
- Chạy lại cổng §0.4, bỏ Draft MR !169.

### Câu hỏi còn mở cho Hải (trong MR !169)

- **Q4** — chuyển `FEATURE_UNUSED` / `FEATURE_OFF` theo khoá lên `rules.ts` làm luật chung (MR riêng sau khi cả hai pattern merge)?
- **Q5** — lỗi tsc có sẵn trên `SA1/test/list-page-base`: `ListPage/components/ProductionOrderTable.tsx(238)` (`selectedCount` any).
- **Q6** — cho `contracts:check` tự build tokens trước?

### `open` trong UI Spec mẫu — chờ PD / BA / BE / PO

| # | Ai | Câu hỏi |
| - | -- | ------- |
| 1 | PD | Luật chia action header: hiện ngoài / "Thao tác khác" (đang tạm: tối đa 2 nút có icon ra ngoài) |
| 2 | BA + PD | Đã lập đủ PN / PX: SRS ghi chữ, màn LIST dùng checkmark (cảnh báo `BADGE_BOOLEAN`) |
| 3 | BA | Cập nhật trạng thái: SRS "disable khi completed", rule PD là ẩn |
| 4 | BA | Xóa: SRS "luôn hiện, chặn ở xác nhận"; bản individual ẩn khi đã có phát sinh |
| 5 | BE | Response chi tiết thiếu mã kho (chỉ `warehouse_name`); `sort_order` chưa trả (không chặn) |
| 6 | PD | Có cần state lỗi riêng (SystemState + Thử lại) như frame Figma không — hiện gộp vào `notFound` |
| 7 | PO | Giữ `DocumentDetailLayout` (bố cục cũ) cho khối thông tin chung |

Khi có câu trả lời: sửa UI Spec mẫu (DS) + UI Spec thật (docs), chạy lại cổng, cập nhật bảng trong mô tả MR.

---

## 6. Tham chiếu nhanh

| Cần | Ở đâu |
| --- | --- |
| SRS LSX | `sapo-accounting-docs/docs/enterprise/inventory/production-order/production-order.md` — §5.2 (AC), §6.2 (UI), §8.2.1 (API) |
| UI Spec LIST LSX | `sapo-accounting-docs/docs/enterprise/inventory/production-order/production-order.LIST.uispec.yaml` |
| Màn chi tiết mẫu enterprise | `sapo-accounting-frontend/apps/enterprise/src/pages/inventory/outward/sections/DetailPage/DetailPage.tsx` |
| Màn chi tiết LSX bản individual | `sapo-accounting-frontend/apps/individual/src/pages/inventory/production-orders/sections/DetailPage/` |
| Tham chiếu / đính kèm dùng chung | `useGetDocumentReferencesQuery` (`app/api`) + `DocumentReference readOnly` · `FilesList refId` (`app/components/FileUploader`) |
| Hướng dẫn thêm pattern | `design-system/packages/patterns/README.md` §Thêm pattern màn mới |
| Blueprint Figma cũ | `git show 3ab3d55^:packages/patterns/src/screen/detail-page.yaml` (repo DS) |

## Liên kết

- [[10_Projects/design-system/README]]
