# REPORT Frontend - TechRadar / TechPulse VN

## 1. Tong quan

Du an co hai frontend nam trong `src/frontend`:

- `src/frontend/web`: ung dung web React + Vite, la frontend day du nhat.
- `src/frontend/app`: ung dung mobile Expo / React Native, co the chay tren Android/iOS va web qua Expo Router.

San pham frontend huong toi mot nen tang phan tich xu huong cong nghe va thi truong tuyen dung IT Viet Nam. Cac chuc nang chinh gom dashboard xu huong cong nghe, so sanh cong nghe, truc quan hoa knowledge graph, phan cum cong nghe, AI Chat RAG, ho so nguoi dung va khu vuc quan tri.

Backend chinh ma frontend goi den la Golang API o `http://localhost:8080/api/v1`. Rieng web dev dung Vite proxy `/api/v1 -> http://localhost:8080`, con mobile dung URL tuy platform:

- Web trong Expo: `http://localhost:8080/api/v1`
- Android emulator: `http://10.0.2.2:8080/api/v1`

## 2. Frontend Web

Thu muc chinh: `src/frontend/web`

Cong nghe:

- React 19
- Vite 7
- React Router DOM 7
- Recharts cho bieu do dashboard/compare/admin
- react-force-graph-2d va D3 cho do thi
- react-select cho bo chon cong nghe
- html2canvas cho export PNG
- ESLint
- Docker multi-stage build voi Nginx

Scripts trong `package.json`:

- `npm run dev`: chay Vite dev server.
- `npm run build`: build production.
- `npm run lint`: lint source.
- `npm run preview`: xem ban build Vite.

### Routing web

File route chinh: `src/frontend/web/src/App.jsx`

Route public:

- `/login`: dang nhap.
- `/register`: dang ky.

Route nguoi dung nam trong `UserLayout`:

- `/`: redirect sang `/dashboard`.
- `/dashboard`: dashboard xu huong.
- `/compare`: so sanh cong nghe.
- `/graph`: kham pha knowledge graph.
- `/clusters`: dashboard phan cum cong nghe.
- `/chat`: AI Chat.
- `/profile`: ho so nguoi dung.

Route admin nam trong `AdminLayout`:

- `/admin`: redirect sang `/admin/dashboard`.
- `/admin/dashboard`: dashboard thong ke admin.
- `/admin/users`: quan ly nguoi dung.
- `/admin/cms`: co component nhung hien khong hien trong sidebar.
- `/admin/settings`: cau hinh he thong va feature flags.

Catch-all route redirect ve `/dashboard`.

### AppContext va feature flags

File: `src/frontend/web/src/contexts/AppContext.jsx`

Context luu cac trang thai:

- `isWebMaintenance`
- `isAppMaintenance`
- `isChatEnabled`
- `isGraphEnabled`

Mac dinh website duoc bat. Khi mount, frontend goi `GET /api/v1/status`, map response backend:

- `maintenance_web` -> `isWebMaintenance`
- `maintenance_mobile` -> `isAppMaintenance`
- `feature_graph` -> `isGraphEnabled`
- `feature_chat` va `feature_rag` -> `isChatEnabled`

Context dong bo status moi 30 giay va luu vao `localStorage` qua key `appSettings`.

### API client web

File: `src/frontend/web/src/utils/apiClient.js`

Dac diem:

- Base URL la `/api/v1`, dua vao Vite proxy hoac Nginx proxy.
- Tu dong gan `Authorization: Bearer <access_token>` neu co token trong `localStorage`.
- Kiem tra timeout phien 900 giay, tu dong xoa token va redirect ve `/login`.
- Neu HTTP 401 thi xoa token, thong bao het phien va redirect.
- Neu HTTP 503 thi nem loi `SERVER_MAINTENANCE`.
- Neu network fetch fail thi map thanh `SERVER_CONNECTION_FAILED`.

## 3. Cac man hinh web nguoi dung

### Dashboard xu huong

File: `src/frontend/web/src/pages/TrendDashboard.jsx`

Chuc nang:

- Goi `GET /radar/top4` de hien 4 cong nghe/nganh noi bat.
- Goi `GET /radar/top10` de lay danh sach top 10 cong nghe va tao options cho select.
- Goi `GET /compare/search?keywords=...&months=...` de ve timeline job postings.
- Ho tro chon nhieu cong nghe, khoang thoi gian 3/6/12/24 thang.
- Ho tro 3 che do bieu do: line, bar, growth percentage.
- Export CSV va PNG.
- Co UI rieng cho maintenance hoac loi ket noi server.

