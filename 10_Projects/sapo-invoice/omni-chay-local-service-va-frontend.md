---
created: 2026-08-11 08:45
status: Implemented
project: "[[10_Projects/sapo-invoice/README]]"
---

# Chạy local `sapo-frontend-v3` (BE dùng staging)

Kiểm chứng thực tế trên máy `sapo` (macOS **arm64**) ngày 2026-08-11 — không phải chép từ README, vì README của cả hai repo đều lệch thực tế ở vài chỗ.

## Mô hình làm việc thực tế

**Chỉ chạy frontend ở local. Backend luôn dùng bản đã deploy trên staging** — không dựng `sapo-einvoice-service` trên máy.

```text
Browser                          Máy local                    Staging
https://phuongnt-dev2            webpack-dev-server           10.10.1.202
  .mysapo.vn:4200      ──────►   :4200                        :9765  Kong → einvoice-service
  /admin/dashboard               (proxy **.json)     ──────►  :8185  FE_X (login/oauth)
                                                              :8189  POS V2
```

Chạy: `npm run start-staging` (script `start-staging` → `env=staging` → `webpack/proxy.js` chọn nhóm target `10.10.1.202`).

→ **Không cần JDK 11, không cần config server, không cần SQL Server/Redis/Kafka/RabbitMQ trên máy.** Phần "chạy service local" bên dưới chỉ dùng khi thật sự cần debug backend bằng breakpoint — công việc hằng ngày không đụng tới.

---

## Frontend — chạy được, kể cả khi sai Node

### Nghịch lý Node version (quan trọng)

`package.json` ghim `volta.node = 14.17.0`. Nhưng:

- **Volta chưa cài** trên máy; `nvm` chỉ có **v24.16.0**
- **Node 14 không có bản darwin-arm64** — đã kiểm chứng: `node-v14.17.0-darwin-arm64.tar.gz` → **HTTP 404**, chỉ có `darwin-x64` → HTTP 200. Muốn đúng 14.17.0 trên máy M-series phải chạy qua Rosetta (`arch -x86_64`).
- **Nhưng thực tế `npm start` chạy ngon trên Node 24.16.0** — đã verify: webpack listen `:4200`, `GET /` trả **HTTP 200** kèm HTML SPA, proxy hoạt động.

→ **Đừng mất công cài Node 14.** Ghim Volta là di sản; webpack ở đây là `^5.74` nên không dính lỗi `ERR_OSSL_EVP_UNSUPPORTED` của Node 17+. `node_modules` sẵn có trong repo cài bằng npm mới (`lockfileVersion: 3`).

### Setup thật của team (chốt bởi chủ máy 2026-08-11)

Host đích: **`https://phuongnt-dev2.mysapo.vn:4200/admin/dashboard`**, và **backend dùng staging**, không phải dev2.

```bash
# 1. Trỏ host về máy mình — BẮT BUỘC
sudo sh -c 'echo "127.0.0.1 phuongnt-dev2.mysapo.vn" >> /etc/hosts'

# 2. Cài dep (nếu node_modules chưa có)
cd /Users/sapo/invoice/sapo-frontend-v3 && npm ci

# 3. Chạy — trỏ backend staging
npm run start-staging
```

**Tại sao phải đúng subdomain, không dùng `localhost`:** hostname chính là định danh gian hàng (`{tên}-dev2.mysapo.vn` / `{tên}.mysapogo.com`) — hệ multi-tenant resolve tenant theo domain. Xác nhận gián tiếp: `src/page/Dashboard/.../banner_ifc_05_2022.json` là allow-list ~8600 domain gian hàng, trong đó có `tiennh-dev2.mysapo.vn` đúng dạng này. Base URL API cũng dựng từ `window.location` (`src/services/config.ts:5`) chứ không đọc env.

> **Đính chính:** trước đó tôi ghi "cookie phiên đặt ở first-party domain `.mysapogo.com` (`App.tsx:61`)" — **sai**. Dòng đó là config **CDP365 analytics**, và chỉ chạy khi `REACT_APP_ENV === "production"` với gói TRIAL. Không liên quan tới session.

### Tài khoản test (dev, được phép lưu)

- **Dev v2**: `http://phuongnt-dev2.mysapo.vn:4200/admin/dashboard`
- **Staging v2**: `https://phuongtestmposlogin-sapostaging.mysapogo.com/admin/dashboard`
- Đăng nhập (dùng chung, chưa rõ áp dụng cho cả hai hay chỉ staging): `0396451260` / `Invoice1234567@`
- **Portainer** (xem log container dev2): `http://192.168.12.70:9000/#!/home` — `admin` / `12345678`

