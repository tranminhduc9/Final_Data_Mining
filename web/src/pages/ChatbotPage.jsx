import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { streamChatResponse } from '../api/chatMock';
import './ChatbotPage.css';

// Minimal markdown renderer (bold, italic, headers, lists, tables)
function renderMarkdown(text) {
    const lines = text.split('\n');
    const elements = [];
    let i = 0;
    while (i < lines.length) {
        const line = lines[i];
        // Table
        if (line.includes('|') && lines[i + 1]?.includes('---')) {
            const headers = line.split('|').filter(h => h.trim());
            const rows = [];
            i += 2;
            while (i < lines.length && lines[i].includes('|')) {
                rows.push(lines[i].split('|').filter(c => c.trim()));
                i++;
            }
            elements.push(
                <table key={i} className="md-table">
                    <thead><tr>{headers.map((h, j) => <th key={j}>{inlineMarkdown(h.trim())}</th>)}</tr></thead>
                    <tbody>{rows.map((r, j) => <tr key={j}>{r.map((c, k) => <td key={k}>{inlineMarkdown(c.trim())}</td>)}</tr>)}</tbody>
                </table>
            );
        } else if (/^#{1,3} /.test(line)) {
            const level = line.match(/^#+/)[0].length;
            const content = line.replace(/^#+\s/, '');
            const Tag = `h${Math.min(level + 2, 6)}`;
            elements.push(<Tag key={i} className="md-heading">{inlineMarkdown(content)}</Tag>);
            i++;
        } else if (/^[*\-] /.test(line)) {
            const items = [];
            while (i < lines.length && /^[*\-] /.test(lines[i])) {
                items.push(<li key={i}>{inlineMarkdown(lines[i].replace(/^[*\-] /, ''))}</li>);
                i++;
            }
            elements.push(<ul key={`ul-${i}`} className="md-list">{items}</ul>);
        } else if (line.trim() === '') {
            elements.push(<br key={`br-${i}`} />);
            i++;
        } else {
            elements.push(<p key={i} className="md-p">{inlineMarkdown(line)}</p>);
            i++;
        }
    }
    return elements;
}

function inlineMarkdown(text) {
    const parts = [];
    let rest = text;
    let key = 0;
    // Bold **text**
    while (rest.length > 0) {
        const boldMatch = rest.match(/\*\*(.+?)\*\*/);
        const italicMatch = rest.match(/\*(.+?)\*/);
        const codeMatch = rest.match(/`(.+?)`/);
        const earliest = [
            boldMatch ? { idx: rest.indexOf(boldMatch[0]), len: boldMatch[0].length, el: <strong key={key++}>{boldMatch[1]}</strong> } : null,
            italicMatch ? { idx: rest.indexOf(italicMatch[0]), len: italicMatch[0].length, el: <em key={key++}>{italicMatch[1]}</em> } : null,
            codeMatch ? { idx: rest.indexOf(codeMatch[0]), len: codeMatch[0].length, el: <code key={key++} className="md-code">{codeMatch[1]}</code> } : null,
        ].filter(Boolean).sort((a, b) => a.idx - b.idx)[0];
        if (!earliest) { parts.push(rest); break; }
        if (earliest.idx > 0) parts.push(rest.slice(0, earliest.idx));
        parts.push(earliest.el);
        rest = rest.slice(earliest.idx + earliest.len);
    }
    return parts;
}

const QUICK_PROMPTS = [
    'Học Golang thì nên apply công ty nào ở Việt Nam, lương bao nhiêu?',
    'AI/ML đang hot như thế nào và cần học gì?',
    'Mình biết React + Node.js 2 năm, lương 25tr, muốn lên senior hoặc chuyển sang AI, nên học gì?',
    'So sánh Python vs Golang cho backend tại Việt Nam',
];

let msgId = 0;

export default function ChatbotPage() {

    const navigate = useNavigate();
    const [messages, setMessages] = useState([
        {
            id: msgId++, role: 'bot',
            text: 'Xin chào! Mình là **Tech Radar AI**, trợ lý tư vấn công nghệ dựa trên dữ liệu thực từ thị trường tuyển dụng IT Việt Nam.\n\nBạn có thể hỏi mình về:\n- Cơ hội việc làm theo tech stack\n- Xu hướng công nghệ & mức lương\n- Lộ trình học và chuyển hướng sự nghiệp',
        }
    ]);
    const [input, setInput] = useState('');
    const [isStreaming, setIsStreaming] = useState(false);
    const [profile, setProfile] = useState({ skills: '', exp: '', salary: '' });
    const [showProfile, setShowProfile] = useState(false);
    const bottomRef = useRef();

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const sendMessage = (text) => {
        if (!text.trim() || isStreaming) return;
        const userMsg = { id: msgId++, role: 'user', text };
        const botMsg = { id: msgId++, role: 'bot', text: '', streaming: true };
        setMessages(prev => [...prev, userMsg, botMsg]);
        setInput('');
        setIsStreaming(true);

        let accumulated = '';
        streamChatResponse(
            text,
            (chunk) => {
                accumulated += chunk;
                setMessages(prev => prev.map(m => m.id === botMsg.id ? { ...m, text: accumulated } : m));
            },
            () => {
                setMessages(prev => prev.map(m => m.id === botMsg.id ? { ...m, streaming: false } : m));
                setIsStreaming(false);
            }
        );
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(input); }
    };

    return (
        <div className="chat-page">
            {/* Left: Chat */}
            <div className="chat-main">
                <div className="chat-window">
                    {messages.map(msg => (
                        <div key={msg.id} className={`chat-bubble-wrap ${msg.role}`}>
                            {msg.role === 'bot' && <div className="bot-avatar text-avatar">AI</div>}
                            <div className={`chat-bubble ${msg.role}`}>
                                <div className="bubble-content">
                                    {renderMarkdown(msg.text)}
                                    {msg.streaming && <span className="cursor-blink" />}
                                </div>
                                {msg.role === 'bot' && !msg.streaming && msg.text.length > 100 && (
                                    <div className="bubble-actions">
                                        <button className="bubble-action-btn" onClick={() => navigate('/graph')}>
                                            Xem chi tiết job matching trong Graph
                                        </button>
                                    </div>
                                )}
                            </div>
                            {msg.role === 'user' && <div className="user-avatar text-avatar">U</div>}
                        </div>
                    ))}
                    <div ref={bottomRef} />
                </div>

                {/* Quick prompts */}
                <div className="quick-prompts">
                    {QUICK_PROMPTS.map((p, i) => (
                        <button key={i} className="quick-btn" onClick={() => sendMessage(p)}>{p}</button>
                    ))}
                </div>

                {/* Input */}
                <div className="chat-input-bar">
                    <textarea
                        className="chat-input"
                        placeholder="Hỏi về xu hướng công nghệ, lương, lộ trình học... (Enter để gửi)"
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        rows={2}
                        disabled={isStreaming}
                    />
                    <button
                        className={`send-btn${isStreaming ? ' loading' : ''}`}
                        onClick={() => sendMessage(input)}
                        disabled={isStreaming || !input.trim()}
                    >
                        {isStreaming ? '...' : 'Gửi'}
                    </button>
                </div>
            </div>

            {/* Right: Profile panel */}
            <div className="chat-sidebar">
                <div className="card profile-panel">
                    <div className="flex-between" style={{ marginBottom: 12 }}>
                        <h3 className="section-title" style={{ marginBottom: 0 }}>
                            <span>Hồ sơ của bạn</span>
                        </h3>
                        <button className="btn btn-ghost" style={{ padding: '4px 8px', fontSize: '0.75rem' }}
                            onClick={() => setShowProfile(p => !p)}>
                            {showProfile ? 'Thu gọn' : 'Mở rộng'}
                        </button>
                    </div>

                    {showProfile && (
                        <div className="profile-form">
                            <div className="pf-group">
                                <label className="pf-label">Kỹ năng hiện tại</label>
                                <input className="pf-input" placeholder="React, Node.js, SQL..."
                                    value={profile.skills} onChange={e => setProfile(p => ({ ...p, skills: e.target.value }))} />
                            </div>
                            <div className="pf-group">
                                <label className="pf-label">Số năm kinh nghiệm</label>
                                <input className="pf-input" placeholder="2 năm" type="text"
                                    value={profile.exp} onChange={e => setProfile(p => ({ ...p, exp: e.target.value }))} />
                            </div>
                            <div className="pf-group">
                                <label className="pf-label">Mức lương mong muốn</label>
                                <input className="pf-input" placeholder="45 triệu" type="text"
                                    value={profile.salary} onChange={e => setProfile(p => ({ ...p, salary: e.target.value }))} />
                            </div>
                            <button className="btn btn-primary w-full" style={{ marginTop: 8, justifyContent: 'center' }}
                                onClick={() => {
                                    const q = `Mình biết ${profile.skills || 'React, Node.js'}, ${profile.exp || '2 năm'} kinh nghiệm, lương hiện ${profile.salary || '25tr'}, nên học gì tiếp?`;
                                    sendMessage(q);
                                    setShowProfile(false);
                                }}>
                                Nhận tư vấn lộ trình
                            </button>
                        </div>
                    )}

                    {!showProfile && (
                        <p className="text-2 text-sm">Nhập hồ sơ để nhận tư vấn lộ trình cá nhân hóa.</p>
                    )}
                </div>

                <div className="card" style={{ marginTop: 12 }}>
                    <h3 className="section-title">Gợi ý câu hỏi</h3>
                    <div className="suggestion-list">
                        {QUICK_PROMPTS.map((p, i) => (
                            <button key={i} className="suggestion-item" onClick={() => sendMessage(p)}>
                                <span className="sug-num">{i + 1}</span>
                                <span>{p}</span>
                            </button>
                        ))}
                    </div>
                </div>

                <div className="card" style={{ marginTop: 12 }}>
                    <h3 className="section-title">Công cụ liên quan</h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                        <button className="btn btn-secondary w-full" style={{ justifyContent: 'flex-start' }}
                            onClick={() => navigate('/graph')}>Graph Explorer</button>
                        <button className="btn btn-secondary w-full" style={{ justifyContent: 'flex-start' }}
                            onClick={() => navigate('/dashboard')}>Trend Dashboard</button>
                        <button className="btn btn-secondary w-full" style={{ justifyContent: 'flex-start' }}
                            onClick={() => navigate('/compare')}>So sánh công nghệ</button>
                    </div>
                </div>
            </div>
        </div>
    );
}
