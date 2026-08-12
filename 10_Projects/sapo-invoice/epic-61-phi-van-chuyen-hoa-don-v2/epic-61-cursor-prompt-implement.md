---
created: 2026-08-11 17:00
updated: 2026-08-12 10:45
status: Draft — chưa chạy
project: "[[10_Projects/sapo-invoice/README]]"
---

# Prompt Cursor — implement Epic #61 (phí vận chuyển trên hóa đơn V2, SRS v0.6)

Plan/SRS đầy đủ: [[epic-61-phi-van-chuyen-hoa-don-v2]] · SRS gốc đã cập nhật: `invoice-docs!105` (v0.6)

⚠️ **Chưa giải quyết B0 (shape `order.delivery_fee`)** trước khi chạy prompt này — SRS v0.6 KHÔNG đề cập vấn đề này (nó về 2 điểm khác — tên dòng phí + checkbox điều chỉnh). B0 vẫn cần xác nhận riêng với BA/Omni. Phần Backend A5 đã viết theo shape hiện tại (object đơn) kèm TODO rõ ràng.

Copy toàn bộ phần trong khung dưới đây và dán vào Cursor (mở workspace `/Users/sapo/invoice`).

---

````markdown
# Task: Cấu hình & dựng dòng phí vận chuyển trên hóa đơn V2 (BE + FE)

Workspace: `/Users/sapo/invoice` — làm việc trên 2 repo:
- `sapo-einvoice-service` (Java 11 / Spring Boot 2.1, Maven, SQL Server)
- `sapo-frontend-v3` (React 16 + TS, Webpack 5, Node 14/24)

Epic gốc: GitLab `&61` (group sapo-money/sapo-invoice, module `invoice-core-v2`) · SRS v0.6 đầy đủ: developer-os `10_Projects/sapo-invoice/epic-61-phi-van-chuyen-hoa-don-v2/epic-61-phi-van-chuyen-hoa-don-v2.md`

## Đọc trước khi code

1. `/Users/sapo/invoice/AGENTS.md` — routing repo
2. `sapo-einvoice-service/docs/project-context.md` — ⚠️ mục Database ghi PostgreSQL là **sai**, DB thật là SQL Server (T-SQL, xác nhận qua các file `V1-V7` trong `db/migration/`)
3. ⚠️ **Flyway KHÔNG được wire vào app này** (`docs/architecture/data-models-and-schema-changes.md` dòng 103-105 tự ghi "Flyway/Liquibase: Not currently used"; `pom.xml` không có dependency flyway). File `V1-V7` chỉ là script tài liệu — **không tự chạy khi deploy**. Migration mới (`V8`, mục A6 dưới) phải báo người quản lý deploy chạy tay trên SQL Server từng môi trường, phối hợp với thời điểm deploy code.

⚠️ **Trạng thái thật của feature `item_type` (epic phụ thuộc &46, Tính chất hàng hóa/dịch vụ) — ĐÃ KIỂM CHỨNG, không phải giả định:**
- `EInvoiceLineItemType` enum đã tồn tại: `DEFAULT(1), PROMOTION(2), DISCOUNT(3), NOTE(4)` — dùng `DEFAULT` cho dòng phí VC.
- `EInvoiceLineItemDTO.itemType` (Integer) đã có sẵn field, dùng được ngay.
- `SapoInvoiceService.java` dòng ~677 (`prepareSapoInvoiceRequest`) khi build payload gửi Sapo Invoice **vẫn hardcode** `sapoInvoiceLineItem.setItemType("products")` cho MỌI dòng — không đọc từ `getItemType()`. Không chặn task này (dòng phí VC vốn `item_type=1`=products nên hardcode tình cờ vẫn đúng) — **KHÔNG sửa** dòng này, thuộc epic &46 khác.
- Tổng hóa đơn (`totalSaleAmount`, `totalAmountWithoutVAT`, `totalVATAmount`, `totalAmount` trong `EInvoiceServiceImpl.setOrderData()` dòng ~2064-2080) **cộng dồn thuần** trên TOÀN BỘ `lineItems`, không filter theo `item_type`. Chỉ cần thêm dòng phí VC vào list `lineItems` trước dòng `eInvoiceDTO.setLineItems(lineItems)` (dòng 2061) là tổng tự động đúng.
- ⚠️ **FE — field `item_type` trên `EinvoiceLineItem` (`services/EinvoiceService/type.ts:94`) đang bị dùng cho mục đích KHÁC:** `FormEinvoice.tsx:921`: `model.item_type = v.variant.product_type;` (tính chất sản phẩm catalog, không phải "Tính chất hóa đơn"). Xung đột đã biết, chính epic &46 tự ghi "F0 (chặn)" ở ticket US-1 (#49), có vẻ chưa xử lý. **KHÔNG động vào field này** trong task hiện tại — task này cố tình dùng field **khác** (`is_shipping_line`, xem A6/B4) để tránh đụng xung đột trên.

## Mục tiêu

Thêm cấu hình cấp store gồm **3 phần**: (1) `shipping_fee_mode` (`none` mặc định / `separate_line`), (2) `shipping_fee_item_name` (tên dòng phí, bắt buộc, autofill "Phí giao hàng", ≤255 ký tự), (3) `auto_adjust_shipping_fee` (checkbox, mặc định bỏ tích). Khi `separate_line` + provider = Sapo Invoice + order có phí vận chuyển → tự động thêm 1 dòng phí vào hóa đơn khi tạo draft (thủ công lẫn Auto Invoice). Đổi provider khỏi Sapo Invoice khi **sửa** hóa đơn → dòng phí bị loại (A7 + B4, vì luồng sửa không tự rebuild từ order). Khi hệ thống tự tạo hóa đơn điều chỉnh → dòng phí bị ghi âm hay loại trừ tùy `auto_adjust_shipping_fee` (A8, mục hoàn toàn mới so với v0.5).

## ⚠️ Chưa xác nhận — shape `order.delivery_fee` (B0, KHÔNG liên quan SRS v0.6)

SRS giả định `order.delivery_fee` là **mảng** (nhiều phí, `Σ fee`). Code thật hiện tại:

```java
// OrderResponse.java:57, OrderDomain.java:58
private DeliveryFeeResponse deliveryFee;   // OBJECT ĐƠN, không phải List
```

`getDeliveryFee()` hiện **không được gọi ở đâu** trong codebase (an toàn để sửa type nếu cần) — nhưng **task này code theo shape HIỆN TẠI (object đơn, 1 phí)**, không tự ý đổi field sang `List`. Nếu sau này xác nhận là mảng, chỉ cần sửa hàm `buildShippingFeeLineItem` ở mục A4 (đã cô lập logic đọc `delivery_fee` vào đúng 1 hàm cho việc này).

---

# PHẦN A — Backend (`sapo-einvoice-service`)

Branch: `dev-money/feature/shipping-fee-invoice-v2` (tách từ `master`)

Đường dẫn dưới đây tính từ `src/main/java/vn/sapo/services/`.

## A1. Setting mới — `domain/sapoinvoice/SapoInvoiceSetting.java`

Thêm **3** giá trị vào enum `SettingKey` (dòng ~39-42 hiện tại):

```java
public enum SettingKey {
    auto_apply_tax_reduction_rate, auto_fill_invoice_series_by_location, auto_hidden_reduction_by_source,
    auto_fill_anonymous_customer, disable_adjustment_calculation_invoice, invoice_payment_methods,
    einvoice_explode_composite_lines, shipping_fee_mode, shipping_fee_item_name, auto_adjust_shipping_fee
}
```

## A2. `service/publisher/sapoinvoice/SapoInvoiceSettingUtil.java` — validate + default

**a) Type check** — thêm vào 2 nhóm case sẵn có (dòng ~24-42):

