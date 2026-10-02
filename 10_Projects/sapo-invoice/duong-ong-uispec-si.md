---
created: 2026-08-20 15:00
status: Draft
project: "[[10_Projects/sapo-invoice/README]]"
---

# Đường ống UI Spec cho SI — chuyển thư viện UI cũ sang DS, thu hoạch spec trên đường đi

Ghi nhớ bước điều tra + kế hoạch. **Vault này là bộ nhớ cá nhân của giai đoạn nghiên cứu**; khi làm task chính thức thì template/skill/rule/cổng CI đặt ở `invoice-docs`.

Mục tiêu công việc: dựng MCP + skill phục vụ chuyển `@sapo/ui-components` → `@sapo-finance/components`, nhằm đồng nhất **UI và spec** giữa các repo, SI trước. DS hiện xây chủ yếu cho SA (`sapo-accounting`) ⇒ phải đo SI tái dùng được gì, bổ sung gì.

Liên quan: [[10_Projects/design-system/README]] · [[10_Projects/design-system/audit-coverage-invoice]] · [[10_Projects/sapo-invoice/migrate-ui-components-sang-design-system]] · [[10_Projects/sapo-invoice/ai/rules-frontend]]

## 1. Kết luận ngắn

1. **Độ phủ đổi hẳn so với audit 31-07.** Đo lại trên manifest 17-08 (DS 55 → 67 component): **81% bề mặt import của SI đã có chỗ trong DS**. Khoảng trống 681 → **375** điểm trọng số, giảm 45%.
2. **78% chỗ trống còn lại nằm ở 4 symbol khung trang — và 3/4 không phải component.** `Page`(75), `FormLayout`(50), `Layout`(45) là *công thức* DS đã có dưới dạng pattern, chỉ đang khai `apps: [sapo-accounting]`. **Đã kiểm 21-08: `Loading`(124) cũng không phải việc của DS** — nó render `null`, và SI đã tự viết lại toàn bộ cơ chế (xem §5). Component DS thật sự còn thiếu chỉ còn 56 điểm, toàn thứ nhỏ.
3. **Khung trang chặn tất cả:** 21/24 module SI chạm `Page`, 13/24 chạm `Loading`. Chưa chốt cách dựng khung trang thì không trang nào migrate trọn vẹn được.
4. **Vốn từ spec tái dùng nhiều hơn tưởng:** 18/19 ngữ nghĩa trung lập dùng ngay; ~15 pattern của SA là generic, chỉ cần thêm bằng chứng SI. Phải xây mới chủ yếu là **flow riêng hóa đơn** (hiện SI có **0 flow riêng**).
5. **Đề xuất mới duy nhất:** bảng ánh xạ thư viện cũ → DS (`legacy-map.yaml`) đặt ở repo DS, phục vụ qua tool MCP `get_legacy_map`. SA cũng đang migrate — để bảng ở từng app là nhân đôi công và nhân đôi sai.

## 2. Đo lại độ phủ (20-08-2026)

Quét `sapo-invoice-admin-frontend/src` nhánh `master`, đối chiếu `manifest.json` sinh 17-08.

| Chỉ số | Giá trị |
|---|--:|
| File `.ts/.tsx` trong `src/` | 951 |
| File chạm `@sapo/ui-components` | 471 |
| Symbol khác nhau | 124 |
| Tổng trọng số (symbol × file) | 2.607 |

| Nhóm | Symbol | Trọng số | Tỉ lệ |
|---|--:|--:|--:|
| DIRECT — đổi import, prop lệch nhẹ | 44 | 1.529 | 58% |
| RESHAPE — DS có nhưng khác chất | 21 | 606 | 23% |
| GAP — chưa có đường đi | 23 | 375 | 14% |
| TYPE/UTIL | 35 | 97 | 3% |

### Ba tuần qua DS đóng được gì