### So sanh cong nghe

File: `src/frontend/web/src/pages/ComparePage.jsx`

Chuc nang:

- Cho nguoi dung chon/toa moi cong nghe bang `CreatableSelect`.
- Gioi han toi da 5 cong nghe.
- Goi `/radar/top10` de lay goi y.
- Goi `/compare/search` de lay `yoy_rate`, `mom_rate`, `growth_rate` va monthly history.
- Ve bieu do tang truong % so voi thang dau tien co job count > 0.

### Graph Explorer

File: `src/frontend/web/src/pages/GraphExplorer.jsx`

Chuc nang:

- Dung `react-force-graph-2d` de ve knowledge graph.
- Mode `Khám phá`: goi `GET /graph/explore` voi `keywords`, `depth`, `location`, `min_salary`.
- Mode `Phân tích lộ trình`: goi `GET /graph/road_analysis?from=...&to=...`.
- Co search local tren nodes da load.
- Co depth 1 hop / 2 hops.
- Co reset, focus, hover node, click node, click edge.
- Co legend cho node types: technology, company, skill, location, industry, job.
- Co mau rieng cho relation types: USES, REQUIRES, LOCATED_IN, RELATED_TO, TAGGED_WITH.
- Neu `feature_graph` tat thi hien trang maintenance.

### Cluster Dashboard

File: `src/frontend/web/src/pages/ClusterDashboard.jsx`

Chuc nang:

- Goi `GET /clustering/clusters` de lay danh sach cum.
- Co search theo label, domain, sample technologies.
- Khi chon mot cum, goi `GET /clustering/clusters/{id}`.
- Man tong quan hien grid cac cum, so cong nghe, confidence, domain.
- Man chi tiet hien graph 1 cum bang `ForceGraph2D`: node trung tam la cluster, cac node con la technologies.
- Panel chi tiet hien domain, label, description, so member, confidence, cluster id, danh sach technologies.

### AI Chat

File: `src/frontend/web/src/pages/ChatbotPage.jsx`

Chuc nang:

- Tao session chat moi qua `POST /chat/session`.
- Lay danh sach session qua `GET /chat/sessions`.
- Lay lich su message qua `GET /chat/session/{session_id}/messages`.
- Gui tin nhan streaming qua `POST /chat/session/{session_id}/messages/stream`.
- Xu ly SSE bang `ReadableStream`, event `data:` co the la token text hoac JSON done co `answer`.
- Luu active session vao `localStorage` key `chat_session_id`.
- Co lich su chat, tao chat moi, xoa session khoi UI local.
- Render markdown don gian: heading, bullet, table, bold, italic, inline code.
- Neu `feature_chat` hoac `feature_rag` tat thi hien maintenance.
- Sau cau tra loi dai, co nut dieu huong sang Graph Explorer.

### Ho so nguoi dung

File: `src/frontend/web/src/pages/UserProfile.jsx`

Chuc nang:

- Goi `GET /user/profile`.
- Goi `PUT /user/profile` de cap nhat ho ten, bio, role cong viec, location, technologies va password neu co.
- Map du lieu linh hoat tu response dang `{ user, profile }` hoac flat object.
- Co che do xem/chinh sua, skeleton loading va toast.

### Auth

Files:

- `src/frontend/web/src/pages/auth/LoginPage.jsx`
- `src/frontend/web/src/pages/auth/RegisterPage.jsx`

Dang nhap:

- Goi `/status` truoc de lay maintenance/feature flags.
- Goi `POST /auth/login`.
- Luu `access_token`, `refresh_token`, `login_timestamp`.
- Goi `GET /auth/me` de lay role.
- Admin redirect sang `/admin`, user redirect sang `/dashboard`.
- Neu web maintenance va role khong phai admin thi chan dang nhap.

Dang ky:

- Goi `registerMock`, thuc te alias sang `registerUser`.
- Gui `full_name`, `email`, `password`, `confirm_password`.
- Thanh cong thi quay ve login.

## 4. Khu vuc Admin web

### Admin Layout

Files:

- `src/frontend/web/src/layouts/AdminLayout.jsx`
- `src/frontend/web/src/components/layout/AdminSidebar.jsx`