```java
case "auto_apply_tax_reduction_rate":
case "disable_adjustment_calculation_invoice":
case "einvoice_explode_composite_lines":
case "auto_adjust_shipping_fee":                    // ← THÊM
    if (!(value instanceof Boolean)) {
        throw new SapoInvoiceExeption(
            "setting", String.format("Key '%s' phải có value kiểu Boolean", key)
        );
    }
    break;
case "auto_fill_invoice_series_by_location":
case "auto_hidden_reduction_by_source":
case "auto_fill_anonymous_customer":
case "invoice_payment_methods":
case "shipping_fee_mode":                            // ← THÊM
case "shipping_fee_item_name":                       // ← THÊM
    if (!(value instanceof String)) {
        throw new SapoInvoiceExeption(
            "setting", String.format("Key '%s' phải có value kiểu String", key)
        );
    }
    break;
```

**b) Validate nghiệp vụ — bắt buộc + giới hạn 255 ký tự cho `shipping_fee_item_name`.** ⚠️ Đây là validate **cross-field** đầu tiên trong file này (mọi case hiện có chỉ check kiểu dữ liệu độc lập từng key) — cần biết CẢ `shipping_fee_mode` lẫn `shipping_fee_item_name` cùng lúc, nên đặt sau vòng `for` trong `validateSettings()`, không đặt trong switch:

```java
public static void validateSettings(Map<String, Object> settings) {
    if (settings == null || settings.isEmpty()) {
        throw new SapoInvoiceExeption("setting", "Thông tin cấu hình không được để trống");
    }

    for (Map.Entry<String, Object> entry : settings.entrySet()) {
        // ... switch hiện có, đã thêm 3 case ở mục (a) ...
    }

    // ↓↓↓ THÊM MỚI — validate cross-field cho shipping_fee_item_name (BR05, UC-01 AC7) ↓↓↓
    if ("separate_line".equals(settings.get("shipping_fee_mode"))) {
        Object itemNameValue = settings.get("shipping_fee_item_name");
        String itemName = itemNameValue instanceof String ? (String) itemNameValue : null;
        if (StringUtils.isBlank(itemName)) {
            throw new SapoInvoiceExeption("setting", "Vui lòng nhập tên dòng phí trên hóa đơn.");
        }
        if (itemName.length() > 255) {
            throw new SapoInvoiceExeption("setting", "Tên dòng phí tối đa 255 ký tự.");
        }
    }
    // ↑↑↑ HẾT PHẦN THÊM MỚI ↑↑↑
}
```

Dùng đúng nguyên văn 2 message lỗi trên (đã chốt trong SRS v0.6 §6.1, dùng làm expected string cho FE/QA).

**c) Default value** — thêm case trong `getDefaultValue()` (dòng ~69-82):

```java
case "shipping_fee_mode":
    return "none";
case "shipping_fee_item_name":
    return "Phí giao hàng";        // autofill mặc định, KHÔNG dùng "" như setting String khác
case "auto_adjust_shipping_fee":
    return false;
```

## A3. Không cần sửa `SapoInvoiceController.java`

