import { useState } from 'react';
import './AdminUsers.css';

export default function AdminUsers() {
    const [users, setUsers] = useState([
        { id: 1, name: 'Admin TechPulse', email: 'admin@techpulse.vn', role: 'Admin', status: 'Active' },
        { id: 2, name: 'Nguyen Van A', email: 'nva@gmail.com', role: 'User', status: 'Active' },
        { id: 3, name: 'Tran Thi B', email: 'btran123@yahoo.com', role: 'User', status: 'Blocked' }
    ]);

    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editTarget, setEditTarget] = useState(null);

    // Form states
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [role, setRole] = useState('User');
    const [status, setStatus] = useState('Active');

    const handleOpenAdd = () => {
        setEditTarget(null);
        setName(''); setEmail(''); setRole('User'); setStatus('Active');
        setIsModalOpen(true);
    };

    const handleOpenEdit = (user) => {
        setEditTarget(user.id);
        setName(user.name); setEmail(user.email); setRole(user.role); setStatus(user.status);
        setIsModalOpen(true);
    };

    const handleDelete = (id) => {
        if(window.confirm('Bạn có chắc chắn muốn xoá người dùng này không?')) {
            setUsers(prev => prev.filter(u => u.id !== id));
        }
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        if(editTarget) {
            setUsers(prev => prev.map(u => u.id === editTarget ? { ...u, name, email, role, status } : u));
        } else {
            const newId = users.length > 0 ? Math.max(...users.map(u => u.id)) + 1 : 1;
            setUsers(prev => [...prev, { id: newId, name, email, role, status }]);
        }
        setIsModalOpen(false);
    };

    return (
        <div className="admin-users">
            <div className="users-header">
                <div className="users-title">
                    <h2>Quản lý Người dùng</h2>
                    <p>Hỗ trợ thao tác tạo, khoá, chỉnh sửa và phân quyền tài khoản hệ thống.</p>
                </div>
                <div className="users-actions">
                    <button className="btn-add" onClick={handleOpenAdd}>Thêm tài khoản</button>
                </div>
            </div>

            <div className="users-card">
                <table className="users-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Họ và Tên</th>
                            <th>Email</th>
                            <th>Vai trò</th>
                            <th>Trạng thái</th>
                            <th>Hành động</th>
                        </tr>
                    </thead>
                    <tbody>
                        {users.map(u => (
                            <tr key={u.id}>
                                <td className="u-id">#{u.id}</td>
                                <td>{u.name}</td>
                                <td>{u.email}</td>
                                <td>
                                    <span className={`role-badge ${u.role === 'Admin' ? 'admin' : 'user'}`}>
                                        {u.role}
                                    </span>
                                </td>
                                <td>
                                    <span className={`status-badge ${u.status === 'Active' ? 'active' : 'blocked'}`}>
                                        {u.status}
                                    </span>
                                </td>
                                <td className="u-actions">
                                    <button className="u-btn edit" onClick={() => handleOpenEdit(u)}>Sửa</button>
                                    <button className="u-btn del" onClick={() => handleDelete(u.id)}>Xoá</button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Modal */}
            {isModalOpen && (
                <div className="modal-overlay" onClick={() => setIsModalOpen(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()}>
                        <h3>{editTarget ? 'Chỉnh sửa tài khoản' : 'Tạo mới tài khoản'}</h3>
                        <form onSubmit={handleSubmit} className="modal-form">
                            <div className="form-group">
                                <label>Họ và Tên</label>
                                <input required type="text" value={name} onChange={e => setName(e.target.value)} />
                            </div>
                            <div className="form-group">
                                <label>Email</label>
                                <input required type="email" value={email} onChange={e => setEmail(e.target.value)} />
                            </div>
                            <div className="form-row">
                                <div className="form-group">
                                    <label>Vai trò</label>
                                    <select value={role} onChange={e => setRole(e.target.value)}>
                                        <option value="User">User</option>
                                        <option value="Admin">Admin</option>
                                    </select>
                                </div>
                                <div className="form-group">
                                    <label>Trạng thái</label>
                                    <select value={status} onChange={e => setStatus(e.target.value)}>
                                        <option value="Active">Hoạt động</option>
                                        <option value="Blocked">Khoá (Blocked)</option>
                                    </select>
                                </div>
                            </div>
                            <div className="modal-actions">
                                <button type="button" className="m-btn cancel" onClick={() => setIsModalOpen(false)}>Hủy bỏ</button>
                                <button type="submit" className="m-btn save">Lưu thay đổi</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