Admin co sidebar collapse/expand, responsive mobile header va logout. Sidebar hien:

- Dashboard
- Quan ly nguoi dung
- Cai dat he thong

Component CMS co ton tai nhung item CMS dang bi comment trong sidebar.

### Admin Dashboard

File: `src/frontend/web/src/pages/admin/AdminDashboard.jsx`

Chuc nang:

- Tong hop du lieu tu `adminService.fetchAdminDashboardStats`.
- Ben service goi song song:
  - `/admin/dashboard/monthly-visits`
  - `/admin/dashboard/searches-today`
  - `/admin/dashboard/top-keywords`
  - `/admin/dashboard/user-count`
  - `/admin/dashboard/visits-today`
- Hien card tong user, truy cap hom nay, luot tim kiem.
- Hien line chart luu luong va danh sach top keywords.
- Neu loi 401 thi thong bao het phien va chuyen ve login.

### Quan ly nguoi dung

File: `src/frontend/web/src/pages/admin/AdminUsers.jsx`

Chuc nang:

- `GET /admin/users`
- `POST /admin/users`
- `PUT /admin/users/{id}`
- `DELETE /admin/users/{id}`
- Co modal tao/sua user, role admin/user, status active/blocked.
- Khi tao user, reload danh sach de lay ID that tu backend.

### Cai dat he thong

File: `src/frontend/web/src/pages/admin/AdminSettings.jsx`

Chuc nang:

- `GET /admin/settings`
- `PUT /admin/settings/{key}`
- Map frontend key sang backend key:
  - `isWebMaintenance` -> `maintenance_web`
  - `isAppMaintenance` -> `maintenance_mobile`
  - `isGraphEnabled` -> `feature_graph`
  - `isChatEnabled` -> `feature_chat`
  - `isRagEnabled` -> `feature_rag`
- Hien toggle cho web maintenance, mobile maintenance, Graph Explorer va AI RAG.

Luu y: UI co state `isChatEnabled` nhung man hinh hien tai chi render toggle AI RAG, chua render toggle rieng cho `feature_chat`.

### CMS

File: `src/frontend/web/src/pages/admin/AdminCMS.jsx`

Trang CMS hien dang dung `MOCK_DATA`, chua goi API that. Cac nut Import, Them, Sua, Xoa hien moi la UI.

## 5. Layout, navigation va style web

Files quan trong:

- `src/frontend/web/src/components/layout/Header.jsx`
- `src/frontend/web/src/components/layout/Footer.jsx`
- `src/frontend/web/src/components/layout/AdminSidebar.jsx`
- `src/frontend/web/src/styles/global.css`

Header nguoi dung:

- Logo TechRadar.
- Nav: Radar, So sanh, Do thi, Cum Cong Nghe, AI Chat.
- Dropdown avatar goi `/user/profile`, co link profile, settings placeholder va logout.
- Logout goi `/auth/logout`, sau do xoa token va ve login.

Style:

- Theme chu dao la dark/monochrome.
- Global CSS dinh nghia token mau, radius, shadow, layout, card, button, badge, responsive utilities.
- Font Inter duoc import tu Google Fonts.

## 6. Build va deploy web

File: `src/frontend/web/Dockerfile`

Quy trinh:

1. Stage build dung `node:20-alpine`.
2. `npm ci`.
3. `npm run build`.
4. Copy `dist` sang `nginx:stable-alpine`.
5. Serve static files bang Nginx.

File: `src/frontend/web/nginx.conf`

Nginx:

- Serve SPA voi `try_files $uri $uri/ /index.html`.
- Proxy `/api` sang `http://techpulse-golang-api:8080`.
- Co endpoint test `/test`.
- Cache static assets 1 nam.

Luu y: `docker-compose.yml` root hien chua khai bao service frontend web, du Dockerfile va nginx.conf da san sang.

## 7. Frontend Mobile / Expo

Thu muc chinh: `src/frontend/app`

Cong nghe:

- Expo 54
- React Native 0.81
- React 19.1
- Expo Router 6
- AsyncStorage
- React Navigation tabs
- Ionicons
- react-native-gifted-charts
- react-native-webview
- expo-file-system va expo-sharing cho export CSV

Scripts:

- `npm start`: `expo start`
- `npm run android`
- `npm run ios`
- `npm run web`
- `npm run lint`

