#!/bin/bash
# Hướng dẫn cho Agent: Chạy script này từ thư mục gốc (Final_Data_Mining/) để setup dự án lần đầu.

echo "🐍 Đang cài đặt thư viện Python bằng uv..."
# Đảm bảo đã cài uv: https://github.com/astral-sh/uv
uv sync

echo "📦 Đang cài đặt thư viện Frontend (React + Vite)..."
cd web
npm install
cd ..

echo "✅ Hoàn tất! Tạo file .env ở thư mục gốc và điền thông tin kết nối Neo4j AuraDB + Gemini API Key trước khi chạy."