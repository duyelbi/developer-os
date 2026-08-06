---
created: 2026-07-31
status: Active
scope: "Audit độ phủ @sapo-finance/components ↔ nhu cầu thật của sapo-invoice-admin-frontend; suy ra backlog DS + thứ tự migrate"
---

# Audit độ phủ DS ↔ Invoice

> Đo ngày 2026-07-31. DS: `/Users/sapo/Design-System/design-system/packages/components` (manifest `generatedAt: 2026-07-31T07:00`). Invoice: `/Users/sapo/invoice/sapo-invoice-admin-frontend`.
> Giả định đã chốt: **invoice sẽ dùng hoàn toàn DS**, và **invoice sẽ lên React 19**. DS chưa hoàn thiện — mục tiêu cuối là DS phủ hết nhu cầu invoice. Vì vậy phần "GAP" dưới đây đọc là **backlog của DS**, không phải lý do hoãn migrate.
> Liên quan: [[10_Projects/design-system/README]], [[10_Projects/sapo-invoice/migrate-ui-components-sang-design-system]], [[10_Projects/sapo-invoice/refactor-frontend-performance]]

## 1. Kết luận React 19 — không phải rào cản, và DS không phải chỗ rủi ro

Grep `packages/components/src/`:

| Kiểm tra | Kết quả |
|---|---|
| `use()`, `useActionState`, `useOptimistic`, `useFormStatus`, `useFormState` | **0** |
| `renderToPipeableStream`, `react-dom/client` | **0** |
| `defaultProps`, `propTypes` (bị gỡ ở React 19) | **0** |
| `forwardRef` | 90 (hợp lệ ở cả 18 và 19 — chỉ deprecated ở 19, không bị gỡ) |
| `ref?:` dạng ref-as-prop trong `types.ts` | 0 |

⇒ **`peerDependencies: react >=18` của DS là khai báo thật, không lỏng.** DS chạy được trên React 18.3 hôm nay, và cũng chạy được trên React 19. DS không ràng buộc thứ tự làm việc.

Rủi ro thật nằm ở **hai package legacy của Sapo**, không phải ở DS:

| Package | peer `react` | Pattern vỡ ở React 19 trong `dist` |
|---|---|---|
| `@sapo/ui-components@0.0.0-snapshot-20251222011441` | `^16.8.0 \|\| ^17.0.0 \|\| ^18.0.0` — **không khai 19** | `defaultProps` 0 · `propTypes` 0 · `findDOMNode` 0 · `ReactDOM.render` 0 · `createFactory` 0 · `unstable_` 0 |
| `@sapo/app-bridge-react@1.2.1` | `^16.14.0 \|\| ^17.0.0 \|\| ^18.0.0` — **không khai 19** | (cần kiểm tương tự) |
| `react-redux@9.2.0` | `^18.0 \|\| ^19` ✅ | — |

Tức là `@sapo/ui-components` **nhiều khả năng chạy được** trên React 19 — dist sạch hoàn toàn 6 pattern breaking phổ biến. Cái chặn chỉ là **dải peer khai báo**, xử lý được bằng `pnpm.peerDependencyRules.allowedVersions` mà không cần fork.

**Hệ quả cho thứ tự làm việc:** React 19 và migrate DS **không khoá nhau**. Ba đường đều mở:
- (a) Migrate DS trên React 18 trước, lên 19 sau khi gỡ hết `@sapo/ui-components` — sạch nhất, không cần override peer.
- (b) Lên React 19 trước bằng `peerDependencyRules`, migrate DS sau — nhanh hơn nhưng chạy `@sapo/ui-components` ngoài dải hỗ trợ khai báo, cần smoke test kỹ (đặc biệt 90 `forwardRef` + `react-transition-group` + `@floating-ui/react` bên trong nó).
- (c) Làm song song. Rủi ro cao nhất, không khuyến nghị.

Đề xuất **(a)**, vì khối lượng migrate DS lớn (xem §2) nên dù sao cũng cần nhiều sprint; lên React 19 ở cuối khi chỉ còn một thư viện UI thì gần như không rủi ro.

## 2. Bề mặt migrate: `@sapo/ui-components`

**473 file** import `@sapo/ui-components`, dùng **125 symbol** khác nhau. Phân loại theo trọng số = số file dùng symbol đó:

| Nhóm | Symbol | Trọng số | Nghĩa |
|---|---|---|---|
| **DIRECT** — DS đã có, đổi import + đổi tên prop nhẹ | 37 | 1.477 | Codemod được phần lớn |
| **RESHAPE** — DS có nhưng API khác chất | 4 | 246 | Phải sửa tay từng call site |
| **GAP** — DS chưa có | 35 | 681 | **Backlog DS** |
| **TYPE/UTIL** — type, props-interface, util | 49 | 227 | Theo component tương ứng |

