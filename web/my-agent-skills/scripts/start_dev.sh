#!/bin/bash
# Hướng dẫn cho Agent: Chạy script này từ thư mục gốc (Final_Data_Mining/) để khởi động môi trường dev.

echo "🐳 Đang khởi động Backend và Database bằng Docker..."
# Chạy container ngầm (-d). Đảm bảo docker-compose.yml đã cấu hình port mapping chuẩn.
docker compose up -d

echo "🌐 Đang khởi động Frontend (React + Vite)..."
cd web
# Chạy frontend ở foreground (hiện log trực tiếp trên terminal)
npm run dev

# --- Dọn dẹp khi bấm Ctrl+C ---
trap "echo 'Đang tắt hệ thống...'; cd ..; docker compose down; exit" SIGINT SIGTERM