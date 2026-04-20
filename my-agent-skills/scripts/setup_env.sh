#!/bin/bash
# Hướng dẫn cho Agent: Chạy script này từ thư mục gốc để setup dự án Frontend.

echo "📦 Đang cài đặt thư viện cho Ứng dụng Web (React/Vite)..."
cd web
npm install
cd ..

echo "📦 Đang cài đặt thư viện cho Ứng dụng Mobile (Expo)..."
cd app
npm install
cd ..

echo "✅ Hoàn tất quá trình cài đặt môi trường cho phân hệ Web và Mobile!"