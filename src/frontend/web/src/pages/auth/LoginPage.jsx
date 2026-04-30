import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { loginUser } from '../../api/authService';
import './Auth.css';

export default function LoginPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleLogin = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const res = await loginUser({ email, password });
            if (res.access_token) {
                localStorage.setItem('access_token', res.access_token);
                if (res.refresh_token) {
                    localStorage.setItem('refresh_token', res.refresh_token);
                }
                navigate('/dashboard');
            } else {
                setError('Đăng nhập thất bại. Vui lòng kiểm tra lại thông tin.');
            }
        } catch (err) {
            setError('Đăng nhập thất bại. Vui lòng thử lại.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-container">
            <div className="auth-left">
                <div className="auth-form-wrapper">
                    <div className="auth-logo">Tech<span>Radar</span></div>
                    <div>
                        <h1 className="auth-title">Welcome back.</h1>
                        <p className="auth-subtitle">Đăng nhập để tiếp tục khai phá dữ liệu.</p>
                    </div>

                    {error && <div style={{ color: '#ff6b6b', fontSize: '0.85rem' }}>{error}</div>}

                    <form className="auth-form" onSubmit={handleLogin}>
                        <div className="auth-input-group">
                            <label>Email Address</label>
                            <input 
                                type="email" 
                                required 
                                placeholder="name@company.com"
                                value={email}
                                onChange={e => setEmail(e.target.value)}
                            />
                        </div>
                        <div className="auth-input-group">
                            <label>Password</label>
                            <input 
                                type="password" 
                                required 
                                placeholder="••••••••"
                                value={password}
                                onChange={e => setPassword(e.target.value)}
                            />
                        </div>
                        
                        <button type="submit" className="auth-btn" disabled={loading}>
                            {loading ? 'Đang xác thực...' : 'Đăng nhập'}
                        </button>
                    </form>

                    <div className="auth-footer">
                        Chưa có tài khoản? 
                        <Link to="/register" className="auth-link">Đăng ký ngay</Link>
                    </div>
                </div>
            </div>

            <div className="auth-right">
                <h2 className="auth-artwork-title">Phân tích.<br/>Làm chủ.<br/>Dẫn đầu.</h2>
                <p className="auth-artwork-subtitle">
                    Hệ thống trích xuất và phân tích xu hướng công nghệ TechRadar - Mang lợi thế cạnh tranh vào lòng bàn tay bạn.
                </p>
            </div>
        </div>
    );
}
