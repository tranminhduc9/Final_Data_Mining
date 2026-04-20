# Quy chuẩn viết code (Coding Convention)

## 1. Ứng dụng Web (React/Vite)
- **Component:** Bắt buộc viết Functional Component và sử dụng Hooks.
- **Styling:** Tuân thủ theo cấu hình hiện tại, có thể dùng CSS thuần hoặc các framework tương ứng đã được cài đặt. 
- **Giao tiếp API:** Nếu có kết nối dữ liệu ngoại vi, tạo các file service riêng trong `src/services/` dùng `axios` hoặc `fetch`. Không fetch API trực tiếp tại UI Component để dễ maintain.

## 2. Ứng dụng Mobile (React Native/Expo)
- **Component:** Sử dụng App Router của Expo (thư mục `app/` cho điều hướng). Các UI Component dùng chung (Button, Card,...) phải được tách riêng ra `components/`.
- **Styling:** Sử dụng `StyleSheet.create` mặc định của React Native.
- **Data Visualization:** Nếu áp dụng biểu đồ, sử dụng thư viện đã cài đặt như `react-native-chart-kit`.