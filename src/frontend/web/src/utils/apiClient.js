// Utility func để call API với Base URL
// Dùng path tương đối để Vite proxy tự forward sang backend (tránh CORS)
const API_BASE_URL = '/api/v1';

export const apiClient = async (endpoint, options = {}) => {
    // Lấy token từ localStorage (hoặc tuỳ cách bạn lưu token)
    const token = localStorage.getItem('access_token');

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

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
        
        if (!response.ok) {
            // Có thể handle logout nếu 401 Unauthorized
            if (response.status === 401) {
                // Xử lý token hết hạn...
            }
            throw new Error(`API error: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
};
