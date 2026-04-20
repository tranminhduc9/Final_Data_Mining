// Mock API cho Development
export const loginMock = async (email, password) => {
    return new Promise((resolve) => {
        setTimeout(() => {
            resolve({
                status: 'success',
                data: {
                    user: { id: 1, email: email, name: 'Admin User' },
                    access_token: 'mock-jwt-token'
                }
            });
        }, 500);
    });
};

export const registerMock = async (userData) => {
    return new Promise((resolve) => {
        setTimeout(() => {
            resolve({
                status: 'success',
                data: {
                    message: "Tạo tài khoản thành công",
                    user: { id: 2, email: userData.email, name: userData.name || 'New User' }
                }
            });
        }, 800);
    });
};

/* =========================================================================
   THỰC TẾ API /api/v1/auth (Tạm thời được comment vì chưa dùng đến)
========================================================================= */
/*
// Đăng ký tài khoản
export const registerUser = async (userData) => {
    // Endpoint: POST /api/v1/auth/register
    // Auth: No
    const response = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(userData)
    });
    return response.json();
};

// Đăng nhập
export const loginUser = async (credentials) => {
    // Endpoint: POST /api/v1/auth/login
    // Auth: No
    const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials)
    });
    return response.json();
};

// Refresh token
export const refreshToken = async (refreshTokenValue) => {
    // Endpoint: POST /api/v1/auth/refresh
    // Auth: No
    const response = await fetch('/api/v1/auth/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshTokenValue })
    });
    return response.json();
};

// Đăng xuất
export const logoutUser = async (token) => {
    // Endpoint: POST /api/v1/auth/logout
    // Auth: Optional
    const response = await fetch('/api/v1/auth/logout', {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'Authorization': token ? `Bearer ${token}` : ''
        }
    });
    return response.json();
};

// Lấy thông tin user hiện tại
export const getCurrentUser = async (token) => {
    // Endpoint: GET /api/v1/auth/me
    // Auth: Yes
    const response = await fetch('/api/v1/auth/me', {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    return response.json();
};
*/
