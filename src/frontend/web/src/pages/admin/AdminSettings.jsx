import { useAppContext } from '../../contexts/AppContext';
import './AdminSettings.css';

export default function AdminSettings() {
    const { settings, updateSettings } = useAppContext();

    const handleToggleWebMaintenance = () => {
        updateSettings({ isWebMaintenance: !settings.isWebMaintenance });
    };

    const handleToggleAppMaintenance = () => {
        updateSettings({ isAppMaintenance: !settings.isAppMaintenance });
    };

    const handleToggleChat = () => {
        updateSettings({ isChatEnabled: !settings.isChatEnabled });
    };

    const handleToggleGraph = () => {
        updateSettings({ isGraphEnabled: !settings.isGraphEnabled });
    };

    return (
        <div className="admin-settings">
            <div className="settings-header">
                <h2>Cài đặt Hệ thống</h2>
                <p>Điều khiển các cờ trạng thái (Feature Flags) của ứng dụng.</p>
            </div>
            
            <div className="settings-card danger-zone">
                <div className="setting-info">
                    <h3>Chế độ Bảo trì Website</h3>
                    <p>Đóng toàn bộ màn hình truy cập của người dùng Web.</p>
                </div>
                <label className="switch">
                    <input type="checkbox" checked={settings.isWebMaintenance || false} onChange={handleToggleWebMaintenance} />
                    <span className="slider round"></span>
                </label>
            </div>

            <div className="settings-card danger-zone">
                <div className="setting-info">
                    <h3>Chế độ Bảo trì App Mobile</h3>
                    <p>Chặn truy cập đối với phiên bản ứng dụng di động.</p>
                </div>
                <label className="switch">
                    <input type="checkbox" checked={settings.isAppMaintenance || false} onChange={handleToggleAppMaintenance} />
                    <span className="slider round"></span>
                </label>
            </div>

            <div className="settings-card">
                <div className="setting-info">
                    <h3>Tính năng AI Chatbot</h3>
                    <p>Bật hoặc tắt tính năng Chatbot tư vấn xu hướng trên diện rộng.</p>
                </div>
                <label className="switch">
                    <input type="checkbox" checked={settings.isChatEnabled !== false} onChange={handleToggleChat} />
                    <span className="slider round"></span>
                </label>
            </div>

            <div className="settings-card">
                <div className="setting-info">
                    <h3>Tính năng Graph Explorer</h3>
                    <p>Bật/tắt nút và luồng truy xuất dữ liệu Knowledge Graph.</p>
                </div>
                <label className="switch">
                    <input type="checkbox" checked={settings.isGraphEnabled !== false} onChange={handleToggleGraph} />
                    <span className="slider round"></span>
                </label>
            </div>
        </div>
    );
}
