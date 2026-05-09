import { useState, useEffect } from 'react';
import { fetchAdminDashboardStats } from '../../api/adminService';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './AdminDashboard.css';

export default function AdminDashboard() {
    const [stats, setStats] = useState(null);

    useEffect(() => {
        fetchAdminDashboardStats().then(res => {
            if(res.status === 'success') {
                setStats(res.data);
            }
        });
    }, []);

    if(!stats) return <div className="loading" style={{color: '#fff', textAlign: 'center'}}>Đang tải dữ liệu Admin...</div>;

    return (
        <div className="admin-dashboard">
            <div className="stat-cards">
                <div className="stat-card">
                    <h3>Tổng User</h3>
                    <p className="stat-value">{stats.totalUsers}</p>
                </div>
                <div className="stat-card">
                    <h3>Truy cập hôm nay</h3>
                    <p className="stat-value">{stats.activeSessions}</p>
                </div>
                <div className="stat-card">
                    <h3>Lượt tìm kiếm</h3>
                    <p className="stat-value">{stats.searchesToday}</p>
                </div>
            </div>

            <div className="dashboard-grid">
                <div className="chart-card">
                    <h3>Lưu lượng truy cập hệ thống</h3>
                    <div style={{ width: '100%', height: 350 }}>
                        <ResponsiveContainer>
                            <LineChart data={stats.revenueMock} margin={{top: 20, right: 30, left: 0, bottom: 0}}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#333333" />
                                <XAxis dataKey="name" stroke="#a0aec0" />
                                <YAxis stroke="#a0aec0" />
                                <Tooltip contentStyle={{ backgroundColor: '#1a202c', border: '1px solid #333333', borderRadius: 8, color: '#fff' }} />
                                <Legend wrapperStyle={{paddingTop: '20px'}}/>
                                <Line type="monotone" dataKey="uv" name="Người dùng truy cập" stroke="#ffffff" strokeWidth={3} dot={{r: 5, strokeWidth: 2}} activeDot={{r: 8}} />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="keyword-card">
                    <h3>Top từ khóa tìm kiếm</h3>
                    <ul className="keyword-list">
                        {stats.topKeywords.map((kw, idx) => (
                            <li key={idx}>
                                <span className="rank-badge">{idx + 1}</span> 
                                <span style={{fontWeight: 500}}>{kw}</span>
                            </li>
                        ))}
                    </ul>
                </div>
            </div>
        </div>
    );
}
