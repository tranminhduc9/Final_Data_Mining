import './Topbar.css';

export default function Topbar({ title }) {
    return (
        <header className="topbar">
            <div className="topbar-left">
                <h1 className="topbar-title">{title}</h1>
            </div>
            <div className="topbar-right">
                <div className="topbar-chip">
                    <span className="dot live" style={{ width: 7, height: 7, borderRadius: '50%', background: 'var(--green)', boxShadow: '0 0 6px var(--green)', display: 'inline-block' }} />
                    <span>Live • Cập nhật 1h trước</span>
                </div>
                <div className="topbar-avatar">TT</div>
            </div>
        </header>
    );
}
