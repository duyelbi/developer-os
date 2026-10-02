---
created: 2026-09-30 10:00
status: Chưa chạy — phiên 1 (BE) rồi phiên 2 (FE), Figma đã có
project: "[[10_Projects/sapo-invoice/README]]"
---

# Prompt Cursor — implement Epic #102 (phí giao hàng theo nguồn đơn, V2)

Plan: [[epic-102-plan]] · Test case: [[epic-102-test-cases]]

Chia **2 phiên**. Copy phần trong khung và dán vào Cursor (mở workspace `/Users/sapo/invoice`).
- **Phiên 1 — BE** (`sapo-einvoice-service`): chạy ngay.
- **Phiên 2 — FE** (`sapo-frontend-v3`): chạy sau khi phiên 1 merge/đã có contract BE. Figma đã có (node `979:50171`).

---

## Phiên 1 — BE

````markdown
# Task: Epic #102 — BE: chỉ dựng dòng phí giao hàng cho nguồn đơn được chọn (V2)

Repo: `/Users/sapo/invoice/sapo-einvoice-service` (Java 11 / Spring Boot 2.1, Maven, SQL Server).
Nhánh: tạo từ `master`, tên `dev-money/feature/shipping-fee-by-source-SM-0`.

## Đọc trước
1. `/Users/sapo/invoice/AGENTS.md`, `sapo-einvoice-service/CLAUDE.md` (coding rules: BigDecimal HALF_UP, lowercase enum, import thay vì FQN, constructor injection).
2. `/Users/sapo/developer-os/10_Projects/sapo-invoice/ai/rules-backend.md`
3. Plan: `/Users/sapo/developer-os/10_Projects/sapo-invoice/epic-102-phi-giao-hang-theo-nguon-don-v2/epic-102-plan.md` (đọc mục "Quyết định đã chốt" và "Thiết kế V2").
4. Test case: `.../epic-102-test-cases.md` nhóm **U**.

## Quyết định đã chốt — KHÔNG tự đổi
- Thêm field `order_source_ids` (List<String>, là **id** nguồn đơn dạng chuỗi) vào JSON setting `shipping_fee_setting`. **Không** thêm setting key mới, **không** migration DB.
- `order_source_ids == null` (thiếu field) = store chưa từng lưu → áp **mọi** nguồn, kể cả order `sourceId == null`.
- Có list → chỉ dựng dòng phí khi `String.valueOf(order.sourceId)` thuộc list; `sourceId == null` → **không** dựng.
- `separate_line` + list rỗng → chặn lưu, message chính xác: `Nguồn đơn không được để trống`.
- **Không** lọc theo status nguồn khi so khớp (nguồn ngừng áp dụng vẫn khớp).
- Không đổi công thức dòng phí, `item_name`, marker `shipping_line`, logic HĐ điều chỉnh (`EInvoiceServiceImpl` ~1689), logic đổi provider.

## Việc cần làm

### 1. Model — `src/main/java/vn/sapo/services/domain/sapoinvoice/SapoInvoiceSetting.java` (~88, class `ShippingFeeSetting`)
Thêm:
```java
/** Id nguồn đơn áp dụng dòng phí; null = store chưa từng lưu → áp mọi nguồn đơn. */
@JsonProperty("order_source_ids")
private List<String> orderSourceIds;
```

### 2. `src/main/java/vn/sapo/services/service/publisher/sapoinvoice/SapoInvoiceSettingUtil.java`
- `normalizeParsed`: **không** gán list rỗng khi `orderSourceIds == null` — giữ `null`.
- `defaultShippingFeeSetting()`: để `orderSourceIds = null` (không set gì).
- `normalizeShippingFeeSettings`: ngoài trim `itemName`, nếu `orderSourceIds != null` → trim từng phần tử, bỏ blank, distinct giữ thứ tự (`StringUtils::trimToNull` + `Objects::nonNull` + `distinct()` + `Collectors.toList()` — Java 11, **không** dùng `.toList()`).
- `validateShippingFeeSettings`: sau đoạn validate `itemName` (trong nhánh `separate_line`), thêm:
  ```java
  List<String> sourceIds = fee.getOrderSourceIds();
  if (sourceIds != null && sourceIds.stream().allMatch(StringUtils::isBlank)) {
      throw new SapoInvoiceExeption("setting", "Nguồn đơn không được để trống");
  }
  ```
  (`allMatch` trên list rỗng = true → bắt cả `[]` và `[" ", ""]`.)

