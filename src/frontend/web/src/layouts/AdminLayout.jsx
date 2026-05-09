import { Outlet } from 'react-router-dom';
import { useState } from 'react';
import AdminSidebar from '../components/layout/AdminSidebar';
import './AdminLayout.css';

export default function AdminLayout() {
    const [collapsed, setCollapsed] = useState(false);

    return (
        <div className="admin-layout">
            <AdminSidebar collapsed={collapsed} onToggle={() => setCollapsed(!collapsed)} />
            <div className={`admin-main ${collapsed ? 'expanded' : ''}`}>
                <main className="admin-content">
                    <Outlet />
                </main>
            </div>
        </div>
    );
}