### 2.1 DIRECT — map thẳng (làm được bằng codemod)

`Text`(232) · `Card`→`Card`+`Card.Section`(167, DS **có** compound Section) · `Button`(143) · `Link`(92) · `Box`(85) · `Icon`(71) · `TextField`(69) · `Badge`(64) · `InlineGrid`(60) · `Checkbox`(37) · `Banner`→**`AlertBanner`**(36) · `RadioButton`→**`Radio`**(33) · `Tooltip`(33) · `InlineStack`→**`Inline`**(31) · `BlockStack`→**`Stack`**(31) · `PageActions`(29) · `Popover`(28) · `FooterHelp`(25) · `Tabs`(23, `onDelete`→`onRemove`) · `Scrollable`→**`ScrollArea`**(22) · `Autocomplete`→**`Combobox`**(22) · `Select2`→**`Select`**(20) · `Spinner`(19) · `Tag`(12) · `Divider`(4) · `Backdrop`(4) · `Portal`(4, primitives) · `Avatar`(3) · `ToggleButton`(3) · `Toast`(2) · `DatePicker`→`Calendar`/`DateField`(2) · `TrapFocus`(2, primitives) · `Collapsible`(2) · `RangeSlider`(2) · `Pagination`(1) · `Select`(1) · `useBreakpoints`(63)

### 2.2 RESHAPE — DS có nhưng phải viết lại call site

| Symbol | Trọng số | Vấn đề |
|---|---|---|
| `Stack` | **139** | Ngữ nghĩa hướng khác nhau. Polaris-style `Stack` mặc định ngang + prop `vertical`; DS tách thành `Stack` (dọc) và `Inline` (ngang). **Không codemod mù được** — phải đọc từng call site xem có `vertical` không. Đây là symbol tốn công nhất trong toàn bộ migrate |
| `Modal` | **100** | `active`→`open`, kiểm tra compound `Modal.Section` |
| `EmptyState` + `EmptyStateProps` + `EmptySearchResult` | 10 | DS dùng **discriminated union prescriptive** (`type: "addOnly" \| "noData" \| "noResults" \| "withImport"` + `objectName`), không nhận `image`/`heading`/`children` tự do như invoice đang dùng. Phải map từng chỗ về đúng `type` |

### 2.3 GAP — backlog DS, xếp theo nhu cầu thật của invoice

Đây là danh sách DS cần build để invoice dùng được 100%. Xếp tier theo mức chặn:

**Tier 1 — không có thì không migrate trọn được một trang nào (weight 295)**

| Cần build | Trọng số | Ghi chú |
|---|---|---|
| `Loading` | **126** | Thanh loading top-of-page. DS có `Spinner`/`ProgressBar` nhưng không có cái này |
| `Page` | **74** | Page shell: title, primaryAction, secondaryActions, fullWidth, breadcrumb. DS mới chỉ có `PageActions` |
| `FormLayout` | **49** | Grid form. DS có `Box`/`Stack`/`InlineGrid` nhưng chưa có recipe form |
| `Layout` + `Layout.Section` | **46** | Bố cục 2 cột primary/secondary — `createTheme` của invoice đang cấu hình `layout.widthPrimary/widthSecondary` nên đây là recipe có sẵn convention |

**Tier 2 — chặn ~20 trang danh sách (weight 156)**

| Cần build | Trọng số | Ghi chú |
|---|---|---|
| **Table family**: `IndexTable`(40) + `useIndexResourceState`(49) + `SelectionType`(7) + `IndexTableHeading`(1) + `DataTable`(17) + `ColumnContentType`(5) | **119** | DS `AGENTS.md` đã ghi `data-patterns → Table` là *future*. Đây là hạng mục lớn nhất và cũng là thứ invoice cần nhất sau Tier 1 |
| **Filters family**: `AlphaFilters`(37) + `AlphaFilterInterface`(31) + `AlphaAppliedFilterInterface`(31) + `Filters`(1) | **37 (component)** | Bộ lọc + applied-filter chips. Đi liền với Table |

**Tier 3 — dùng nhiều nhưng thay tạm được (weight 133)**

`SkeletonPage`(46) · `SkeletonTabs`(23) — DS có `Skeleton.BodyText`/`Skeleton` base, thiếu recipe cấp trang · `List`(22) · `ContextualSaveBar`(16) — DS ghi *future* trong `page-shell` · `DropZone`(16) · `ChoiceList`(14) · `ButtonGroup`(12) — DS ghi *future* trong `action-patterns` · `Labelled`(12) — DS có `Label`, thiếu wrapper