| Symbol cũ | Trọng số | 31-07 | Hôm nay |
|---|--:|---|---|
| `IndexTable`/`DataTable`/`useIndexResourceState`/`SelectionType`… | 168 | GAP Tier 2 | `DataGrid` — RESHAPE |
| `AlphaFilters` + 3 interface | 100 | GAP Tier 2 | `Filters`/`FilterPanel` — RESHAPE |
| `DropZone` | 15 | GAP Tier 3 | `Dropzone` — DIRECT |
| `ContextualSaveBar` | 16 | GAP Tier 3 | Có — DIRECT |
| `ButtonGroup`/`ActionList`/`OptionList` | 21 | GAP Tier 3/4 | Có — DIRECT |
| `SettingColumn` (component nội bộ SI) | — | đề xuất promote | Đã có trong DS |

⇒ **Bảng dữ liệu không còn là đường găng. Đường găng là khung trang.**

## 3. Tái sử dụng được gì từ DS xây cho SA

### Component — 81% dùng lại được

Không component nào của DS bị khoá theo nghiệp vụ kế toán. Phần RESHAPE tốn công vì DS chọn ngữ nghĩa khác thư viện cũ:

| Symbol | Trọng số | Lệch ở đâu |
|---|--:|---|
| `Stack` | 134 | Thư viện cũ mặc định *ngang* + prop `vertical`; DS tách `Stack` (dọc) / `Inline` (ngang). Không codemod mù được — **tốn công nhất toàn bộ migrate** |
| `Modal` | 100 | `active` → `open`, kiểm compound `Modal.Section` |
| bộ bảng → `DataGrid` | 168 | Chọn dòng + phân trang gộp vào lưới; bỏ `useIndexResourceState` |
| bộ lọc → `Filters` | 100 | Applied-filter chips đổi hình dạng interface |
| `EmptyState` họ | 10 | DS dùng union quy định sẵn (`SystemState`) |
| `Skeleton*` họ | 94 | DS có base; công thức cấp trang nằm ở pattern `page-skeleton` |

### Pattern — phân loại theo việc phải làm

| Nhóm | Gồm | Việc |
|---|---|---|
| **Dùng ngay** | 18 ngữ nghĩa trung lập · `list-page` · `filter-bar` · `overlay-form` · `settings-page` · `dashboard-page` · `confirm-modal` · `bulk-action-bar` · `column-setting` · `footer-help` · 6 flow chung | Không có |
| **Nhận bằng chứng SI** | `detail-page` · `form-page` · `report-page` · `wizard-page` · `page-skeleton` · `form-section` · `line-items` · `summary-strip` · `detail-summary` · `related-list` · `drill-down` · `import-modal` · `export-modal` · `async-job-toast` · `period-filter` · flow `import`/`export`/`duplicate` | Thêm `sapo-invoice` vào `apps` + dòng `seenIn` thật. Đã kiểm `form-page`: PageHeader + thanh lưu + nhóm trường, không dính kế toán |
| **Xây mới cho SI** | flow: phát hành · cấp mã CQT · thay thế · điều chỉnh · hủy · gửi người mua · xử lý thông điệp CQT. semantic: `taxCode` · `invoiceSeries` · `invoiceNo` · `vatRate` · `taxAuthorityCode` | `pattern-mine` trên `src/pages` rồi MR sang DS |
| **Không áp dụng** | `post-voucher` · `unpost-voucher` · `closing-date-guard` · `auto-post` · `derive-voucher` · `settlement` · `sequence-duplicate` · semantic `refNo` | Bỏ qua |

`vatRate` đáng nói riêng: `vat_name` nhận cả `10%` lẫn `KCT`/`KKKNT` ⇒ không phải `percent`, cũng không phải `enum` thuần.

## 4. Cần bổ sung gì vào DS

