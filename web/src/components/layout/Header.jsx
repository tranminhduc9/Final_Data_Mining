import { NavLink } from 'react-router-dom';
import { useState, useRef, useEffect } from 'react';
import './Header.css';

const navItems = [
    { path: '/dashboard', label: 'Radar' },
    { path: '/compare', label: 'So sánh' },
    { path: '/graph', label: 'Đồ thị' },
    { path: '/chat', label: 'AI Chat' },
];

export default function Header() {
    const [menuOpen, setMenuOpen] = useState(false);
    const menuRef = useRef();

    useEffect(() => {
        function handleClick(e) {
            if (menuRef.current && !menuRef.current.contains(e.target)) {
                setMenuOpen(false);
            }
        }
        document.addEventListener('mousedown', handleClick);
        return () => document.removeEventListener('mousedown', handleClick);
    }, []);
    return (
        <header className="site-header">
            <div className="header-inner">
                {/* Logo */}
                <div className="header-logo">
                    <span className="logo-text">Tech<span className="logo-accent">Radar</span></span>
                </div>

                {/* Navbar */}
                <nav className="header-nav" aria-label="Main navigation">
                    {navItems.map(({ path, label }) => (
                        <NavLink
                            key={path}
                            to={path}
                            className={({ isActive }) =>
                                `nav-link${isActive ? ' nav-link--active' : ''}`
                            }
                        >
                            {label}
                        </NavLink>
                    ))}
                </nav>

                {/* Right actions */}
                <div className="header-actions">
                    <div className="header-status">
                        <span className="status-dot" />
                        <span className="status-text">Live</span>
                    </div>
                    <div className="avatar-wrap" ref={menuRef}>
                        <div
                            className={`header-avatar${menuOpen ? ' active' : ''}`}
                            title="Tài khoản"
                            onClick={() => setMenuOpen(o => !o)}
                        >
                            <svg viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg" width="36" height="36">
                                <circle cx="18" cy="18" r="18" fill="#9FA8C7" />
                                <circle cx="18" cy="14" r="6" fill="#E8EAF6" />
                                <ellipse cx="18" cy="30" rx="11" ry="7" fill="#E8EAF6" />
                            </svg>
                        </div>
                        {menuOpen && (
                            <div className="avatar-dropdown">
                                <div className="dropdown-header">
                                    <div className="dropdown-avatar">
                                        <svg viewBox="0 0 40 40" fill="none" width="40" height="40">
                                            <circle cx="20" cy="20" r="20" fill="#9FA8C7" />
                                            <circle cx="20" cy="15" r="7" fill="#E8EAF6" />
                                            <ellipse cx="20" cy="33" rx="12" ry="8" fill="#E8EAF6" />
                                        </svg>
                                    </div>
                                    <div>
                                        <div className="dropdown-name">Người dùng</div>
                                        <div className="dropdown-email">user@techradar.vn</div>
                                    </div>
                                </div>
                                <div className="dropdown-divider" />
                                <button className="dropdown-item">
                                    <span>Thông tin cá nhân</span>
                                </button>
                                <button className="dropdown-item">
                                    <span>Cài đặt</span>
                                </button>
                                <div className="dropdown-divider" />
                                <button className="dropdown-item danger">
                                    <span>Đăng xuất</span>
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </header>
    );
}
