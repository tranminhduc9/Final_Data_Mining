import { NavLink } from 'react-router-dom';
import './Sidebar.css';

const NAV_ITEMS = [
    { to: '/admin/dashboard', label: 'Dashboard' },
    { to: '/admin/users', label: 'Quản lý người dùng' },
    { to: '/admin/cms', label: 'Quản lý dữ liệu (CMS)' },
    { to: '/admin/settings', label: 'Cài đặt hệ thống' },
];

export default function AdminSidebar({ collapsed, onToggle }) {
    return (
        <aside className={`sidebar${collapsed ? ' collapsed' : ''}`}>
            <div className="sidebar-header">
                {!collapsed && (
                    <div className="sidebar-brand">
                        <span className="brand-name">Admin Portal</span>
                    </div>
                )}
                <button className="collapse-btn" onClick={onToggle} title="Toggle sidebar">
                    {collapsed ? '›' : '‹'}
                </button>
            </div>

            <nav className="sidebar-nav">
                {NAV_ITEMS.map(item => (
                    <NavLink
                        key={item.to}
                        to={item.to}
                        className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
                        title={collapsed ? item.label : ''}
                    >
                        {!collapsed && <span className="nav-label">{item.label}</span>}
                    </NavLink>
                ))}
            </nav>
        </aside>
    );
}