| Symbol | Trọng số | Bản chất | Đề xuất |
|---|--:|---|---|
| `Loading` | 124 | **SI tự lo** — đã kiểm 21-08 | Component này **render `null`**: nó chỉ gọi `useFrame().startLoading()` khi mount. Thanh tiến trình do `Frame` vẽ. SI đã tự viết lại đủ bộ ở `pages/setting/components/SettingLayout/` (xem §5) |
| `Page` | 75 | Đã có công thức | `PageHeader` cover title · backAction · actions · collapsedActions · info · pagination; phần bọc ngoài do `Container` + skeleton của screen pattern lo |
| `FormLayout` | 50 | Đã có công thức | `form-section` (PAT-BLK-010) + `Stack`/`InlineGrid` |
| `Layout` + `Layout.Section` | 45 | Đã có công thức | `Container` · `GridResponsive` · `InlineGrid`; cần một recipe hai cột được viết ra |
| `List` · `ChoiceList` · `Labelled` · `TextContainer` | 49 | Thiếu thật | Nhỏ, làm sau |
| `ColorPicker` + 5 util màu | 8 | Thiếu thật | SI có sẵn 376 LOC — promote lên DS thay vì build lại |
| `Frame`/`Navigation`/`TopBar`/`AppProvider`/`createTheme`/`useTheme` | 21 | **Quyết định, không phải code** | `packages/components/AGENTS.md` đang **loại trừ** app shell khỏi export — mâu thuẫn với mục tiêu "DS phủ hết nhu cầu SI" |

### Khung trang chặn 21/24 module (đo được)

Chỉ `auth`, `oauth`, `dashboard` là sạch hoặc gần sạch. Ứng viên trang mẫu, bề mặt nhỏ nhất:

| Trang | File chạm | Symbol | Còn vướng |
|---|--:|--:|---|
| `setting/pages/email-invoice` | 1 | 6 | `FormLayout`, `Page` |
| `setting/pages/decimal-configuration` | 1 | 10 | `FormLayout`, `Page` |
| `setting/pages/import-export-history` | 5 | 18 | `Loading`, `Page` |
| `setting/pages/tax-category` | 12 | 15 | `Loading`, `Page` |

Cả bốn chỉ vướng đúng họ khung trang ⇒ chốt xong mục 4 là có ngay trang làm mẫu.

> **"Màn mới hoặc viết lại trọn vẹn" nghĩa là gì:** một trang phải chuyển **hết trong một lần**, không đổi lẻ vài component rồi để đó. Trộn hai thư viện trong cùng một trang = trộn hai hệ token, hai runtime CSS-in-JS (emotion + styled-components) và hai ngữ nghĩa `Stack`.

## 5. Kiểm chứng `Loading` (21-08-2026) — không phải khoảng trống của DS

Giả thuyết ban đầu: `Loading`(124) là component duy nhất DS phải build gấp. **Sai.** Bốn bằng chứng:

**(1) `Loading` của thư viện cũ render `null`.** Nguyên văn `node_modules/@sapo/ui-components/dist/esm/components/Loading/Loading.js`:

```js
const Loading = memo(function Loading() {
  const { startLoading, stopLoading } = useFrame();
  useEffect(() => { startLoading(); return () => { stopLoading(); }; }, [startLoading, stopLoading]);
  return null;
});
```

Nó là **tín hiệu**, không phải giao diện. Thanh tiến trình do `Frame` vẽ. Vì vậy 124 file kia không dùng 124 chỗ giao diện — chúng chỉ báo "đang bận" cho shell.

**(2) SI đã tự viết lại đủ bộ, đang chạy thật.** `pages/setting/components/SettingLayout/`:

| File | Vai trò |
|---|---|
| `SettingFrame.tsx` | Context riêng: `loadingStack`, `startLoading`, `stopLoading`, `setContextualSaveBar`; render `<StyledLoadingBar><SettingLoading/></StyledLoadingBar>` khi `loadingStack > 0` |
| `SettingLoading.tsx` | Thanh tiến trình ~40 dòng, `role="progressbar"`, tự animate qua `requestAnimationFrame` |
| `components/SettingLoading.tsx` | Bản tín hiệu y hệt `Loading` của lib: `startLoading()`/`stopLoading()` rồi `return null` |

14 file đang dùng bản tự viết này. Tức SI đã copy đúng kiến trúc của lib — 1 tín hiệu + 1 frame giữ stack + 1 thanh — và nó hoạt động.

**(3) `<Frame>` chỉ render ở 5 chỗ:** `App.tsx:319` (gốc, chỉ bọc providers), `AdminFrame.tsx:55`, `LookupPage.tsx:85`, `AuthorizationTenantPage.tsx:38`, `PackagePriceListPage.tsx:28`. Thay không phải rewrite.