### Routing mobile

File: `src/frontend/app/app/_layout.tsx`

- Stack root gom `login`, `register`, `(tabs)`.
- Dung dark navigation theme.
- Co `MaintenanceOverlay`, nhung state `isMaintenance` dang hard-code `false`, chua dong bo global tu backend tai root.

File: `src/frontend/app/app/(tabs)/_layout.tsx`

Bottom tabs:

- `index`: Dashboard.
- `compare`: So sanh.
- `cluster`: Phan cum.
- `graph`: Do thi.
- `chat`: AI Chat.
- `profile`: Tai khoan.

### API client mobile

File: `src/frontend/app/utils/apiClient.js`

Dac diem:

- Dung AsyncStorage thay localStorage.
- Token luu qua `access_token`, `refresh_token`, `login_timestamp`.
- Session timeout 900 giay.
- Neu 401 thi xoa token va hien Alert.
- Base URL phu thuoc platform:
  - Web: `http://localhost:8080/api/v1`
  - Native Android emulator: `http://10.0.2.2:8080/api/v1`

## 8. Cac man hinh mobile

### Mobile Dashboard

File: `src/frontend/app/app/(tabs)/index.tsx`

Tuong tu web dashboard:

- Goi `/radar/top4`, `/radar/top10`, `/compare/search`.
- Hien top stats, chart line/bar/growth, top 10.
- Dung `react-native-gifted-charts`.
- Export CSV tren native bang FileSystem + Sharing.
- Export PNG chi ho tro web; native hien thong bao chua ho tro.

### Mobile Compare

File: `src/frontend/app/app/(tabs)/compare.tsx`

- Goi `/radar/top10` de lay options.
- Goi `/compare/search`.
- Hien cards YoY/MoM/growth va line chart tang truong %.
- Chon 2-5 cong nghe.

### Mobile Graph

File: `src/frontend/app/app/(tabs)/graph.tsx`

- Dung `WebView` chua HTML inline, HTML load force-graph tu `https://unpkg.com/force-graph`.
- Goi `/graph/explore` va `/graph/road_analysis`.
- Co 2 mode: explore va journey.
- Dong bo feature flag bang cach poll `/status` moi 30 giay; neu `feature_graph` false thi hien `MaintenanceOverlay`.

Luu y quan trong: Mobile Graph phu thuoc CDN `unpkg.com` trong WebView. Khi offline hoac bi chan network, graph co the khong hien.

### Mobile Cluster

File: `src/frontend/app/app/(tabs)/cluster.tsx`

- Goi `/clustering/clusters`.
- Search cum theo label, domain, sample tech.
- Khi chon cum, goi `/clustering/clusters/{id}`.
- Dung WebView/iframe voi force-graph tu CDN de ve graph cluster.

### Mobile Chat

Files:

- `src/frontend/app/app/(tabs)/chat.tsx`
- `src/frontend/app/services/chatService.js`

Chuc nang:

- Goi `/chat/session`, `/chat/sessions`, `/chat/session/{id}/messages`.
- Streaming SSE qua `/chat/session/{id}/messages/stream`.
- Luu active session vao AsyncStorage key `chat_session_id`.
- Co lich su chat, tao chat moi, xoa session trong local UI.
- Poll `/status` moi 30 giay; neu `feature_rag` hoac `feature_chat` false thi hien maintenance overlay.
- Render markdown don gian: heading, bullet, bold.

### Mobile Profile

File: `src/frontend/app/app/(tabs)/profile.tsx`

- Goi `/user/profile` de hien ten/email.
- Logout goi `/auth/logout`, xoa token AsyncStorage, ve `/login`.
- Co link sang `/personal-info`.

### Mobile Login/Register

Files:

- `src/frontend/app/app/login.tsx`
- `src/frontend/app/app/register.tsx`

Login:

- Goi `/status`, luu feature flags vao AsyncStorage.
- Chan login neu `maintenance_mobile` true.
- Goi `/auth/login`, luu token, timestamp va redirect sang tabs.

Register:

- Goi `/auth/register`.
- Validate day du field va confirm password.
- Thanh cong thi quay ve login.

## 9. API endpoints frontend dang dung

Auth va user:

- `POST /auth/login`
- `POST /auth/register`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET /auth/me`
- `GET /status`
- `GET /user/profile`
- `PUT /user/profile`

Radar / trend / compare:

- `GET /radar/top4`
- `GET /radar/top10`
- `GET /radar/search?keywords=...&months=...`
- `GET /compare/search?keywords=...&months=...`

Graph:

- `GET /graph/explore?keywords=...&depth=...&location=...&min_salary=...`
- `GET /graph/road_analysis?from=...&to=...`

Clustering:

- `GET /clustering/clusters?is_coherent=true`
- `GET /clustering/clusters/{id}`
- `POST /clustering/predict/batch`
- `GET /clustering/tech/{name}/cluster`

Chat:

- `GET /chat`
- `POST /chat/session`
- `GET /chat/sessions`
- `GET /chat/session/{session_id}/messages`
- `POST /chat/session/{session_id}/messages`
- `POST /chat/session/{session_id}/messages/stream`

Admin:

- `GET /admin/dashboard/monthly-visits`
- `GET /admin/dashboard/searches-today`
- `GET /admin/dashboard/top-keywords`
- `GET /admin/dashboard/user-count`
- `GET /admin/dashboard/visits-today`
- `GET /admin/settings`
- `PUT /admin/settings/{key}`
- `GET /admin/users`
- `POST /admin/users`
- `PUT /admin/users/{id}`
- `DELETE /admin/users/{id}`

## 10. Diem dang chu y / rui ro

1. Web README van la README mac dinh cua Vite, chua mo ta frontend that.

2. README root noi frontend la Next.js 15, nhung code hien tai la React + Vite cho web va Expo cho app. Bao cao nay dua tren code thuc te.

3. Mot so text tieng Viet trong file doc/code khi doc bang PowerShell bi hien mojibake. Kha nang cao la van de encoding hien thi, nhung nen kiem tra editor/UTF-8 de dam bao UI khong bi loi font.

4. Web admin CMS hien la mock, chua co API integration va chua hien trong sidebar.

5. Mobile root maintenance overlay dang co state hard-code `false`; tung tab rieng co poll `/status` cho graph/chat, nhung mobile app chua co global maintenance sync tai root.

6. Session timeout 15 phut duoc implement o ca web va mobile. Tuy nhien mobile khi timeout chi Alert va comment can navigation ve login o cap UI, chua co event/navigation tap trung.

7. Graph tren mobile va cluster mobile load `force-graph` tu CDN trong WebView/iframe. Day la diem phu thuoc network ben ngoai.

8. Web Chat co ham `saveSessionsList` duoc goi trong `clearSession`/`deleteSession` nhung trong file `ChatbotPage.jsx` khong thay dinh nghia ham nay. Day la loi runtime tiem an khi tao chat moi/xoa session.

9. `chatMock.js` van con trong web va app, nhung luong chinh dang dung API that.

10. Dockerfile frontend web da san sang, nhung `docker-compose.yml` root chua include service frontend.

11. Web `RegisterPage.jsx` comment noi dung "mock", nhung `registerMock` thuc chat alias `registerUser`, co the gay hieu nham.

12. Mobile va web co nhieu service API trung lap (`api/` va `services/` trong mobile). Can can nhac chuan hoa neu tiep tuc phat trien.

## 11. Cach chay nhanh

Chay web frontend:

```bash
cd src/frontend/web
npm install
npm run dev
```

Backend can chay o port `8080` de Vite proxy `/api/v1` hoat dong.

Build web:

```bash
cd src/frontend/web
npm run build
```

Chay mobile Expo:

```bash
cd src/frontend/app
npm install
npm start
```

Neu chay Android emulator, app se goi backend qua `http://10.0.2.2:8080/api/v1`. Neu chay thiet bi that, can doi base URL sang IP LAN cua may chay backend.

## 12. Ket luan

Frontend web hien la phan hoan thien nhat va bao phu day du user flow chinh: dashboard, compare, graph, cluster, chat, profile, admin. Mobile app da port phan lon chuc nang nguoi dung sang Expo, nhung con mot so diem can hoan thien nhu global maintenance, xu ly timeout navigation, va phu thuoc CDN cho graph.

Kien truc frontend kha ro: moi domain co service API rieng, page tu quan ly state local, theme dark dung token chung. Neu tiep tuc phat trien, uu tien nen la sua cac loi runtime tiem an, dong bo doc/README voi code thuc te, hoan thien admin CMS, va them frontend vao docker-compose de deploy tron bo.
