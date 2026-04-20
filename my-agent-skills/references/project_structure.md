# Cấu trúc Dự án (Project Structure)

Thư mục này đại diện cho kiến trúc dự án thuần Frontend (Monorepo), tập trung hoàn toàn vào nền tảng Web và Mobile.

## 🌳 Sơ đồ cây (Directory Tree)

Project/
├── app/                    # Ứng dụng Mobile (React Native / Expo)
│   ├── assets/             # Hình ảnh, icon, font
│   ├── components/         # Các UI component tái sử dụng
│   ├── constants/          # Định nghĩa hằng số, màu sắc, theme
│   ├── hooks/              # Custom React Hooks
│   ├── services/           # Các hàm fetch API
│   ├── app.json            # Cấu hình chung cho Expo project
│   └── package.json        # Khai báo dependency chính cho Mobile
│
├── web/                    # Ứng dụng Web Dashboard (React / Vite)
│   ├── public/             # Static files (favicon, icon)
│   ├── src/                # SOURCE CODE CHÍNH CỦA ỨNG DỤNG WEB
│   ├── Dockerfile          # Khai báo đóng gói Nginx cho Web
│   ├── docker-compose.yml  # Triển khai Web bằng Docker
│   ├── package.json        # Khai báo dependency chính cho Web
│   └── vite.config.js      # Cấu hình đóng gói Web bundler
│
└── my-agent-skills/        # Thư mục kỹ năng và hướng dẫn cho AI

## 📍 Hướng dẫn điều hướng cho AI (Navigation Rules)

1. **Khi được yêu cầu "Xử lý/Tạo màn hình trên Mobile":**
   - Chỉ hoạt động trong phạm vi thư mục `/app`.
   - Vận dụng Expo Routing và UI styling cơ bản của React Native.
2. **Khi được yêu cầu "Xử lý logic, vẽ biểu đồ trên Web Dashboard":**
   - Chỉ hoạt động trong phạm vi thư mục `/web/src`.
   - Cài đặt thư viện bằng `npm install --save <tên_thu_vien>` ngay bên trong thư mục `/web/`.