### 3. `src/main/java/vn/sapo/services/service/publisher/sapoinvoice/SapoInvoiceService.java`
- DTO `ShippingFeeSettings` (~2305): thêm field `private final List<String> orderSourceIds;` và method:
  ```java
  /**
   * BR2 (epic 102): list null = store chưa từng lưu nguồn đơn → áp mọi nguồn (kể cả order không nguồn);
   * có list → order phải có source_id thuộc list. Không lọc theo status nguồn (BR5).
   */
  public boolean appliesToOrderSource(Long sourceId) {
      if (orderSourceIds == null) {
          return true;
      }
      if (sourceId == null) {
          return false;
      }
      return orderSourceIds.contains(String.valueOf(sourceId));
  }
  ```
- `getShippingFeeSettings` (~2288): truyền `fee.getOrderSourceIds()` vào constructor; 2 nhánh fallback (không có row / exception) truyền `null`.
- Tìm mọi chỗ khác gọi `new ShippingFeeSettings(` (kể cả trong `src/test`) và cập nhật theo constructor mới.

### 4. Gate — `src/main/java/vn/sapo/services/service/impl/EInvoiceServiceImpl.java`, trong `setOrderData` (~2650–2667)
Đổi `if (shippingFeeSettings.isSeparateLine())` thành:
```java
if (shippingFeeSettings.isSeparateLine()
        && shippingFeeSettings.appliesToOrderSource(orderResponse.getSourceId())) {
    ... // giữ nguyên thân hiện tại
} else if (shippingFeeSettings.isSeparateLine()) {
    log.debug("Skip shipping fee line tenantId={} orderId={} sourceId={} reason=source_not_matched",
            tenantId, orderId, orderResponse.getSourceId());
}
```
- `setOrderData` được gọi từ `createDraftInvoice` (~1503, dùng cho cả controller `create_draft` và Kafka `OrderConsumer` Auto Invoice) và `createDraftPreview` (~1994) → một chỗ sửa phủ đủ. **Xác minh lại** bằng grep, nếu có đường dựng dòng phí nào khác gọi `buildShippingFeeLineItem` thì áp cùng điều kiện.
- ⚠️ **KHÔNG** copy mẫu `isAutoHiddenReductionRate(long sourceId, …)` (~1390): tham số primitive `long` làm NPE khi `getSourceId()` null.

### 5. Unit test
Làm đủ nhóm **U1–U8** trong test-cases:
- Mở rộng `src/test/java/vn/sapo/services/service/publisher/sapoinvoice/SapoInvoiceSettingUtilTest.java` (U1–U5, U7).
- Test `appliesToOrderSource` (U6) — class mới `ShippingFeeSettingsTest` cùng package.
- Cập nhật `SapoInvoiceServiceShippingFeeResetTest` nếu so JSON default (U8).
Chạy: `mvn test -Dtest='SapoInvoiceSettingUtilTest,ShippingFeeSettingsTest,SapoInvoiceServiceShippingFeeResetTest,ShippingFeeLineHelperTest,EInvoiceItemTypeTotalsTest'` rồi `mvn test` toàn bộ.

## Definition of Done
- [ ] Build `mvn clean package -DskipTests` pass; toàn bộ `mvn test` pass (báo nguyên output nếu fail).
- [ ] JSON cũ (không có field) → hành vi y hệt trước (dòng phí cho mọi đơn).
- [ ] Không FQN inline; comment tiếng Việt cho logic nghiệp vụ; không đổi file ngoài phạm vi.
- [ ] Commit message không có dòng `Co-Authored-By`.
- [ ] Báo lại: diff tóm tắt, danh sách test đã thêm, các chỗ đã grep xác minh ở bước 4.
````

---

## Phiên 2 — FE

````markdown
# Task: Epic #102 — FE: trường "Nguồn đơn" cho cấu hình phí giao hàng (V2)

Repo: `/Users/sapo/invoice/sapo-frontend-v3` (React 16 + TS). File chính: `src/page/Settings/Einvoices/Einvoice.tsx`.
Figma: https://www.figma.com/design/eB5jx4MxReLJuyrlptKhs2/SAPO-INVOICE-V2?node-id=979-50171 ← dùng skill figma-design-to-code trước khi `get_design_context`.
Frame cần xem: `979:51676` (đã chọn 1 nguồn), `979:52519` (tên trống + checkbox tích), `979:53321` (lỗi validate), `979:50924` (mode none), `979:53317` (tooltip).
Tóm tắt UI đã trích sẵn trong plan, mục "UI theo Figma" — **đọc mục đó trước**, Figma chỉ để đối chiếu pixel.
Nhánh: `dev-money/feature/shipping-fee-by-source-SM-0`.