`POST/GET /invoice_providers/sapo_invoice/settings` (dòng 271, 297) đã tổng quát qua `Map<String, Object>` — 3 key mới tự động đi qua được, không cần thêm field DTO riêng.

## A4. Đọc setting trong lúc dựng hóa đơn — `service/publisher/sapoinvoice/SapoInvoiceService.java`

Thêm 3 method mới, đặt cạnh `isExplodeCompositeLines` (dòng ~1872-1883), **copy đúng pattern try/catch/log.warn** của nó:

```java
public String getShippingFeeMode(long tenantId) {
    try {
        return sapoInvoiceSettingRepository.findByTenantIdAndSettingKey(tenantId,
                SapoInvoiceSetting.SettingKey.shipping_fee_mode)
            .map(SapoInvoiceSetting::getSettingValue)
            .orElse("none");
    } catch (Exception e) {
        log.warn("Cannot read shipping_fee_mode setting for tenant {}: {}", tenantId, e.getMessage());
        return "none";
    }
}

public String getShippingFeeItemName(long tenantId) {
    try {
        return sapoInvoiceSettingRepository.findByTenantIdAndSettingKey(tenantId,
                SapoInvoiceSetting.SettingKey.shipping_fee_item_name)
            .map(SapoInvoiceSetting::getSettingValue)
            .filter(StringUtils::isNotBlank)
            .orElse("Phí giao hàng");
    } catch (Exception e) {
        log.warn("Cannot read shipping_fee_item_name setting for tenant {}: {}", tenantId, e.getMessage());
        return "Phí giao hàng";
    }
}

public boolean isAutoAdjustShippingFee(long tenantId) {
    try {
        return sapoInvoiceSettingRepository.findByTenantIdAndSettingKey(tenantId,
                SapoInvoiceSetting.SettingKey.auto_adjust_shipping_fee)
            .map(setting -> Boolean.parseBoolean(setting.getSettingValue()))
            .orElse(false);
    } catch (Exception e) {
        log.warn("Cannot read auto_adjust_shipping_fee setting for tenant {}: {}", tenantId, e.getMessage());
        return false;
    }
}
```

## A5. Dựng dòng phí VC — `service/impl/EInvoiceServiceImpl.java`

**Điểm chốt duy nhất:** method `setOrderData()` (dòng 1798). Dùng chung cho CẢ `createDraftInvoice` (dòng 1468, luồng thủ công) LẪN Auto Invoice — đã verify `createDraft(OrderDomain, Long)` (dòng 260, gọi từ `AutoInvoiceExecutionServiceImpl.java:622`) và `createDraft(OrderDomain)` (dòng 244) đều đổ về `createDraftInvoice()` → `setOrderData()`. Sửa đúng 1 chỗ này là phủ cả 2 luồng.

**Bước 1 — thêm hàm private mới** (đặt gần `setOrderData`, cùng class):

```java
private EInvoiceLineItemDTO buildShippingFeeLineItem(OrderResponse orderResponse, long tenantId,
        long orderId, int lineNumber) {
    // TODO: SRS giả định order.delivery_fee là MẢNG (nhiều phí, Σ fee).
    // Code hiện tại (OrderResponse.getDeliveryFee()) trả 1 OBJECT ĐƠN — implement theo shape này (B0, chưa xác nhận với BA/Omni).
    // Nếu sau này xác nhận Omni trả mảng, sửa lại đúng hàm này (đổi tham số đầu vào,
    // và tổng hợp Σ fee thay vì đọc 1 fee đơn).
    DeliveryFeeResponse deliveryFee = orderResponse.getDeliveryFee();
    if (deliveryFee == null || deliveryFee.getFee() == null) {
        return null; // Không có phí vận chuyển -> không tạo dòng (BR01)
    }

    BigDecimal fee = deliveryFee.getFee().setScale(3, RoundingMode.HALF_UP);

    EInvoiceLineItemDTO lineItem = new EInvoiceLineItemDTO();
    lineItem.setOrderId(orderId);
    lineItem.setTenantId(tenantId);
    lineItem.setLineNumber(lineNumber);
    lineItem.setItemType(EInvoiceLineItemType.DEFAULT.value()); // BR01: item_type=1 (products)
    lineItem.setIsShippingLine(true); // BR10 — marker, xem A6 cho lý do cần field riêng này
    lineItem.setItemName(sapoInvoiceService.getShippingFeeItemName(tenantId)); // BR05 v0.6: từ cấu hình, KHÔNG cố định
    lineItem.setUnitName("");
    lineItem.setQuantity(BigDecimal.ONE);
    lineItem.setUnitPrice(fee);
    lineItem.setAmount(fee);
    lineItem.setTaxRate(BigDecimal.ZERO);
    lineItem.setTaxName("KCT"); // BR03 — pattern "KCT" đã dùng ở SInvoiceService.java:314, MeinvoiceMapper.java
    lineItem.setTaxAmount(BigDecimal.ZERO);
    lineItem.setDiscountRate(BigDecimal.ZERO);
    lineItem.setUnitDiscountAmount(BigDecimal.ZERO);
    lineItem.setDiscountAmount(BigDecimal.ZERO);
    lineItem.setDiscountAllocationAmount(BigDecimal.ZERO);
    lineItem.setTotalDiscountAmount(BigDecimal.ZERO);
    lineItem.setAmountWithoutVAT(fee); // BR06: amount - totalDiscountAmount(=0) = fee
    lineItem.setStatus(EInvoiceLineItemStatus.ACTIVE.value());
    return lineItem;
}
```

