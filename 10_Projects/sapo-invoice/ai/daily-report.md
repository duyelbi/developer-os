---
created: 2026-09-10 08:35
scope: "Cách gom và viết daily report (standup) — Sapo Invoice"
---

# Daily report — Sapo Invoice

Khi Duy hỏi **daily report / standup / báo cáo hôm qua / hôm nay**, viết theo format dưới. **Ngắn gọn** — không liệt kê file, không tóm tắt dài, không bullet thừa.

Nguồn sự thật format: mẫu Duy chốt + template [[40_Templates/DailyReport]].

## Format bắt buộc

```
Hôm qua:
1. <Tên epic / feature>:
- <việc đã làm>
gap: <blocker nếu có>
2. <Epic tiếp>:
- <việc đã làm>
Hôm nay:
- <ưu tiên>
```

### Quy tắc viết

- Gom theo **epic / feature**, không theo repo hay commit
- Tên mục: ngắn, tiếng Việt, giữ thuật ngữ (`HĐĐC`, `MTT`, `consent`, `CR`)
- Mỗi bullet = 1 việc đã ship / đang làm — không giải thích dài
- Có blocker → thêm dòng `gap: …` ngay dưới epic đó
- **Hôm nay**: chỉ ưu tiên, không viết thành kế hoạch chi tiết
- Không bịa task — thiếu info thì hỏi hoặc ghi rõ giả định

## Ví dụ (chuẩn)

```
Hôm qua:
1. Popup xác nhận trách nhiệm khi lập HĐĐC MTT:
- xử lý Ghi consent sau khi tạo HĐĐC MTT thành công
gap: chờ PD chốt được nội dung của popup
2. [V2] Tự động tạo & phát hành HĐĐC cho đơn trả 1 phần:
- fix bug và comment
- xử lý phần CR FE để bắt buộc chọn Trạng thái đơn hàng khi bật Cài đặt tự động tạo và phát hành hóa đơn điều chỉnh
Hôm nay:
- ưu tiên fix bug và comment
- xử lý phần migration component DS mới cho các màn đơn giản.
```

## Cách gom dữ liệu (agent)

1. Xác định ngày: "hôm qua" = calendar day trước (giờ VN)
2. Commit author **Duy / DuyND7 / Nguyễn Đức Duy** trên các repo workspace (`invoice-app`, `admin-*`, `sapo-einvoice-service`, `sapo-frontend-v3`, …)
3. Agent transcripts / SearchConversations cập nhật trong ngày đó
4. Map việc → epic folder trong `10_Projects/sapo-invoice/epic-*` khi có (vd Epic #87, #80, #61)
5. Xuất đúng format trên — mặc định **chỉ title + bullet ngắn**; chỉ mở rộng nếu Duy yêu cầu

## Lưu sau khi báo cáo (tuỳ chọn)

Nếu Duy muốn giữ lại: tạo `60_Journal/YYYY-MM-DD.md` (ngày báo cáo), section Daily report, nội dung đúng format đã gửi.