**Tier 4 — lẻ (weight 26)**

`OptionList`(6) · `useEventListener`(6) · `ActionList`(5) · `Thumbnail`(1) · `TextContainer`(1) · `ColorPicker`(1) + 5 util màu (`rgbToHex`, `hexToRgb`, `hsbToHex`, `hsbToRgb`, `rgbToHsb`) + `RGBAColor`

**Tier 5 — KHÔNG phải việc code, là quyết định kiến trúc (weight 22)**

| Symbol | Trọng số | Mâu thuẫn cần giải |
|---|---|---|
| `Frame`(6) · `Navigation`(3) · `TopBar`(2) | 11 | `packages/components/AGENTS.md` hiện ghi rõ: *"Templates (Topbar, Navigation trong Figma): **không** nhét vào `base`/`composite` export — giữ Playroom/docs hoặc RFC riêng."* Điều này **mâu thuẫn trực tiếp** với mục tiêu "DS cover hết nhu cầu invoice" |
| `AppProvider`(2) · `createTheme`(2) · `useTheme`(6) · `Theme`(1) | 11 | DS dùng CSS vars từ `@sapo-finance/tokens` thay cho theme object runtime. Invoice đang cấu hình theme runtime (`main.tsx`: `layout.widthPrimary`, `navigation.baseWidth`, `popover.maxHeight`). Cần chốt: DS có API theming runtime không, hay invoice bỏ hẳn và chuyển sang override CSS vars |

**Đây là hai câu hỏi cần trả lời sớm nhất** — sớm hơn cả việc build Table, vì chúng quyết định *ranh giới* của DS chứ không chỉ nội dung. Nếu DS không nhận app shell thì invoice giữ shell riêng, và "dùng hoàn toàn DS" nghĩa là "dùng DS cho mọi thứ bên trong shell" — vẫn hợp lý, nhưng phải nói rõ để không ai kỳ vọng sai.

## 3. Component nội bộ của invoice (`src/components/`, 78 mục, 16.536 LOC)

| Nhóm | Số component | LOC | Tỉ lệ |
|---|---|---|---|
| **Xoá — DS đã có** | 30 | 9.019 | 55% |
| **Promote lên DS** | 16 | 3.558 | 22% |
| **Giữ ở app** | 32 | 3.959 | 24% |

Chỉ **8/78** component có gọi API và **6/78** chạm router ⇒ ~90% là UI thuần, promote được về nguyên tắc.

### 3.1 Xoá, dùng DS (9.019 LOC — hơn một nửa thư mục)

`DateTimeField`(2.814) + `DateTime`(601) → DS `DateField`/`DateTimePicker`/`DateRangePicker`/`Calendar`/`TimeField`/`TimePicker` · `TextField2`(979) → `TextField` · `NumberField`(929) + `MoneyField`(237) → `NumberField` · `Modal2`(637) + `Sheet2`(157) → `Modal` + `SlideOut` · `SearchSelect`(428) + `AutocompleteSelectField`(315) + `AutocompleteCustom`(259) + `AutocompleteSelect`(254) + `AutocompleteField`(32) → `Combobox` · `EmailTagsInput`(254) → `TagsField` · `Pagination`(137) → `Pagination` · `TruncatedText`(101) + `TruncatedText2`(63) → `TruncatedText` · `IndexEmptyState`(96) + `EmptySearchResult`(53) + `SelectEmptyState`(16) → `EmptyState` · `ConfirmModal`(85) → `Modal` recipe · các field wrapper nhỏ (`InputField`, `InputField2`, `SelectField`, `PasswordField`, `PlainButton`, `Banner2`, `ButtonPopover`, `SelectPopover`, `LoadingState`, `PageLoading`)

> Riêng cụm select/autocomplete: invoice hiện có **5 biến thể song song** cho cùng một nhu cầu. Gộp về `Combobox` của DS là chỗ giảm nợ kỹ thuật rõ nhất.

### 3.2 Promote lên DS (3.558 LOC) — trùng khớp với GAP ở §2.3

| Component invoice | LOC | Vào DS như |
|---|---|---|
| `Virtual/core.ts` | 1.113 | **hook** `useVirtualList` (không phải component) — đi kèm Table Tier 2 |
| `DragDropImages` | 588 | `DropZone` (Tier 3) |
| `SettingColumn` | 449 | composite `ColumnSettings` — đi kèm Table |
| `Timeline` | 227 | base `Timeline` |
| `RgbColorPicker`(222) + `PopoverColorPicker`(154) | 376 | `ColorPicker` (Tier 4) |
| `ImportFileDropzone` | 165 | gộp vào `DropZone` |
| `AppSkeleton`(133) + `SkeletonTable`(128) | 261 | `Skeleton` recipes (Tier 3) |
| `IndexTableField`(118) + `IndexTableCell`(54) + `ListTable` | 172 | Table family (Tier 2) |
| `NoImageThumbnail`(9) | 9 | `Thumbnail` (Tier 4) |
| `RadioTag`, `InlineWarning`, `StopPropagation` | ~198 | cân nhắc từng cái |