**Bước 2 — gọi hàm này trong `setOrderData()`, CHÈN GIỮA dòng 2059 (`}` đóng vòng lặp chính) và dòng 2061 (`eInvoiceDTO.setLineItems(lineItems);`)**:

```java
            lineItems.add(lineItem);
            lineNumber++;
        }
        // ↓↓↓ CHÈN ĐOẠN MỚI Ở ĐÂY ↓↓↓
        boolean isSapoInvoiceProvider = EInvoiceProvider.SAPO_INVOICE.value()
                .equals(eInvoiceDTO.getPublishingProvider());
        if (isSapoInvoiceProvider && "separate_line".equals(sapoInvoiceService.getShippingFeeMode(tenantId))) {
            EInvoiceLineItemDTO shippingFeeLineItem = buildShippingFeeLineItem(orderResponse, tenantId, orderId, lineNumber);
            if (shippingFeeLineItem != null) {
                lineItems.add(shippingFeeLineItem);
                lineNumber++;
            }
        }
        // ↑↑↑ HẾT ĐOẠN MỚI ↑↑↑

        eInvoiceDTO.setLineItems(lineItems);
```

⚠️ `sapoInvoiceService` đã là field/dependency có sẵn trong class này (dùng ở dòng 1429, 1852) — không cần inject thêm. `eInvoiceDTO.getPublishingProvider()` tại đây đã được set xong ở đoạn code phía trên (dòng 1417-1443) — đọc sau thời điểm đó an toàn (BR09).

## A6. Marker `is_shipping_line` — migration + field, LÝ DO CẦN THIẾT (đọc kỹ trước khi bỏ qua)

**Vì sao không dùng `item_name` để nhận diện dòng phí VC (như bản v0.5 từng định làm):** từ v0.6, `item_name` **cấu hình được** (`shipping_fee_item_name`) — merchant đổi tên bất kỳ lúc nào, nên so khớp chuỗi để nhận diện "đây là dòng phí VC" ở A7 (đổi provider) và A8 (điều chỉnh tự động) sẽ sai ngay khi tên bị đổi.

**Vì sao không tái dùng `itemCode` (item_id-style) làm marker:** đã verify `itemCode` bị dùng cho việc khác — hiển thị trực tiếp lên UI khi user bật cột "Mã hàng" (`EinvoiceTableLineItems.tsx:245-247`), gửi thẳng sang API Sapo Invoice (`SapoInvoiceService.java:680`), và dùng match metafield (dòng 925-932). Nhét giá trị đánh dấu vào đây sẽ rò rỉ ra hóa đơn thật.

**Vì sao không dùng `itemId == null` (cách code hiện tại phân biệt dòng "freeform"):** dòng phí VC cũng sẽ có `itemId = null` (không phải sản phẩm thật) — **giống hệt** điều kiện của 1 dòng freeform user tự gõ tay (xem `ProductType.FREEFORM`, chỉ dùng làm tiền tố key tạm thời trong `edit()` dòng 1022/1168/1208, KHÔNG phải cột lưu DB). Không có field nào tách 2 loại dòng `itemId=null` này ra.

→ **SRS v0.6 (BR10) đã chốt: thêm marker riêng `is_shipping_line` (Boolean).** Migration:

```sql
-- src/main/resources/db/migration/V8__add_is_shipping_line_to_einvoice_lineitems.sql
IF NOT EXISTS (
    SELECT * FROM sys.columns
    WHERE object_id = OBJECT_ID('EInvoiceLineItems') AND name = 'IsShippingLine'
)
BEGIN
    ALTER TABLE [EInvoiceLineItems] ADD [IsShippingLine] BIT NULL;
END
GO
```

⚠️ **File này KHÔNG tự chạy khi deploy** (xem cảnh báo Flyway ở "Đọc trước khi code") — báo người quản lý deploy chạy tay câu SQL trên SQL Server từng môi trường (dev2/staging/prod) **trước hoặc cùng lúc** deploy code. Cột nullable, không default khác NULL → dữ liệu cũ không bị ảnh hưởng, không cần backfill.

**Thêm field `isShippingLine` (Boolean) vào 4 class** — TÊN GIỐNG HỆT NHAU ở cả 4 nơi:
- `domain/EInvoiceLineItem.java` (entity — map trực tiếp cột `IsShippingLine`)
- `model/einvoice/EInvoiceLineItemDTO.java`
- `model/einvoice/EInvoiceLineItemRequest.java`
- `model/einvoice/EInvoiceLineItemResponse.java`

⚠️ **Không cần sửa `EInvoiceLineItemMapper.java`** — đây là MapStruct interface **không có `@Mapping` thủ công nào** (đã verify), tự map theo tên field trùng khớp. Thêm field cùng tên `isShippingLine` vào cả 4 class là đủ, MapStruct tự nối dây.

**KHÔNG** thêm field này vào `SapoInvoiceLineItem.java` (payload gửi Sapo Invoice) — chỉ là marker nội bộ, không có ý nghĩa với API công khai của SI, cố tình không map sang (đối lập với `itemCode` — xem lý do ở trên).

## A7. Đổi provider khi SỬA hóa đơn đã tồn tại (UC-02 AC10 / BR09)

