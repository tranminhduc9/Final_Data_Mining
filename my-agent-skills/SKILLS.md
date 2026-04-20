---
name: pure-frontend-dev-workflow
description: Kỹ năng quản lý, thiết lập môi trường và vận hành dự án thuần Frontend (bao gồm ứng dụng Web với React/Vite và ứng dụng Mobile với React Native/Expo).
license: MIT
compatibility: Node.js 18+, npm, expo
metadata:
  project_type: Pure Frontend Monorepo (Web + Mobile)
allowed-tools: bash npm npx
---

# Hướng dẫn quy trình phát triển dự án thuần Frontend

Theo cấu trúc thực tế, dự án này là một dự án **thuần Frontend** (không bao gồm database hay backend server nội bộ). Agent cần lưu ý tập trung toàn bộ vào việc phát triển, tối ưu hóa giao diện người dùng, và tích hợp API bên ngoài (nếu có).

## 1. Cấu trúc thư mục chính

Dự án được chia làm 2 phân hệ Frontend độc lập:

- **`/web`** - Ứng dụng Web Dashboard
  - **Tech Stack**: React 19, Vite, React Router DOM.
  - **Data Visualization**: Sử dụng `recharts`, `d3`, và `react-force-graph-2d` để vẽ biểu đồ và trực quan hóa Knowledge Graph.
  - **Lệnh thường dùng**:
    - Cài đặt: `cd web && npm install`
    - Khởi chạy dev server: `cd web && npm run dev`
    - Build production: `cd web && npm run build`

- **`/app`** - Ứng dụng Mobile (Cross-platform)
  - **Tech Stack**: React Native (0.81), Expo (v54), Expo Router.
  - **Tính năng UI**: Sử dụng `react-native-chart-kit` để vẽ biểu đồ, `react-native-reanimated`, và `react-native-webview`.
  - **Lệnh thường dùng**:
    - Cài đặt: `cd app && npm install`
    - Khởi chạy Expo: `cd app && npm run start`

## 2. Nhiệm vụ và Phạm vi của Agent
- **Chỉ code Frontend**: Tuyệt đối không đề xuất khởi tạo FastAPI, Neo4j, hay các thành phần Backend khác (như đã đề cập sai lệch ở tài liệu cũ) trừ khi user yêu cầu đích danh.
- **Tập trung vào UI/UX**: Tối ưu hiển thị biểu đồ, xử lý trạng thái (state management) và luồng điều hướng (navigation).
- **Tuân thủ cấu trúc**: Bất kỳ tính năng web nào phải viết trong `/web/src`, và tính năng mobile phải viết trong thư mục của `/app`.