## Đọc trước
1. `/Users/sapo/invoice/AGENTS.md`, `/Users/sapo/developer-os/10_Projects/sapo-invoice/ai/rules-frontend.md`
2. Plan + test case epic 102 trong `/Users/sapo/developer-os/10_Projects/sapo-invoice/epic-102-phi-giao-hang-theo-nguon-don-v2/` (nhóm C của test case).
3. Tham chiếu V3 đã làm (chỉ đọc, không sửa): `git -C /Users/sapo/invoice/invoice-app show e90cc984 -- frontend/` — `SettingAutomaticPage.tsx`, `utils/shippingFeeSetting.ts`.

## Contract BE (đã làm ở phiên 1)
JSON string trong `shipping_fee_setting`:
`{ "mode": "none"|"separate_line", "item_name": string, "auto_adjust": boolean, "order_source_ids": string[] | null }`
- `null` = chưa từng lưu. Lỗi BE khi list rỗng: `Nguồn đơn không được để trống` (field `setting`).

## Việc cần làm
1. `parseShippingFeeSetting` / `stringifyShippingFeeSetting` (~87–112): thêm `order_source_ids` (không phải array → `null`; lọc phần tử string). `stringify` giữ `null` nếu là `null`.
2. Trường **"Nguồn đơn"** (nhãn `Nguồn đơn` + `*` đỏ, placeholder **`Chọn giá trị`** — đúng Figma, KHÔNG dùng `Chọn nguồn đơn`) đặt **dưới** ô "Tên dòng phí trên hóa đơn", **full width**, **trên** checkbox "Tự động điều chỉnh phí giao hàng", trong cùng `Box marginLeft: 28` hiện có (~1522). **Không** làm 2 cột như V3. **Chỉ hiện khi `mode === "separate_line"`**.
   - Dùng lại `DropdownSearch` `multiple` + `activeOrderSources` giống trường "Không hiện chiết khấu trên hóa đơn theo nguồn đơn" (~1405–1450): `fetchOptions` lọc bỏ dấu, `renderOption={(o) => o.name}`, `backgroundColor="#FFFFFF"`, `error`/`helperText`.
   - Popup của component đã có hàng checkbox **chọn tất cả** (value `"all"`) → đó là "Tất cả nguồn đơn", không tự thêm option.
   - Figma: khi có chọn, ô hiển thị `Đã chọn {n} giá trị` và **chip có nút ✕** cho từng nguồn ngay dưới ô (margin-top ~8px). Kiểm tra component có tự render như vậy không; nếu không, tự render chip (dùng `Chip`/`Tag` của `@sapo-presentation/sapo-ui-components`, bấm ✕ = bỏ nguồn đó khỏi list).
   - Không đổi các chữ/khối khác của section (radio, mô tả, tooltip, checkbox, "Lưu ý:") — đã khớp Figma.
3. Giá trị `null` → hiển thị tích hết `activeOrderSources`. Khi **lưu** ở `separate_line` mà giá trị đang `null` → gửi id (String) của toàn bộ `activeOrderSources` (giống `resolveOrderSourceNamesForSubmit` V3). Lưu ở `none` → giữ nguyên giá trị hiện có.
4. **BR5 — V3 làm thiếu, V2 bắt buộc (Figma chưa vẽ):** id đã lưu nhưng không có trong `activeOrderSources` (ngừng áp dụng / bị xóa) **không được rơi** khỏi state khi hiển thị/lưu — lưu ý `onChange` của `DropdownSearch` chỉ trả các item active, phải **gộp lại** các id inactive đang có trước khi set state. Hiển thị chip với hậu tố tạm ` (Ngừng áp dụng)` màu xám `#747C87`; tên lấy từ danh sách nguồn đầy đủ (trước khi lọc status, ~224) nếu có, không có thì hiển thị id. Chỉ xóa khi user bấm ✕ trên chip đó. Đếm `Đã chọn {n} giá trị` tính cả id inactive.
5. Validate FE trong hàm validate hiện có (~461–473): `separate_line` + list rỗng → viền đỏ + `Nguồn đơn không được để trống` dưới trường (Figma `979:53321`). **Không return sớm**: nếu cả tên dòng phí lẫn nguồn đơn đều trống thì hiện **cả 2 lỗi cùng lúc**. Clear lỗi khi chọn lại hoặc đổi mode. Lỗi BE cùng message → hiển thị cùng chỗ.
6. Dirty-check / nút Lưu: đổi nguồn phải bật trạng thái có thay đổi.

## Definition of Done
- [ ] Case C1–C9, C12 và F1–F8 trong test-cases chạy tay pass trên local/dev.
- [ ] `yarn lint` / type-check pass.
- [ ] Không đổi hành vi các cài đặt khác (R2).
- [ ] Commit message không có dòng `Co-Authored-By`.
````
