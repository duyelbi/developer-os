---
created: 2026-08-07 00:00
status: Proposed — chưa sửa code
project: "[[10_Projects/sapo-invoice/README]]"
---

# Mã QR thanh toán — tăng quiet zone (QR thật 80×80 trong ảnh 100×100)

Branch liên quan: `feature/template-font-mau-qr` (có ở cả `sapo-invoice-admin-frontend` và `sapo-invoice-admin-service`).

## Yêu cầu

Ở màn "Thêm mới mẫu hoá đơn" → tab **Cấu hình chung** → **Mã QR**, ảnh QR trên preview hoá đơn giữ nguyên **100×100** (để layout không đổi), nhưng phần mã QR thật chỉ chiếm **80×80** ở giữa — phần còn lại là khoảng trắng.

## Ảnh QR sinh ở đâu (đã kiểm tra code, KHÔNG phải giả định)

Không phải frontend. PNG do backend sinh rồi trả base64 xuống:

- FE gọi `POST /api/templates/qr-preview` — `sapo-invoice-admin-frontend/src/pages/template/api.ts:100`, trả `QrPreviewResponse.qr_image_base64`.
- FE chỉ gắn `img.src = data:image/png;base64,...` — `src/pages/template/hooks/useQrPreviewRenderer.ts:218`. Ảnh hiển thị ở **kích thước tự nhiên**: `removeAttribute("width"/"height")` tại `useQrPreviewRenderer.ts:201-202`, có comment "để không làm nhòe module QR khi browser resize".
- BE sinh ảnh: `sapo-invoice-admin-service` → `src/main/java/vn/sapo/invoice/admin/invoice/application/service/qr/QrImageRenderer.java`.
- Kích thước 100 là hằng số `QR_DEFAULT_SIZE_PX = 100` ở `InvoiceQrService.java:26`, dùng ở 3 chỗ (dòng 112, 121, 129).
- Bản hoá đơn thật (không phải preview) dùng `QrHtmlInjector.java` — nếu đổi cách render phải kiểm tra luôn nhánh này.

## Vấn đề hiện tại

`QrImageRenderer.scaleToFill()` giãn ma trận QR **lấp đầy** toàn bộ `sizePx × sizePx`, nên không có khoảng trắng ngoài `MARGIN=2` mà ZXing đã nhúng sẵn trong ma trận.

## Cách sửa đề xuất

Vẽ ma trận vào ô `sizePx * 0.8` căn giữa trên nền trắng `sizePx`. Giữ nguyên chữ ký `renderPngBase64(payload, sizePx)` nên `InvoiceQrService` không phải đổi gì.

```java
// Ảnh vẫn sizePx để layout hoá đơn không đổi; QR thật chỉ chiếm QR_CONTENT_RATIO,
// phần còn lại là quiet zone trắng.
private static final double QR_CONTENT_RATIO = 0.8;

private BufferedImage scaleToFill(BitMatrix matrix, int sizePx) {
    var contentPx = (int) Math.round(sizePx * QR_CONTENT_RATIO);
    var offset = (sizePx - contentPx) / 2;
    var image = new BufferedImage(sizePx, sizePx, BufferedImage.TYPE_INT_RGB);
    for (int y = 0; y < sizePx; y++) {
        for (int x = 0; x < sizePx; x++) {
            var contentX = x - offset;
            var contentY = y - offset;
            var isInside = contentX >= 0 && contentX < contentPx && contentY >= 0 && contentY < contentPx;
            var isDark = isInside
                    && matrix.get(contentX * matrix.getWidth() / contentPx,
                                  contentY * matrix.getHeight() / contentPx);
            image.setRGB(x, y, isDark ? 0xFF000000 : 0xFFFFFFFF);
        }
    }
    return image;
}
```

Lưu ý: `BufferedImage.TYPE_INT_RGB` mặc định pixel đen, nên vòng lặp phải quét **toàn bộ** canvas và ghi trắng cho vùng ngoài — không được chỉ vẽ vùng QR.

## ⚠️ Rủi ro cần test trước khi chốt

Payload VietQR ~130 ký tự → ma trận cỡ **41×41 modules**, cộng `MARGIN=2` mỗi bên là **45×45**.

| Kích thước QR | px / module |
|---|---|
| 100px (hiện tại) | ~2.2 |
| 80px (sau khi sửa) | ~1.8 |

`scaleToFill` dùng nearest-neighbour, chia số nguyên → module sẽ méo không đều (chỗ 1px, chỗ 2px). Ở 100px đã méo sẵn, xuống 80px méo nặng hơn. **Phải test quét thật bằng app ngân hàng trên bản in PDF**, không chỉ nhìn trên màn hình.

## Hướng làm QR nét hơn (tách riêng, chưa quyết)

Render PNG ở **bội số nguyên** của kích thước ma trận (vd 45 × 8 = 360px) rồi để `<img>` hiển thị ở 100px:

- Module thành đúng 8px vuông vắn, không méo; PDF giữ nguyên độ phân giải khi in.
- Đổi kèm ở FE: bỏ `removeAttribute("width"/"height")` ở `useQrPreviewRenderer.ts:201-202`, set `width=100 height=100` tường minh.
- Đụng cả 2 repo → làm thành task riêng.

## Trạng thái

Chưa sửa gì. Repo `sapo-invoice-admin-service` lúc khảo sát đang checkout `feat/import-invoice-buyer-id-number`, code QR nằm ở `feature/template-font-mau-qr` — muốn sửa phải checkout branch đó hoặc tạo git worktree.