**Tín hiệu tốt:** danh sách promote này được suy ra độc lập với danh sách GAP ở §2.3 nhưng trùng nhau gần hết (Table, DropZone, ColorPicker, Skeleton recipe, Thumbnail). Hai nguồn nhu cầu độc lập cùng chỉ vào một chỗ ⇒ backlog DS đang được xác nhận chéo, không phải suy đoán.

### 3.3 Giữ ở app (3.959 LOC)

Gắn nghiệp vụ hoặc gắn hạ tầng app: `ErrorBoundary`(461 — dùng DS `FailureState` để render, giữ phần Sentry ở app) · `RemoteSigningModal`(330) · `DashboardChart`(200) + `InvoiceChart`(162) (Highcharts) · `Navigate`/`Navigate2`/`Link`/`leave-page`/`AppLayout`/`RouterTitle`/`DocumentTitle` (gắn react-router) · `PopupSaveSearch`/`PopupSavedSearch` (nghiệp vụ saved search) · `NghiDinh254Modal`, `UsbTokenFailModal`, `MaintenanceModal`, `DashboardPopup`, `VideoModal`, `NotiModal`, `ActionSuccessModal` (modal nghiệp vụ, dựng trên DS `Modal`) · `BlockedAccount` · `WardSelect`/`WardSelect2`/`WardSelectTwoTier`/`ProvinceSelect`/`ProvinceSelect2`/`DistrictSelect` (656 LOC — **gọi API bên trong**; nên tách thành DS `Combobox` + hook data ở app, xem P1.2 trong plan refactor)

## 4. Thứ tự đề xuất

1. **Chốt Tier 5 trước hết** (app shell + theming). Là quyết định policy, tốn vài ngày thảo luận, nhưng chặn mọi thứ phía sau. Nếu DS nhận app shell → cập nhật `packages/components/AGENTS.md` vì rule hiện tại đang loại trừ.
2. **DS build Tier 1** (`Loading`, `Page`, `FormLayout`, `Layout`). 4 component này mở khoá việc migrate trọn vẹn trang đầu tiên.
3. **Invoice dọn nội bộ song song** — §3.1, xoá 9.019 LOC. Không phụ thuộc Tier nào của DS ngoài những component DS đã có sẵn. Bắt đầu ngay được, và giảm bề mặt migrate trước khi đụng vào phần khó.
4. **Migrate trang đầu tiên trọn vẹn** làm mẫu. Chọn trang đơn giản, ít bảng — đề xuất một trang trong `setting/pages/` (`decimal-configuration` hoặc `tax-category`). Rút ra codemod + checklist.
5. **DS build Tier 2** (Table + Filters + `useVirtualList` + `ColumnSettings`) — hạng mục lớn nhất, nên bắt đầu thiết kế `SPEC.md` song song với bước 2 vì lead time dài.
6. **Migrate loạt 20 trang danh sách** sau khi Tier 2 xong.
7. **Tier 3/4** cuốn chiếu theo trang.
8. **Nâng React 19** khi `@sapo/ui-components` đã bị gỡ khỏi `package.json`.

## 5. Điểm cần lưu ý khi thực thi

- **`Stack` (139 file) là điểm tốn công nhất**, không phải Table. Vì nó không codemod mù được (phải đọc `vertical` prop từng chỗ) mà lại rải khắp repo. Nên viết codemod bán tự động: tự đổi khi có/không `vertical` rõ ràng, đánh dấu `// TODO-DS-REVIEW` khi prop truyền động.
- **Giai đoạn chuyển tiếp chạy 2 runtime CSS-in-JS** (emotion + styled-components). Chấp nhận được nếu có deadline; ADR hiện ghi "chưa có timeline" — nên chốt.
- **DS đang 55/55 component ở `status: draft`.** Cần biết "draft" nghĩa là gì với consumer (API có thể đổi không?) trước khi invoice cam kết 473 file vào nó.
- Audit này đo bề mặt **import**, chưa đo **độ lệch hành vi**. Với 3 component trọng số cao nhất (`Text` 232, `Card` 167, `Button` 143) nên diff prop-level chi tiết trước khi viết codemod — sai ở đây thì sai trên hàng trăm file.
