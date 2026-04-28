# Quy chuẩn viết code (Coding Convention)

## 1. Web Dashboard (Next.js 15)
- **App Router**: Sử dụng cấu trúc thư mục `app/` cho điều hướng.
- **Components**: 
  - Ưu tiên Server Components cho các phần fetch dữ liệu.
  - Sử dụng Client Components (`'use client'`) cho các phần tương tác UI.
- **Styling**: Sử dụng Tailwind CSS. Tuân thủ thiết kế hiện đại, premium (vibrant colors, glassmorphism, animations).
- **Icons**: Sử dụng `lucide-react`.
- **Data Fetching**: Sử dụng `fetch` API tích hợp sẵn của Next.js với các cơ chế caching phù hợp.

## 2. Mobile App (Expo / React Native)
- **Structure**: Sử dụng `expo-router` (thư mục `app/`).
- **Components**: Tách biệt UI logic và Business logic. Các component dùng chung đặt trong `components/`.
- **Styling**: Sử dụng `NativeWind` (nếu có) hoặc `StyleSheet` chuẩn.
- **Assets**: Quản lý ảnh, font trong thư mục `assets/`.

## 3. Quy chuẩn chung cho Agent
- **Clean Code**: Đặt tên biến, hàm rõ nghĩa (tiếng Anh).
- **Documentation**: Viết JSDoc cho các hàm phức tạp.
- **Type Safety**: Luôn sử dụng TypeScript, định nghĩa Interface/Type rõ ràng, tránh dùng `any`.
- **Error Handling**: Sử dụng Try-Catch và thông báo lỗi thân thiện với người dùng.