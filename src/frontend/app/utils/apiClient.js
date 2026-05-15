import AsyncStorage from '@react-native-async-storage/async-storage';

import { Platform, Alert } from 'react-native';

// Đối với Mobile, localhost thường không hoạt động trên Android Emulator (dùng 10.0.2.2)
// Hoặc dùng địa chỉ IP nội bộ của máy tính nếu test trên thiết bị thật.
const API_BASE_URL = Platform.OS === 'web' 
    ? 'http://localhost:8080/api/v1' 
    : 'http://10.0.2.2:8080/api/v1'; 

export const apiClient = async (endpoint, options = {}) => {
    try {
        // 1. Kiểm tra thời gian phiên đăng nhập (900 giây = 15 phút)
        const loginTimestamp = await AsyncStorage.getItem('login_timestamp');
        if (loginTimestamp) {
            const diffSeconds = (Date.now() - parseInt(loginTimestamp)) / 1000;
            if (diffSeconds > 900) {
                console.warn('Session timeout reached (900s). Clearing session...');
                await AsyncStorage.removeItem('access_token');
                await AsyncStorage.removeItem('refresh_token');
                await AsyncStorage.removeItem('login_timestamp');
                
                const msg = 'Phiên đăng nhập đã hết hạn (sau 15 phút). Vui lòng đăng nhập lại.';
                if (Platform.OS === 'web') {
                    window.alert(msg);
                    window.location.href = '/login';
                } else {
                    Alert.alert('Hết phiên', msg);
                    // Lưu ý: Cần xử lý navigation ra ngoài login ở cấp UI hoặc thông qua Event
                }
                
                throw new Error('SESSION_TIMEOUT');
            }
        }

        // Lấy token từ AsyncStorage
        const token = await AsyncStorage.getItem('access_token');

        const headers = {
            'Content-Type': 'application/json',
            ...options.headers,
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const config = {
            ...options,
            headers,
        };

        console.log(`[API Call] ${API_BASE_URL}${endpoint}`);

        const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
        
        if (!response.ok) {
            if (response.status === 401) {
                // Xử lý khi hết phiên đăng nhập hoặc Token không hợp lệ
                console.warn('Unauthorized. Clearing session...');
                await AsyncStorage.removeItem('access_token');
                await AsyncStorage.removeItem('refresh_token');
                await AsyncStorage.removeItem('login_timestamp');

                const msg = 'Phiên đăng nhập của bạn đã hết hạn. Vui lòng đăng nhập lại.';
                if (Platform.OS === 'web') {
                    window.alert(msg);
                    window.location.href = '/login';
                } else {
                    Alert.alert('Lỗi xác thực', msg);
                }
            }
            throw new Error(`API error: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Mobile API call failed:', error);
        throw error;
    }
};