### Hai thứ còn thiếu để URL đó chạy được

**1. `/etc/hosts` chưa có entry.** Hiện chỉ có `192.168.12.72 phuongnt-dev2.mysapogo.com` — khác domain (`.com` vs `.vn`) và trỏ ra **máy dev2 ở xa**, không phải dev server local. Cần thiết vì `*.mysapo.vn` có **wildcard DNS công khai** trỏ về Cloudflare (`172.66.165.147`, `104.20.29.250`) — không thêm hosts entry thì trình duyệt đi ra Internet chứ không vào máy mình. (Cloudflare cũng không proxy HTTPS ở port 4200.)

**2. Dev server chưa bật HTTPS.** `webpack-dev-server` **4.15.2**, và `webpack/webpack.dev.js` **không có** `server`/`https`/cert nào; `git status` sạch (không có config HTTPS chưa commit), repo cũng không có file `.pem`/`.crt`. Mặc định wds v4 chỉ serve **HTTP** → gõ `https://…:4200` sẽ fail. Muốn HTTPS phải thêm vào `devServer`:

```js
server: {
  type: "https",
  options: { key: "…/localhost-key.pem", cert: "…/localhost.pem" },  // vd. tạo bằng mkcert
},
```

### Ngoại lệ: trang QR không cần login

Route `/sapo_invoice/qr/:token` và `/invoice_qr/:id` nằm trong `PUBLIC_ROUTES` → test được mà không cần session, tiện khi làm luồng QR.

---

## (Tùy chọn) Chạy service local — chỉ khi cần debug backend bằng breakpoint

Không thuộc luồng làm việc hằng ngày (xem "Mô hình làm việc thực tế" ở đầu note). Ghi lại vì nếu có lúc cần thì đây là 3 chỗ sẽ vấp.

### Chặn 1: Java 17 không compile được

Máy chỉ có JDK **17.0.19** (Homebrew, đang là `JAVA_HOME`) và **22.0.2** (Temurin). Chạy `mvn compile` fail:

```
Fatal error compiling: java.lang.ExceptionInInitializerError:
Unable to make field private com.sun.tools.javac.processing.JavacProcessingEnvironment$DiscoveredProcessors
... accessible: module jdk.compiler does not "opens com.sun.tools.javac.processing" to unnamed module
```

Lỗi kinh điển của annotation processor (Lombok/MapStruct đời cũ) gặp module system JDK 16+. **Không né bằng `--add-opens` cho gọn** — cài JDK 11 là đúng hướng:

```bash
brew install openjdk@11
export JAVA_HOME=/opt/homebrew/opt/openjdk@11
mvn -s .m2/settings.xml clean package -DskipTests
```

### Chặn 2: Maven cần `settings.xml` của repo

`~/.m2/settings.xml` **không tồn tại**. Repo có sẵn `.m2/settings.xml` trỏ nexus nội bộ `https://nexus.sapocorp.net/repository/maven-releases/` — nơi chứa parent POM `sapo-dependencies:2.0.4` và `sapo-common:1.5.9-rc1`.

→ **Luôn thêm `-s .m2/settings.xml`**, hoặc copy 1 lần: `cp .m2/settings.xml ~/.m2/settings.xml`. Đã verify `mvn -s .m2/settings.xml validate` → BUILD SUCCESS (resolve được parent POM nội bộ).

### Chặn 3: Config server — `failFast: true`

`bootstrap.yml` mặc định trỏ `http://sapo-config-server:8888`, hostname này **không có trong `/etc/hosts`** → app chết ngay lúc khởi động. Hai cách:

```bash
# Cách A (gọn nhất): dùng profile dev2 — bootstrap.yml đã ghi sẵn IP thật
mvn -s .m2/settings.xml spring-boot:run -Dspring.profiles.active=dev2   # → 192.168.12.72:8888

# Cách B: giữ profile local, map hostname
sudo sh -c 'echo "192.168.12.72 sapo-config-server" >> /etc/hosts'
mvn -s .m2/settings.xml spring-boot:run -Dspring.profiles.active=local
```

Profile có URI tường minh trong `bootstrap.yml`: `dev2` → `192.168.12.72:8888`, `dev1_debug` → `192.168.12.71:8888`, `staging_debug` → `10.10.1.202:9888`, `live_test` → `10.10.2.87:8888`. Các profile còn lại (`local`, `dev`, `staging`, `live`) dùng hostname mặc định.

