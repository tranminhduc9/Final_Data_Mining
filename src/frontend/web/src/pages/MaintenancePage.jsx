import './MaintenancePage.css';

export default function MaintenancePage() {
    return (
        <div className="maintenance-wrapper">
            <div className="maintenance-content">
                <div className="icon-pulse">🚧</div>
                <h1>Hệ Thống Đang Bảo Trì</h1>
                <p>Tech Radar VN đang tiến hành nâng cấp thuật toán AI và tối ưu hoá dữ liệu định kỳ. Chúng tôi sẽ nhanh chóng khôi phục hệ thống.</p>
                <div className="maintenance-footer">
                    * Quyền Admin? <a href="/admin">Khu vực Quản trị nội bộ</a>
                </div>
            </div>
        </div>
    );
}