**Đã đọc trực tiếp `EInvoiceServiceImpl.edit()` (dòng 1007-1198) — xác nhận: hàm này KHÔNG rebuild `lineItems` từ order.** Nó map thẳng `eInvoiceDTO = eInvoiceMapper.toDTO(eInvoiceRequest)` (dòng 1027) — `lineItems` đến từ **client gửi lên nguyên vẹn**, backend chỉ tính lại tiền/tổng cho từng dòng client gửi (dòng 1087-1163), không đụng tới `orderResponse`/`setOrderData()`. Vậy BR09 không tự đúng — phải code cả 2 phía (backend chặn 1 chiều, FE lo chiều dựng lại — xem B4).

Thêm ngay sau dòng 1028 (`eInvoiceDTO.setCustomFields(eInvoiceRequest.getCustomFields());`), trước khối xác định `invoiceName`:

```java
// BR09: server không tin client — nếu provider phát hành khác Sapo Invoice thì
// luôn loại bỏ dòng phí VC (nhận diện qua is_shipping_line, KHÔNG so tên — BR10) dù client có gửi lên hay không.
if (!EInvoiceProvider.SAPO_INVOICE.value().equals(eInvoiceDTO.getPublishingProvider())) {
    eInvoiceDTO.setLineItems(eInvoiceDTO.getLineItems().stream()
        .filter(li -> !Boolean.TRUE.equals(li.getIsShippingLine()))
        .collect(Collectors.toList()));
}
```

**Không cần code "dựng lại khi đổi ngược" ở backend** — `edit()` không có sẵn `OrderResponse` (không refetch order giữa chừng). Trách nhiệm "dựng lại" giao cho FE (mục B4) vì FE đã có sẵn dòng phí trong state trước khi user bấm đổi provider.

## A8. Điều chỉnh hóa đơn tự động (`auto_adjust_shipping_fee`, UC-01 AC8 + BR08 — MỤC HOÀN TOÀN MỚI so với v0.5)

**Đã trace toàn bộ luồng "hóa đơn điều chỉnh tự động" — chỉ có ĐÚNG 1 đường vào, không phức tạp:**

`createAdjustmentAutoDraft(OrderDomain, autoInvoiceConfigId)` (dòng 325) là **nơi duy nhất** gọi `createDraftInvoice(..., adjustmentBaseline)` với baseline khác null (đã grep toàn file xác nhận). Không có luồng "tạo hóa đơn điều chỉnh thủ công" nào khác. Trong đó, `buildAdjustmentLineItemsFromBaseline(baseline)` (dòng 1641) copy **toàn bộ** dòng hàng từ hóa đơn gốc, không lọc gì — sửa đúng hàm này.

Đọc setting mới `getShippingFeeMode`/`isAutoAdjustShippingFee` không cần vì **KHÔNG gate theo `shipping_fee_mode`** ở đây — chỉ cần biết dòng nào là `is_shipping_line=true` (đã persist sẵn trên baseline) và `auto_adjust_shipping_fee` hiện tại của tenant. `AutoInvoiceConfig.AutoAdjustmentInvoiceEnabled` (setting Auto Invoice có sẵn, KHÔNG phải setting mới của task này) đã tự gate trước khi luồng chạy tới đây — không cần check lại.

Sửa `buildAdjustmentLineItemsFromBaseline` (dòng 1641):

```java
private List<EInvoiceLineItemDTO> buildAdjustmentLineItemsFromBaseline(EInvoice baseline) {
    if (baseline.getLineItems() == null || baseline.getLineItems().isEmpty()) {
        return Collections.emptyList();
    }
    // BR08/BR10: loại dòng phí VC khỏi hóa đơn điều chỉnh nếu auto_adjust_shipping_fee đang tắt
    boolean autoAdjustShippingFee = sapoInvoiceService.isAutoAdjustShippingFee(baseline.getTenantId());

    List<EInvoiceLineItemDTO> lineItems = new ArrayList<>();
    int fallbackLineNumber = 1;
    for (EInvoiceLineItem baselineLine : baseline.getLineItems()) {
        if (baselineLine == null) {
            continue;
        }
        // ↓↓↓ THÊM MỚI ↓↓↓
        if (Boolean.TRUE.equals(baselineLine.getIsShippingLine()) && !autoAdjustShippingFee) {
            continue; // bỏ tích -> loại trừ dòng phí VC khỏi điều chỉnh (BR08)
        }
        // ↑↑↑ HẾT PHẦN THÊM MỚI ↑↑↑
        EInvoiceLineItemDTO lineItem = eInvoiceLineItemMapper.toDTO(baselineLine);
        lineItem.setId(null);
        lineItem.setEInvoiceId(null);
        // ... phần còn lại của hàm giữ nguyên không đổi ...
    }
    // ... phần còn lại của hàm giữ nguyên không đổi ...
}
```

Khi **tích** `auto_adjust_shipping_fee`: dòng phí VC được copy như mọi dòng khác, sau đó `applyNegativeSignToAdjustmentAutoDraft()` (dòng 1522, gọi ở dòng 1458) tự ghi âm **toàn bộ** `lineItems` bao gồm dòng phí — không cần code thêm gì cho việc ghi âm, hàm đó đã generic theo `dto.getLineItems()`.

## A9. Publish sang Sapo Invoice

`SapoInvoiceService.prepareSapoInvoiceRequest()` (dòng ~663+) đọc từ `eInvoiceResponse.getLineItems()` (không phải từ DTO) — dòng phí VC đã persist qua `EInvoice` entity ở bước tạo draft nên tự động có mặt khi publish, **không cần sửa gì thêm ở đây**. Verify sau khi test thủ công: dòng phí xuất hiện trong request gửi SI với `item_type="products"` (hardcode hiện tại, xem cảnh báo đầu file) và field tiền đúng.