**(4) Chỗ duy nhất còn vướng DS là token:** `StyledLoading` dùng `p.theme.colors.actionPrimary`, `p.theme.spacing(1)`, `p.theme.motion.duration500` — theme runtime của lib cũ. Đổi sang CSS vars của `@sapo-finance/tokens` là 3 token.

### Việc thật phải làm

| Việc | Quy mô |
|---|---|
| Nâng cơ chế `SettingFrame` lên cấp app (`AppFrame` + `AppLoading`) | ~60 LOC đã tồn tại, chỉ move + generalize |
| Thay 5 chỗ `<Frame>` của lib | 5 file |
| Đổi 124 import `Loading` → `app/components/AppLoading` | Codemod thuần, không đọc từng call site |
| Đổi 3 token trong `StyledLoading` sang CSS vars | 1 file |

### Hệ quả dây chuyền

- GAP "DS phải build" tụt từ **180 → 56** điểm: chỉ còn `List`(22) · `ChoiceList`(14) · `Labelled`(12) · `ColorPicker`+util(8). Toàn thứ nhỏ, làm sau được.
- **Câu hỏi app shell biến mất.** `Frame`+`Navigation`+`TopBar` = 10 điểm, và SI đã tự dựng frame 2 lần. SI **nên** giữ shell — đúng thứ `packages/components/AGENTS.md:55` của DS muốn. Chuyển từ "câu hỏi cho DS" thành "ADR của SI".
- **Câu hỏi theming cũng tự trả lời được** (xem §9).
- Còn phải làm việc với DS thật sự chỉ hai thứ, cả hai đều nhẹ: nhận MR mở `apps` cho 4 pattern, và trả lời `draft` nghĩa gì với consumer.

**Kết luận: SI không bị chặn. Bắt đầu được ngay.**

## 6. MCP + skill phục vụ chuyển đổi

Nguyên tắc: **mỗi lần migrate một trang là một lần sinh ra bằng chứng và spec.** Không thu hoạch thì chỉ đổi được import và mất cơ hội đồng nhất spec.

### 6.1 Thêm vào MCP: `legacy-map`

Bảng "symbol cũ → component DS + prop đổi tên + bẫy" là **dữ liệu**, không phải văn xuôi trong skill. Đặt ở `design-system/packages/patterns/src/foundation/legacy-map.yaml`, phục vụ qua tool mới `get_legacy_map` của `sapo-ds`.

```yaml
- from: Stack
  to: { component: Stack, alt: Inline }
  kind: reshape
  rule: "có prop `vertical` → Stack; không có → Inline"
  danger: "prop truyền động thì KHÔNG tự đổi — đánh dấu TODO-DS-REVIEW"
  weight: { sapo-invoice: 134 }

- from: Banner
  to: { component: AlertBanner }
  kind: direct
  props: { status: tone }

- from: IndexTable
  to: { component: DataGrid }
  kind: reshape
  note: "chọn dòng + phân trang gộp vào lưới; bỏ useIndexResourceState"
  seeAlso: [PAT-SCR-001]
```

Lý do đặt ở DS: SA cũng đang migrate — đo được ở `line-items`, enterprise còn 69 file thư viện cũ, individual đã sang `DataGrid` 75 file.

### 6.2 Skill `ds-migrate-screen` (repo SI)

Đầu vào là **một trang**, không phải một component.

| Bước | Làm gì | Dừng khi |
|--:|---|---|
| 1 | Liệt kê symbol cũ của trang; tra `get_legacy_map` từng cái | — |
| 2 | Còn symbol `kind: gap` → **dừng**, ghi `foundation/ds-debt.yaml`, báo cần DS bổ sung gì | Luôn dừng. Migrate nửa trang là nợ, không phải tiến độ |
| 3 | `get_usage` từng component đích — import, prop **có thật**, mục `dont` | Prop không có trong kết quả là prop không tồn tại. Không grep source DS |
| 4 | `get_pattern` khung màn; dựng lại trang theo `skeleton` thay vì bê nguyên bố cục cũ | Đây là chỗ biến "đổi import" thành "đồng nhất UI" |
| 5 | Viết khối `yaml uispec` cho trang **từ code vừa dựng**; `validate_spec` tới khi sạch | Spec sinh ra như sản phẩm phụ của migrate |
| 6 | Thu hoạch `seenIn` cho pattern đã dùng → MR sang DS | Đủ 3 dòng ⇒ pattern lên `stable` ⇒ `validate_spec` bắt đầu **chặn** |
| 7 | Cổng: `pnpm lint:fix && pnpm format` · đủ 5 state · đối chiếu `checklist` | Không thỏa thì nói thẳng |