**Hệ quả:** toàn bộ DB/Redis/Kafka/RabbitMQ đều lấy từ config server → "chạy local" thực chất là chạy code local đâm vào **hạ tầng dev2**. Không cần dựng SQL Server/Kafka/Redis trên máy.

Chạy xong log hiện `SAPO APPLICATION STARTED`; health: `curl http://localhost:8080/actuator/health` (port thật do config server quyết định).

### README của repo sai 2 chỗ

- Ghi cần **PostgreSQL 13+**, và ví dụ override `application-local.yml` dùng `jdbc:postgresql://...` — DB thật là **SQL Server**, xem [[10_Projects/sapo-invoice/omni-einvoice-service-tong-quan]]
- Ghi "Java 11 **or higher**" — thực tế **phải đúng 11**, 17 không compile được

---

## ⚠️ Staging không truy cập được từ mạng hiện tại

Team dùng **backend staging** (`npm run start-staging` → proxy tới `10.10.1.202`). Đo lại 2 lần bằng `curl` ngày 2026-08-11: **toàn bộ port staging đều connection-refused ngay lập tức** (`connect=0.000000s`, không phải timeout):

| Port staging | Vai trò | |
|---|---|---|
| 9765 | Kong `SAPO_API` | ❌ |
| 9888 | Config server | ❌ |
| 8189 | POS V2 | ❌ |
| 8185 | `SAPO_FE_X` | ❌ |

→ **Phải bật VPN công ty** thì `npm run start-staging` mới gọi được API. Mạng hiện tại chỉ thông dev2 (`192.168.12.72`).

## Trạng thái hạ tầng dev2 (đo 2026-08-11, `192.168.12.72`)

| Port | Vai trò | Trạng thái |
|---|---|---|
| 8888 | Spring Cloud Config Server | ✅ UP |
| 8765 | Kong gateway = `SAPO_API` | ✅ UP |
| 8189 | POS V2 | ✅ UP |
| **8185** | **`SAPO_FE_X`** — legacy FE, giữ login/oauth/session | ❌ **DOWN** (connection refused) |

Kiểm chứng route qua gateway:

| Endpoint | Kết quả | Nghĩa |
|---|---|---|
| `/admin/einvoices.json` | **401** | route sống, service einvoice OK, chỉ thiếu auth |
| `/admin/products.json` | 401 | sống |
| `/admin/orders.json` | 412 | sống (thiếu precondition header) |
| `/admin/session.json` | **502** | Kong trả — upstream session đang chết |

⚠️ **8185 down + session.json 502 ⇒ luồng đăng nhập đang hỏng ở dev2.** FE chạy được và gọi được API hóa đơn, nhưng không lấy được session để qua `AuthGuardRoute`. Nếu gặp cảnh "mở lên bị đá về login mãi" thì **không phải lỗi setup máy** — hỏi team hạ tầng bật lại FE_X.

Bản thân `sapo-einvoice-service` trên dev2 **vẫn khỏe** — log khởi động thành công 08:28:12 ngày 2026-08-11 (có graceful shutdown lúc 08:27 ngay trước đó, tức vừa redeploy).

### Cách đo cổng cho đúng

- **Đừng probe Kong bằng `/`** — `http://192.168.12.72:8765/` lúc trả 404, lúc trả 000, trong khi `/admin/einvoices.json` vẫn ổn định 401. Luôn probe bằng **đường dẫn thật**.
- **Đừng dùng `nc`** — cho kết quả chập chờn ở mạng này (cùng một cổng, lần OK lần FAIL).
- Dùng `curl -sv` và đọc dòng kết nối để phân biệt cho chắc:
  - `Connected to … port 8765` + `HTTP/1.1 401` → service sống, chỉ thiếu auth
  - `connect to … port 8185 failed: Connection refused` → thật sự không có gì lắng nghe

`nc`/`curl` tới `10.10.1.202` (staging) fail → staging không truy cập được từ mạng hiện tại, chỉ dev2 thông.

---

## ⚠️ Secret commit thẳng vào repo

Không phải việc cần sửa ngay, nhưng nên biết:

- `sapo-frontend-v3/.npmrc` — chứa **GitLab deploy token** (`_authToken=gldt-…`) cho registry `@sapo-presentation`
- `sapo-einvoice-service/src/main/resources/bootstrap.yml` — chứa **user/password basic auth** (`sapo/123456` cho config server, cùng 4 tài khoản `sapo`/`sapoweb`/`sapoexpress`/`digital_finance` kèm password và apiKey plaintext)

Cả hai đều đang nằm trong lịch sử git. Đừng copy các file này ra ngoài, đừng dán nội dung vào chat/issue/artifact.

---

## Cập nhật phiên làm việc khác cùng ngày (2026-08-11, chiều) — có điểm mâu thuẫn với phần trên

Một phiên Claude Code khác (không đọc note này trước khi bắt đầu) đã đi lại gần như toàn bộ hành trình debug ở trên nhưng **từ hai giả định sai** — ghi lại để không lặp lại:

- **Đã cài Node 14.17.0 qua Rosetta** (`arch -x86_64 zsh` → `nvm install 14.17.0` → tải bản `darwin-x64`) vì tưởng bắt buộc theo `volta.node` trong `package.json`. Theo phần "Nghịch lý Node version" ở trên, việc này **không cần thiết** — Node 24 đã chạy được. Chưa verify lại xem cài Node 14 có gây tác dụng phụ gì không (chưa thấy dấu hiệu có).
- **Không biết domain đúng là `phuongnt-dev2.mysapo.vn`** ngay từ đầu, nên dò qua nhiều domain sai (`core2-dev2.mysapogo.com`, `phuongnt-dev2.mysapogo.com`...) đều ra "Sorry, the store doesn't exist", cuối cùng "trúng" một domain khác — `phuongtestmposlogin-sapostaging.mysapogo.com` (map `127.0.0.1`) — chạy được với `npm run start-staging`. Đây nhiều khả năng là tenant test **khác**, không phải tenant chính `phuongnt-dev2`. **Chưa thử lại** `phuongnt-dev2.mysapo.vn:4200` với `npm run start-staging` để xác nhận tenant chính cũng chạy được qua staging backend — nên làm việc này trước khi coi note này là chốt.

### `/etc/hosts` đầy đủ hơn, lấy từ máy đồng nghiệp

Phiên đó nhận được nguyên file `/etc/hosts` mẫu của team (không chỉ 1-2 dòng), áp dụng đủ 5 nhóm:

```
# Service nội bộ dev backend (Kong, Redis, Unleash, config server...)
192.168.12.72 sapo-swarm-prod.local sapo-kong sapo_redis-session-ha sapo-redis-session-ha sapo-unleash sapo-config-server sapo-api sapo-redis-session

# Frontend local (npm start / npm run start-staging) — domain .mysapo.vn -> máy mình
127.0.0.1 thuongpd-dev2.mysapo.vn hoatest-dev2.mysapo.vn hoamy-dev2.mysapo.vn trongns99-dev2.mysapo.vn trong28-dev2.mysapo.vn phuongnt-dev2.mysapo.vn tphuongtest-dev2.mysapo.vn money-message-staging.sapoapps.vn phuongtestmposlogin-sapostaging.mysapo.vn

# Kong gateway dev bên ngoài
118.70.186.143 sapo-dev-kong-2.mysapo.vn sapo-dev-kong-1.mysapo.vn sapo-dev-swagger.mysapo.vn

# Domain .mysapogo.com -> trỏ THẲNG server dev2 thật (không phải máy mình) — để so sánh với bản local khi cần
192.168.12.72 hoatest-dev2.mysapogo.com thuongpd-dev2.mysapogo.com hoamy-dev2.mysapogo.com trongns99-dev2.mysapogo.com trong28-dev2.mysapogo.com phuongnt-dev2.mysapogo.com tphuongtest-dev2.mysapogo.com

# Cổng thanh toán Napas (staging)
192.168.68.114 apg-stg.napas.com.vn
```

Điểm cần nhớ: **`.mysapo.vn` và `.mysapogo.com` là hai domain khác nhau cho cùng tên tenant**, dùng cho hai mục đích khác nhau — `.mysapo.vn` trỏ về máy mình (frontend local), `.mysapogo.com` trỏ thẳng server dev2 (`192.168.12.72`, bản đã deploy sẵn, không phải code local). Nhầm domain là nguyên nhân chính gây "store doesn't exist" ở trên.

## Liên kết

- [[10_Projects/sapo-invoice/omni-einvoice-service-tong-quan]]
- [[10_Projects/sapo-invoice/omni-frontend-v3-einvoice-tong-quan]]