---

# PHẦN B — Frontend (`sapo-frontend-v3`)

Branch: `dev-money/feature/shipping-fee-invoice-v2` (tách từ `master`)

## B1. Màn cấu hình — ĐÃ XÁC NHẬN tồn tại thật (khác v0.5, không cần điều tra lại)

Đã xem trực tiếp Figma design (`figma.com/design/eB5jx4MxReLJuyrlptKhs2/SAPO-INVOICE-V2?node-id=979-50171`) — màn "Quản lý kết nối Sapo Invoice" → section "Cài đặt chung" đã tồn tại thật, có sẵn các setting boolean khác cùng dạng (checkbox "Tự động tính lại giá trị...", "Không hiện chiết khấu...", "Tạo hóa đơn điện tử cho sản phẩm gốc..."). Section mới "Thiết lập hiển thị phí giao hàng" nằm ngay dưới. Nếu grep `getSapoInvoiceSettings`/`updateSapoInvoiceSettings` trong `src/` vẫn ra rỗng như lần kiểm tra trước — nghĩa là component đọc/ghi setting này chưa được nối API thật dù UI (theo Figma) đã thiết kế xong; tìm đúng file component của màn "Quản lý kết nối Sapo Invoice" (tìm theo route hoặc theo text "Quản lý kết nối Sapo Invoice" trong `src/page/`) để thêm cả phần gọi API nếu cần, không chỉ thêm control.

## B2. 2 control mới trong section "Thiết lập hiển thị phí giao hàng"

**Radio `shipping_fee_mode`** (đã có ở bản trước, giữ nguyên): `none` ("Không hiển thị phí giao hàng") / `separate_line` ("Hiển thị 1 dòng phí giao hàng").

**Khi chọn `separate_line`, hiện thêm 2 control mới (v0.6):**

1. **Text field `shipping_fee_item_name`** — dùng đúng nguyên văn UI copy đã chốt trong SRS:
   - Nhãn: `Tên dòng phí trên hóa đơn`
   - Giá trị autofill mặc định: `Phí giao hàng`
   - Placeholder: `Nhập tên dòng phí…`
   - Helptext: `Tên này hiển thị làm tên hàng hóa/dịch vụ của dòng phí trên hóa đơn.`
   - Lỗi khi trống: `Vui lòng nhập tên dòng phí trên hóa đơn.`
   - Lỗi khi >255 ký tự: `Tên dòng phí tối đa 255 ký tự.`
   - Validate: bắt buộc, `maxLength={255}`, chặn lưu khi vi phạm (khớp validate backend ở A2b — làm validate FE **thêm**, không thay thế, BE vẫn phải tự chặn).

2. **Checkbox `auto_adjust_shipping_fee`** — nhãn "Tự động điều chỉnh phí giao hàng", **mặc định bỏ tích**, helptext = đúng cảnh báo điều chỉnh (xem dưới).

Cảnh báo pháp lý (nguyên văn, hiện khi `separate_line`, giữ nguyên):
> ⚠️ Chỉ cài đặt hiển thị phí vận chuyển khi bạn thực sự cung cấp dịch vụ vận chuyển. Nếu phí do bên thứ ba thu hộ, khoản này không thuộc đối tượng phải xuất hóa đơn (Nghị định 254/2026/NĐ-CP).

Cảnh báo điều chỉnh (nguyên văn, **đổi nhẹ ở v0.6** — thêm "tích chọn"):
> ⚠️ Nếu tích chọn và đã cài đặt Tự động tạo và phát hành hóa đơn điều chỉnh, hệ thống sẽ tự động điều chỉnh dòng phí vận chuyển cùng các dòng hàng hóa, dịch vụ khi điều chỉnh hóa đơn có phát sinh phí vận chuyển.

Bám UI pattern của các setting boolean/text khác đã có trong cùng màn (copy component/style, đừng tự thiết kế mới).

## B3. Hiển thị dòng phí VC trên form hóa đơn — không cần code gì thêm

Dòng phí VC là dòng `item_type=1` bình thường trả về từ backend trong `line_items[]` — bảng `EinvoiceTableLineItems.tsx` render mọi dòng hàng hóa như nhau. Không cần logic riêng để hiển thị. Chỉ verify bằng test thủ công.

## B4. Đổi provider trên form — ẩn/khôi phục dòng phí VC (khớp A7)

**Hook điểm chính xác:** hàm `handleProviderChange` trong `FormEinvoice.tsx` (dòng ~1592-1606) — **onChange duy nhất** của dropdown `publishing_provider` (dòng ~2214-2227).

**Nhận diện dòng phí VC bằng field `is_shipping_line` (KHÔNG so `item_name`)** — vì tên giờ cấu hình được (v0.6), so tên sẽ sai khi merchant đổi tên. Cần thêm field `is_shipping_line?: boolean` vào type `EinvoiceLineItem` (`services/EinvoiceService/type.ts`, cạnh `item_type`) để nhận đúng field mới từ backend response.

**Vẫn giữ nguyên chiến lược "cất đi rồi khôi phục nguyên trạng"** (không đổi so với thiết kế trước, chỉ đổi điều kiện tìm dòng) — vì lý do sau vẫn còn nguyên: `item_type` trên `EinvoiceLineItem` (FE) đang xung đột với `variant.product_type` (xem đầu file) → tuyệt đối KHÔNG tự dựng `EinvoiceLineItem` mới cho dòng phí VC ở FE, chỉ thao tác trên object đã có sẵn từ backend:

```tsx
// Khai báo cùng chỗ các state khác của FormEinvoice
const shippingFeeLineRef = useRef<EinvoiceLineItem | null>(null);

const handleProviderChange = (event: any) => {
  // ... code hiện có giữ nguyên (dòng 1592-1600) ...
  setValue("publishing_provider", event.value as string);
  if (provider !== event.value) {
    setValue("serial_no", "");
    setEinvoiceCustomFields([]);
  }

  // ↓↓↓ THÊM MỚI — ẩn/khôi phục dòng phí VC theo provider ↓↓↓
  const isSwitchingAwayFromSapoInvoice =
    provider === EInvoiceProvider.SAPO_INVOICE && event.value !== EInvoiceProvider.SAPO_INVOICE;
  const isSwitchingBackToSapoInvoice =
    provider !== EInvoiceProvider.SAPO_INVOICE && event.value === EInvoiceProvider.SAPO_INVOICE;

  if (isSwitchingAwayFromSapoInvoice) {
    const shippingLine = lineItemsStore.find((line) => line.is_shipping_line === true);
    if (shippingLine) {
      shippingFeeLineRef.current = shippingLine; // cất nguyên object, KHÔNG đụng item_type
      deleteLineItem(shippingLine.uid as string);
    }
  } else if (isSwitchingBackToSapoInvoice && shippingFeeLineRef.current) {
    addLineItem(shippingFeeLineRef.current); // khôi phục nguyên object đã cất
    shippingFeeLineRef.current = null;
  }
  // ↑↑↑ HẾT PHẦN THÊM MỚI ↑↑↑

  setProvider(event.value as string);
};
```

Cần thêm `deleteLineItem` vào destructure của `useLineItemEinvoiceStore` ở dòng ~339-345 (hiện tại chỉ lấy `addLineItem, updateLineItem, lineItemsStore, setLineItems, scannerOption` — thiếu `deleteLineItem`).

**Vì sao cách này đúng với BR09 dù không gọi lại API:** trong 1 phiên sửa hóa đơn, giá trị `delivery_fee`/`fee` của order không đổi — cất & khôi phục nguyên object cho kết quả tiền giống hệt "tính lại từ delivery_fee", mà không cần FE biết gì về `delivery_fee` (hiện FE hoàn toàn chưa có field này) và không cần thêm API call.

**Nếu `shippingFeeLineRef.current` rỗng khi đổi ngược về Sapo Invoice** — hóa đơn này vốn chưa từng có dòng phí VC lúc mở form → **không tự thêm dòng**, giữ đúng BR02 (cấu hình chỉ áp dụng lúc tạo).

---

# Verify

**Backend**
```bash
cd /Users/sapo/invoice/sapo-einvoice-service
mvn -s .m2/settings.xml clean compile
```
(Không có test nào trong repo này — `mvn test` sẽ pass vì rỗng, không phải bằng chứng code đúng. Verify bằng test thủ công dưới đây.)

**Frontend**
```bash
cd /Users/sapo/invoice/sapo-frontend-v3
npm run lint:fix
npm run type-check
```

**Test thủ công — nhóm cấu hình (A1-A2, B2)**
- [ ] Bật `separate_line`, để trống "Tên dòng phí trên hóa đơn", bấm lưu → **chặn lưu**, báo đúng "Vui lòng nhập tên dòng phí trên hóa đơn." (cả FE lẫn gọi thẳng API để verify BE cũng tự chặn, không chỉ FE)
- [ ] Nhập tên > 255 ký tự → chặn lưu, báo đúng "Tên dòng phí tối đa 255 ký tự."
- [ ] Chọn `none` → 2 control mới (tên dòng phí, checkbox điều chỉnh) và 2 dòng cảnh báo đều ẩn

**Test thủ công — nhóm dựng dòng phí (A4-A6, A9)**
- [ ] Tenant `shipping_fee_mode=none` (mặc định) + order có `delivery_fee` → tạo draft, hóa đơn **không** có dòng phí (hành vi hiện tại giữ nguyên)
- [ ] Set `separate_line` + tên dòng phí tùy chỉnh (vd "Cước vận chuyển"), provider = Sapo Invoice, order có `delivery_fee.fee > 0` → tạo draft → có đúng 1 dòng tên **đúng như đã cấu hình** (không phải "Phí giao hàng" cứng), `item_type=1`, `tax_name=KCT`, `amount` = đúng `fee`, cộng đúng vào tổng
- [ ] Đổi `shipping_fee_item_name` sang tên khác **sau khi** hóa đơn trên đã tạo → mở lại hóa đơn cũ, dòng phí **vẫn giữ tên cũ** (snapshot, BR02/BR05) — chỉ hóa đơn tạo mới sau đó dùng tên mới
- [ ] Order có `delivery_fee.fee = 0` → vẫn tạo dòng phí 0đ (BR07), không lỗi
- [ ] Order **không có** `delivery_fee` (null) → không tạo dòng phí, không lỗi
- [ ] Provider ≠ Sapo Invoice (dù order có `delivery_fee` và `separate_line`) → không tạo dòng phí (BR09)
- [ ] Auto Invoice tạo draft (không qua form thủ công) cũng có dòng phí đúng như luồng thủ công
- [ ] Publish hóa đơn có dòng phí VC sang Sapo Invoice — dòng phí xuất hiện trong payload gửi đi, số tiền khớp