**Vòng lặp tự siết:** migrate → `seenIn` → `stable` → validator chặn → trang sau bị ép đi đúng khung. Hôm nay toàn bộ 59 pattern + 67 component đều `draft` nên chưa chặn được ai; chính việc migrate là nguồn bằng chứng duy nhất để thoát trạng thái đó.

### 6.3 Nối dây

```json
{
  "mcpServers": {
    "sapo-ds": { "type": "stdio", "command": "npx", "args": ["-y", "@sapo-finance/mcp"] }
  }
}
```

Đặt ở `sapo-invoice-admin-frontend/.mcp.json` và `invoice-docs/.mcp.json`. Ở repo frontend `cwd` có ý nghĩa: MCP resolve `@sapo-finance/components` theo cwd trước khi rơi xuống snapshot ⇒ manifest khớp version app đang code. Cần `.npmrc` trỏ scope `@sapo-finance` sang GitLab registry (`git.dktsoft.com:2008/api/v4/projects/3656/packages/npm/`). **Đừng** khai `SAPO_DS_MANIFEST`/`SAPO_DS_PATTERNS`.

> Bẫy: server đọc manifest/patterns **một lần mỗi process**. Regen xong phải restart `sapo-ds`, không thì agent kiểm bằng vốn từ cũ mà không báo lỗi.

## 7. Spec: UI Spec và template SRS

`sapo-ds` đã phục vụ sẵn hợp đồng UI Spec: một schema zod dùng chung cho `validate_spec`, resource `ds://spec-schema` và khối YAML mẫu ⇒ không lệch nhau được. Kèm hai prompt `author_uispec` (BA) và `implement_uispec` (dev) — đặt ở MCP vì BA làm ở repo docs, dev ở repo frontend, không repo nào đọc được skill của repo kia.

Ba chỗ template `invoice-docs/_template/srs-uc.md` chưa đỡ được khối máy đọc:

| Cần thêm | Vì sao |
|---|---|
| **Mục Domain Model** — bảng thực thể có cột *ngữ nghĩa · bắt buộc · tập giá trị · công thức · trỏ tới* | Nguồn của `fields[]`. Không có bảng thì khối YAML bị bịa từ văn xuôi. `srs-domain.md` đã có sẵn mục này |
| **Mục UI Spec** — bảng đăng ký màn + mỗi màn một khối ` ```yaml uispec ` | §6 hiện là bảng văn xuôi. Có khối máy đọc thì validate = đọc file → parse → gọi tool; không có thì phải nhờ LLM trích, và bước trích đó là chỗ sai lệch âm thầm |
| **Bảng mã lỗi** + **bảng API** | `guards[].error` trỏ mã, `params.api` trỏ mã API |

Va chạm số mục: hợp đồng DS ghi "§7"/"§5" theo template của SA; `srs-uc.md` của SI có §5 = User Stories, §7 = Tuân thủ. **Neo vào thẻ khối `yaml uispec` + tên mục**, rồi MR nhỏ sang DS sửa cách gọi tên.

## 8. Lộ trình

| GĐ | Làm gì | Xong khi |
|---|---|---|
| 0 · Nối dây | Hai `.mcp.json` + `.npmrc`; cài `@sapo-finance/components` vào SI | Gọi được `get_pattern`/`get_usage` từ cả hai repo |
| 1 · **Nâng shell của SI lên cấp app** | Không còn chờ DS. Đưa cơ chế `SettingFrame` (loadingStack + thanh tiến trình) lên app; thay 5 chỗ `<Frame>`; đổi 124 import `Loading` sang bản của app; ghi ADR "shell thuộc SI" | Một trang `setting/pages/*` dựng lại hoàn toàn bằng DS, không còn import thư viện cũ |
| 2 · Bảng ánh xạ + skill | `legacy-map.yaml` + `get_legacy_map`; skill `ds-migrate-screen`; migrate `email-invoice` hoặc `decimal-configuration` | Trang mẫu qua đủ 7 bước, có khối `uispec` validate sạch |
| 3 · Thu hoạch vốn từ | Mỗi trang cấp `seenIn`; `pattern-mine` đãi flow riêng SI + 5 ngữ nghĩa | Pattern đủ 3 bằng chứng lên `stable` |
| 4 · Template SRS | Sửa template ở `invoice-docs`; skill viết UI Spec; rule nạp theo path | Một SRS thật có khối `uispec` validate 0 error |
| 5 · Nhân rộng | Cuốn chiếu `setting` → `report` → danh sách hóa đơn; CLI `sapo-mcp validate` cho cổng CI | `@sapo/ui-components` rời `package.json` |

Chạy song song, không chặn ai: **dọn component nội bộ SI** — audit 31-07 đo 9.019 LOC trong `src/components/` là thứ DS đã có (riêng cụm select/autocomplete có 5 biến thể song song).

## 9. Quyết định cần chốt

| Câu hỏi | Khuyến nghị | Nếu chọn khác |
|---|---|---|
| DS có nhận app shell? | **Không cần hỏi nữa.** SI tự giữ shell — đã dựng frame riêng 2 lần (`SettingFrame`, `AdminFrame`), đúng thứ `AGENTS.md` của DS muốn. Chỉ cần ghi thành ADR | Đi hỏi rồi chờ ⇒ mất vài sprint cho thứ SI đã có |
| Khung trang: DS build `Page`/`FormLayout`/`Layout` hay SI đổi sang `PageHeader` + pattern? | Đi theo pattern — DS đã cố ý phân rã như vậy | Xin DS build ⇒ chậm hơn và SA sẽ không dùng |
| Theming runtime hay CSS vars? | **Tự trả lời được.** `createTheme` chỉ cấu hình cho component của lib cũ (`layout.widthPrimary` → `Layout`, `navigation.baseWidth` → `Navigation`, `popover.maxHeight` → `Popover`) — bỏ lib là bỏ luôn. Phần theme SI thật sự cần cho code của mình (vd `StyledLoading` dùng 3 token) chuyển sang CSS vars của `@sapo-finance/tokens` | Hai hệ token cùng chạy suốt giai đoạn chuyển tiếp |
| Ai làm chủ `legacy-map`? | Repo DS | Mỗi app một bảng ⇒ hai cách đổi `Stack` |
| `draft` nghĩa gì với consumer? | Trả lời trước khi SI cam kết 471 file: API còn đổi không, đổi thì báo qua đâu | Migrate xong một đợt rồi DS đổi prop, không có đường biết |
| Ai sở hữu pattern riêng SI? | Repo DS, MR do người SI mở | Hai vốn từ, `validate_spec` mất nghĩa |

## Nguồn đo

Quét `sapo-invoice-admin-frontend/src` (951 file, `master` 20-08) đối chiếu `@sapo-finance/components/manifest.json` (67 component, sinh 17-08) và `@sapo-finance/patterns/patterns.json` (59 pattern) · `design-system/packages/mcp` · `invoice-docs/_template/{srs-uc,srs-domain}.md` · `sapo-invoice-admin-frontend/.claude/commands/review-code.md`. Số LOC component nội bộ và phân tích Tier lấy từ [[10_Projects/design-system/audit-coverage-invoice]].

**Chưa kiểm chứng:** template SRS của `sapo-accounting-docs` không có trên máy, không tìm thấy qua GitLab search. Phân loại DIRECT/RESHAPE đo ở mức *bề mặt import*, chưa đo lệch hành vi từng prop — với `Text`(232), `Card`(165), `Button`(142) nên diff prop-level trước khi viết codemod.
