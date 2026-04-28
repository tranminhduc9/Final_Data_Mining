---
name: pure-frontend-dev-workflow
description: Kỹ năng quản lý, thiết lập môi trường và vận hành dự án thuần Frontend (bao gồm ứng dụng Web với Next.js 15 và ứng dụng Mobile với React Native/Expo).
license: MIT
compatibility: Node.js 18+, npm, pnpm, expo
metadata:
  project_type: TechPulse VN - Frontend Focus (Web + Mobile)
allowed-tools: bash npm npx pnpm
---

# Hướng dẫn quy trình phát triển dự án TechPulse VN (Frontend)

Dự án này hiện đang tập trung vào phát triển **Frontend** (Web & Mobile). Các thành phần Backend/AI khác trong thư mục `src/` hiện đang ở bước thiết kế kiến trúc. Agent cần tập trung vào việc tối ưu hóa giao diện, trải nghiệm người dùng và tích hợp dữ liệu.

## 1. Cấu trúc thư mục Frontend

Dự án được chia làm 2 phân hệ Frontend nằm trong thư mục `src/frontend/`:

- **`src/frontend/web`** - Ứng dụng Web Dashboard
  - **Tech Stack**: Next.js 15 (App Router), TypeScript, Tailwind CSS, Lucide React.
  - **Data Visualization**: `react-force-graph` (cho Knowledge Graph), `recharts`/`chart.js` (cho Dashboard).
  - **Lệnh thường dùng**:
    - Cài đặt: `cd src/frontend/web && npm install`
    - Khởi chạy: `cd src/frontend/web && npm run dev`
    - Docker: `src/frontend/web/Dockerfile`

- **`src/frontend/app`** - Ứng dụng Mobile (Cross-platform)
  - **Tech Stack**: React Native, Expo, Expo Router, TypeScript.
  - **Tính năng**: Dashboard xu hướng, Chatbot UI, Knowledge Graph viewer (mobile optimized).
  - **Lệnh thường dùng**:
    - Cài đặt: `cd src/frontend/app && npm install`
    - Khởi chạy: `cd src/frontend/app && npx expo start`

## 2. Nhiệm vụ và Phạm vi của Agent
- **Tập trung Frontend**: Hiện tại chỉ code và chỉnh sửa trong `src/frontend/web` và `src/frontend/app`.
- **Blueprints**: Có thể đọc các file `__init__.py` trong các folder khác của `src/` để hiểu kiến trúc toàn hệ thống, nhưng không tự ý khởi tạo code backend trừ khi có yêu cầu cụ thể.
- **Tuân thủ UI/UX**: Đảm bảo giao diện hiện đại, premium, sử dụng các biểu đồ trực quan sinh động.
- **Tích hợp**: Sử dụng API service từ các file trong `services/` hoặc `api/` của từng project frontend.