**Test thủ công — nhóm đổi provider khi sửa (A7, B4)**
- [ ] Sửa hóa đơn draft đang có dòng phí VC, đổi provider sang MeInvoice/SInvoice/VnInvoice → dòng phí biến mất khỏi FE ngay (chưa cần lưu); **lưu xong**, gọi lại GET → dòng phí thật sự không còn trong `line_items[]` (verify guard backend hoạt động, không chỉ ẩn ở FE)
- [ ] Từ trạng thái trên, đổi ngược lại provider = Sapo Invoice (chưa reload trang) → dòng phí xuất hiện lại đúng số tiền cũ, lưu thành công
- [ ] Mở 1 hóa đơn **không** có dòng phí VC từ đầu (vd tạo lúc `shipping_fee_mode=none`), đổi qua lại provider → **không** tự sinh dòng phí mới (BR02)

**Test thủ công — nhóm điều chỉnh tự động (A8, MỤC MỚI, cần dữ liệu test có Auto Invoice + Auto Adjustment bật sẵn)**
- [ ] `auto_adjust_shipping_fee` **bỏ tích** (mặc định) → hóa đơn gốc có dòng phí VC, khi hệ thống tự tạo hóa đơn điều chỉnh (đơn trả/hủy, `AutoAdjustmentInvoiceEnabled=1`) → hóa đơn điều chỉnh **KHÔNG** có dòng phí VC, tổng tiền điều chỉnh không gồm phần phí
- [ ] Tích `auto_adjust_shipping_fee` → cùng kịch bản trên → hóa đơn điều chỉnh **CÓ** dòng phí VC, giá trị **âm** (ghi âm cùng các dòng khác — verify `applyNegativeSignToAdjustmentAutoDraft` áp đúng cho dòng này)
- [ ] Hóa đơn gốc **không** có dòng phí VC (order không có `delivery_fee`, hoặc `shipping_fee_mode=none` lúc tạo) → hóa đơn điều chỉnh cũng không có, bất kể `auto_adjust_shipping_fee` bật hay tắt (không có gì để lọc)

# Ràng buộc

- **KHÔNG chạy `git add` / `git commit`** — để nguyên unstaged, tôi tự review rồi tự stage.
- **CÓ migration lần này** (`V8__add_is_shipping_line_to_einvoice_lineitems.sql`, mục A6) — khác v0.5, đã đổi quyết định sau khi phát hiện không có cách an toàn nhận diện dòng phí VC nếu không có field riêng. Nhớ báo người quản lý deploy chạy tay (Flyway không tự áp dụng — xem "Đọc trước khi code").
- **KHÔNG sửa** `SapoInvoiceService.java:677` (hardcode `setItemType("products")`) — thuộc epic khác (&46), ngoài phạm vi task này dù có liên quan.
- **KHÔNG tự đổi** `OrderResponse.deliveryFee`/`OrderDomain.deliveryFee` từ object đơn sang `List` — giữ nguyên shape hiện tại cho tới khi có xác nhận từ BA/Omni (B0, xem đầu file).
- **KHÔNG động vào field `item_type` ở FE** (`FormEinvoice.tsx:921`, đang chứa `variant.product_type`) — xung đột đã biết thuộc epic &46, không tự "tiện tay sửa luôn". Task này dùng `is_shipping_line` để né hẳn field này.
- **KHÔNG thêm field `is_shipping_line`/tương đương vào `SapoInvoiceLineItem.java`** (payload gửi Sapo Invoice) — chỉ là marker nội bộ.
- Comment code: tiếng Việt cho logic nghiệp vụ, technical term giữ tiếng Anh (đúng convention repo).
- Không thêm test tự động ngoài phạm vi trên trừ khi tôi yêu cầu thêm.
- Nếu phát hiện chỗ nào lệch so với mô tả trên (số dòng đã trôi, hàm không tồn tại đúng tên) → **dừng lại báo tôi**, không tự suy diễn sửa bừa.
````

---

## Ghi chú khi dùng

- **Chưa chạy prompt này.** Trước khi chạy, cân nhắc xác nhận B0 (shape `delivery_fee`) với BA/Omni — SRS v0.6 không đề cập vấn đề này, vẫn là câu hỏi mở riêng.
- **Cập nhật 2026-08-12 theo SRS v0.6 (`invoice-docs!105`, đã merge/update mới nhất):** thêm 2 setting mới (`shipping_fee_item_name`, `auto_adjust_shipping_fee`), đổi marker từ ý tưởng ban đầu (`LineSource` string, tự đề xuất) sang đúng field SRS đã chốt (`is_shipping_line` boolean, BR10) — BA độc lập đi đến cùng kết luận "cần marker riêng" qua phân tích khác, khớp hướng kỹ thuật đã trace (đọc `edit()`, `buildAdjustmentLineItemsFromBaseline`, loại trừ `itemCode`/`item_name` làm nơi đánh dấu).
- **A8 (điều chỉnh tự động) là mục hoàn toàn mới** — v0.5 không có, chỉ nói chung chung "dòng phí chịu chung logic điều chỉnh". Đã trace kỹ: chỉ 1 điểm chèn (`buildAdjustmentLineItemsFromBaseline`), không phức tạp như lo ngại ban đầu.
- Phần A1-A7 (trừ đoạn `is_shipping_line`) đã đọc trực tiếp code thật, có số dòng chính xác tại thời điểm viết (2026-08-11/12) — nếu code đã đổi nhiều từ lúc đó, số dòng có thể trôi, nhưng tên hàm/field vẫn nên còn đúng.
