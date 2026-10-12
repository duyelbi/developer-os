---
created: 2026-10-12
status: FE Task 1–4 đã code local (2026-10-12); Task 4 chờ BE listDelta; Task 5 đã điều tra, chưa gọi thử dev
project: "[[10_Projects/sapo-invoice/README]]"
epic: "[[epic-100-plan]]"
---

# FE #24 — Popup "Chi tiết hoạt động": xử lý gap sau khi BA trả lời

Plan cho Cursor làm tiếp. Bối cảnh đầy đủ ở [[epic-100-plan]].

## Bối cảnh nhanh

- Repo `~/invoice/sapo-invoice-admin-frontend`, nhánh `feat/activity-log-screen`. Commit mới nhất `7e73963a` đã push.
- MR [!424 → master](https://git.dktsoft.com:2008/sapo-money/sapo-invoice/sapo-invoice-admin-frontend/-/merge_requests/424) còn mở. !427 → dev đã merge, nên commit mới cần **MR mới vào dev**.
- Màn dùng **thư viện cũ `@sapo/ui-components`** (đã chốt). **Không** migrate sang DS trong việc này.
- Code popup nằm ở `src/pages/setting/pages/activity-log/`:
  - `components/ActivityLogDetailModal.tsx`: khung popup, khối Thiết bị, Thông tin thao tác, Nội dung chi tiết;
  - `components/ActivityLogChangesTable.tsx`: bảng Nội dung thay đổi;
  - `utils/activityLogDetail.ts`: các dòng Nội dung chi tiết và nhãn trạng thái;
  - `utils/activityLogChanges.ts`: gom nhóm thay đổi, delta của trường danh sách;
  - `utils/permissionLabels.ts`: nhãn quyền lấy từ `user-permission/constants`;
  - `utils/activityLog.test.ts`: test (đang 104/104).
- Quy ước repo: đọc `.claude/commands/review-code.md` trước khi sửa. Xong việc chạy `pnpm lint:fix && pnpm format`, rồi `pnpm lint`, `pnpm typecheck`, `pnpm test` phải xanh.
- Commit **không** thêm `Co-Authored-By` hay footer "Generated with …". Không commit `.claude/launch.json`.

## Câu trả lời của BA (2026-10-12)

| Mục   | Câu hỏi                                        | BA chốt                                                                 | Việc cần làm                          |
| ----- | ---------------------------------------------- | ----------------------------------------------------------------------- | ------------------------------------- |
| A1–A5 | Các mục FE tự chốt                             | **Đồng ý đề xuất**                                                      | Task 1, Task 2. A2, A3, A4 giữ nguyên |
| B1    | Link đối tượng mở cùng tab hay tab mới         | **Cùng tab**, cho đồng bộ với V3                                        | Task 3 (chỉ kiểm, gần như không sửa)  |
| B2    | Trường danh sách (quyền, vai trò)              | **Theo Figma: hiện danh sách cũ → mới đầy đủ**                          | Task 4, **cần BE đổi dữ liệu**        |
| B3    | Khung sửa hóa đơn, trạng thái thất bại, mobile | Đang chờ chốt thiết kế                                                  | Không làm, chỉ theo dõi               |
| B4    | Lỗi vẽ trong Figma                             | — (bỏ qua)                                                              | Không làm                             |
| B5    | Khối Thiết bị khi actor là đối tác OAuth2      | SI có lấy được **IP thật của máy chủ đối tác** không? **Điều tra thêm** | Task 5 (điều tra, chưa code)          |

A2, A3, A4 giữ nguyên:

- A2: Esc và bấm ra ngoài vẫn đóng popup (mặc định của `Modal`).
- A3: "Xem kết quả xử lý" mở danh sách `/admin/settings/import_export_histories`. Giữ TODO B10.
- A4: bảng thay đổi cuộn ngang trên mobile.

---

## Task 1 — A1: nhãn cho quyền Tờ khai thuế / TVAN (FE, khoảng 30 phút)

**Vấn đề.** `formatPermissionCodes` và `getPermissionDeltaLabels` lấy nhãn từ `defaultColumnsPermission` của màn Phân quyền. Màn đó không có nhóm quyền tờ khai/TVAN, nên popup hiện mã thô (`read_tax_declaration`…) trong nhóm "Khác".

**Mã còn thiếu.** Lấy bằng cách so `PermissionConst.java` (admin-service `origin/dev`) với `user-permission/constants.ts`. **Phải kiểm lại từng mã**, vì có chuỗi trong `PermissionConst` có thể không phải mã quyền:

```
change_registration, create_tax_forms, create_tax_registration, create_tvan_registration,
delete_tax_forms, import_tax_declaration_xml, read_tax_declaration, read_tax_forms,
read_tax_registration, sign_tax_declaration, sign_tax_registration, sign_tvan_registration,
stop_declaration, terminate_registration, update_tax_forms, update_tax_registration,
update_tvan_registration, view_tvan_registration
```

**Cách làm.**

1. Tìm tên tiếng Việt của từng mã, theo thứ tự ưu tiên:
   1. màn hoặc menu nào trong SI đang hiển thị quyền đó (grep `src/` theo mã, kể cả `Permissions.*` trong `src/constants`);
   2. comment trong `PermissionConst.java`;
   3. tài liệu `invoice-docs`.
      Không tìm được thì **để trống và liệt kê ra cho user hỏi PO**. Không tự đặt tên.
2. Trong `utils/permissionLabels.ts`, thêm một bảng nhãn bổ sung (ví dụ `extraPermissionGroups`, cùng dạng `{ groupName, columns: [{ key, label }] }`). Nạp sau `defaultColumnsPermission` để thứ tự nhóm nằm cuối.
   **Không sửa `user-permission/constants.ts`**, vì sửa ở đó sẽ làm màn Phân quyền hiện thêm checkbox.
3. Thêm test trong `activityLog.test.ts`: một mã tờ khai hiện ra "Nhóm – Tên", không còn mã thô.

**Done khi:** popup vai trò có quyền tờ khai/TVAN không còn hiện mã thô (trừ mã chưa có tên, đã báo user).

## Task 2 — A5: nhãn trạng thái biên bản (FE, khoảng 15 phút)

**Hiện trạng.** `statementStatusLabels` trong `utils/activityLogDetail.ts` có hai nhãn tự đặt: `seller_signing` → "Bên bán đang ký" và `buyer_signing` → "Bên mua đang ký".

- SI không có map nhãn trạng thái biên bản để đối chiếu: `src/pages/invoice-statement/constants.ts` chỉ có enum `StatementStatusEnum`.

**Cách làm.**

1. Đối chiếu với SRS:
   - `invoice-docs/docs/invoice/nhat-ky-hoat-dong/su-kien-a4-*.md` (Danh mục sự kiện A.4.2);
   - `bang-tong-hop-thao-tac.md`;
   - Excel `tong-hop-lich-su-hoat-dong.xlsx`.
     Kéo `invoice-docs` mới nhất trước khi đọc.
2. Tài liệu có chữ khác thì sửa cho khớp chữ tài liệu. Tài liệu không có thì giữ, và thêm một dòng comment: `// Tự đặt — SRS A.4.2 chỉ nêu draft/seller_signed/sent_buyer/buyer_signed`.

**Done khi:** nhãn khớp tài liệu, hoặc đã ghi rõ lý do giữ.

## Task 3 — B1: link mở cùng tab (FE, chỉ kiểm)

BA chốt **cùng tab**, khớp code hiện tại.

**Cách làm.** Kiểm `app/components/Link` (component dùng trong `ActivityLogDetailModal` và `ActivityLogTimeline`):

- không có `external` hoặc `target="_blank"`;
- điều hướng kiểu SPA, không tải lại trang.

Bấm link trong popup thì route đổi và popup tự unmount theo trang. Kiểm thêm: bấm Back của trình duyệt có quay về màn nhật ký không.

**Ghi chú UX (không làm).** Quay lại thì danh sách đã "Xem thêm" bị mất (cursor nằm trong state). Chỉ ghi lại để báo user, không tự lưu cursor vào URL.

**Done khi:** đã xác nhận hành vi, cập nhật comment hoặc TODO G7 nếu có. Không cần đổi code.

## Task 4 — B2: trường danh sách hiện đầy đủ cũ → mới theo Figma (BE + FE)

### Vì sao FE không tự làm được

BE đang ghi **delta** chứ không ghi danh sách đầy đủ. Ở admin-service `origin/dev`, `ConfigChangeLogWriter.listDelta(configKey, oldValues, newValues)` ghi:

- `old_value` = các mã bị **gỡ**;
- `new_value` = các mã được **thêm** (nối bằng `", "`).

Từ delta, FE không dựng lại được danh sách cũ và mới đầy đủ.

### Phần BE (của congnv, #18 nhóm Cấu hình). Cursor chỉ soạn tin nhắn, không sửa code BE

Nhờ congnv đổi `listDelta` (hoặc thêm hàm mới cho `permissions` và `roles`) để ghi:

- `old_value` = danh sách đầy đủ **trước** khi sửa;
- `new_value` = danh sách đầy đủ **sau** khi sửa;
- vẫn giữ quy tắc: hai danh sách bằng nhau (không đổi gì) thì không ghi dòng thay đổi.

Định dạng giữ nguyên chuỗi nối `", "` để FE không phải đổi `parseCodes`. Hỏi thêm congnv: dữ liệu delta cũ trên dev có cần chuyển đổi không (khả năng cao là không, vì chỉ là dữ liệu test).

**Soạn sẵn tin nhắn tiếng Việt cho user copy gửi congnv**, gồm: lý do (BA chốt theo Figma), file và hàm cần đổi, định dạng mong muốn.

### Phần FE (làm sau khi BE xác nhận định dạng; có thể code trước với test dữ liệu giả)

Ở `utils/activityLogChanges.ts`:

- Bỏ khái niệm `delta: { added, removed }`. Đổi thành `list?: { oldItems: string[]; newItems: string[] }`, mỗi vế qua `getPermissionDeltaLabels` / `parseCodes` như hiện tại.
- Đổi tên `listDeltaLabels` thành `listFieldLabels`. Sửa comment dòng 7 và 18 cho khớp nghĩa mới.

Ở `components/ActivityLogChangesTable.tsx`:

- Bỏ `DeltaItems` có dấu `+`/`−`.
- Cột "Giá trị cũ" hiện danh sách cũ, cột "Giá trị mới" hiện danh sách mới, mỗi mục một dòng.
- Danh sách rỗng hiện "-".
- **Mở Figma để lấy đúng cách trình bày danh sách** (có gạch đầu dòng không, khoảng cách giữa các dòng): file `7t7C9XzNP3nBJpBismG9zS`, frame bảng cấu hình node `598-21602`, popup node `35278-94701`.
  - Đọc bằng `use_figma` script read-only. `get_metadata` cả file quá lớn.

Test: thay các test delta `+/−` bằng test danh sách đầy đủ. Có một case vai trò và một case quyền, quyền sắp theo thứ tự màn Phân quyền.

**Rủi ro.** Nếu FE merge trước BE, dữ liệu delta cũ sẽ hiện thành "cũ = các quyền bị gỡ, mới = các quyền được thêm", tức là sai nghĩa. Vì vậy **merge FE cùng lúc hoặc sau BE**, và ghi rõ điều này trong MR.

**Done khi:** BE đã ghi danh sách đầy đủ trên dev, popup sửa vai trò hiện đúng cũ → mới như Figma, test xanh.

## Task 5 — B5: SI có lấy được IP thật của máy chủ đối tác OAuth2 không? (chỉ điều tra, chưa code)

**Câu hỏi của BA.** Khi đối tác tích hợp (actor `app`, tức OAuth2 client credentials) gọi API SI từ máy chủ của họ, `ip_address` trong nhật ký có phải IP thật của máy chủ đối tác không. Câu trả lời quyết định khối Thiết bị của actor `app` hiện gì (SRS câu E19).

**Điều đã biết (đã đọc code admin-service `origin/dev`):**

- Có 3 cách lấy IP:
  - `ActorHelper.getCurrentIpAddress()`: phần tử **đầu** của `X-Forwarded-For`, không có thì `request.getRemoteAddr()`;
  - `ConfigChangeLogWriter.currentHeader("X-Forwarded-For", true)`: giống trên;
  - `IpUtils.getRemoteIP` (lib `sapo-invoice-common`): dùng cho `RateLimitInterceptor` và `ConsentWriteService`. Chưa đọc logic.
- **Rủi ro:** phần tử đầu của `X-Forwarded-For` là **giá trị phía client tự gửi được**. Nếu gateway hoặc ingress chỉ _nối thêm_ vào XFF (không ghi đè), đối tác có thể gửi XFF giả và nhật ký ghi IP giả. IP đáng tin là phần tử do **proxy tin cậy gần nhất** thêm vào (đếm từ phải), hoặc header `X-Real-IP` do gateway đặt.
- `OAuthAuditService` (dòng khoảng 313–335) có ghi `ipAddress` cho audit OAuth. Cần xem nó lấy IP từ đâu.

**Các bước điều tra:**

1. Đọc `IpUtils.getRemoteIP` trong `~/invoice/sapo-invoice-libs/sapo-invoice-common` (hoặc jar trên Nexus) và nguồn `ipAddress` của `OAuthAuditService`.
2. Xác định đường đi request của đối tác OAuth2: domain, path (`/api/...` hay endpoint open API riêng), qua những tầng nào (Cloudflare/WAF? nginx? ingress? Spring Cloud Gateway?).
   - Tìm trong `~/invoice/dev-ops-config-override` (config gateway / route) và `~/invoice/servers`. Không thấy thì ghi câu hỏi cho DevOps/congnv.
3. Với từng tầng: tầng đó **ghi đè** hay **nối thêm** `X-Forwarded-For`, có đặt `X-Real-IP` không. Spring có bật `server.forward-headers-strategy` hoặc `RemoteIpValve` không (grep `forward-headers-strategy`, `remote-ip-header`, `internal-proxies` trong config-override và `application*.yml`).
4. Kiểm bằng dữ liệu thật trên dev, nếu có client OAuth2 test:
   - gọi một API ghi log (ví dụ tạo khách hàng) từ máy có IP public đã biết, so với `ip_address` trong `GET /api/activity_logs`;
   - gọi lại kèm header `X-Forwarded-For: 1.2.3.4` để xem có giả được không.
   - **Không tự nhập client secret.** Nhờ user chạy lệnh nếu cần token.
5. Kết luận, viết thành một mục trong [[epic-100-plan]]:
   - lấy được IP thật hay không, giả được hay không;
   - đề xuất cho E19: hiện IP (nếu tin được) + "Đối tác tích hợp: ‹tên app›", hoặc ẩn IP;
   - nếu cần sửa BE (lấy IP từ phải sang hoặc từ `X-Real-IP`) thì ghi rõ file, hàm và người phụ trách. Lỗi giả IP ảnh hưởng **mọi** actor, không chỉ OAuth2, nên báo cả congnv (#25 envelope IP/UA).
6. Soạn sẵn câu trả lời ngắn cho BA (tiếng Việt, không thuật ngữ quá sâu).

**Done khi:** có kết luận kèm bằng chứng (file:dòng, config, kết quả gọi thử) và tin nhắn trả lời BA. **Chưa sửa code FE** cho tới khi BA chốt cách hiển thị.

---

## Thứ tự đề xuất

1. Task 1 + Task 2 + Task 3: FE thuần, làm và commit chung một commit, ví dụ `fix(activity-log): nhãn quyền tờ khai/TVAN, nhãn trạng thái biên bản`.
2. Task 4: soạn tin nhắn cho congnv trước, rồi code FE trên nhánh và **chưa merge** khi BE chưa xong.
3. Task 5: điều tra song song, không đụng code.
4. Sau 1 và 4: mở **MR mới → dev** cho các commit từ `7e73963a` trở đi. Cập nhật mô tả !424 (bỏ đoạn mock / phân trang số trang, ghi "Xem thêm" + popup). Hỏi user trước khi tạo MR.

## Còn treo, không thuộc plan này

| Mục                                                                                    | Chờ ai           |
| -------------------------------------------------------------------------------------- | ---------------- |
| B3: khung popup sửa hóa đơn, trạng thái thất bại, mobile                               | PD (xamlt)       |
| Hóa đơn chưa có `detail`/`changes`/IP/UA, và phần "Không có thay đổi"                  | BE #19 (trongns) |
| Hàng hóa hệ thống tạo thiếu `object_code`/`detail`                                     | BE #21 (manhtv3) |
| `channel` luôn `null`                                                                  | BE #25 (congnv)  |
| Tên khóa `detail` lẫn camel/snake, khóa "Lý do"                                        | congnv           |
| #20 Xử lý HĐ: thiếu danh sách HĐ, HĐ gốc, lượt gửi–ký, email, chứng thư                | duynd7 (BE)      |
| Lưu bộ lọc thành tab · lọc Kết quả · "Hệ thống" trong Người thao tác · API list-actors | API (congnv #26) |
