import { useState, useEffect, useCallback } from 'react';
import {
    LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
    Tooltip, Legend, ResponsiveContainer, ReferenceLine
} from 'recharts';
import Select from 'react-select';
import { timelineData, growthData, topTechs, ALL_TECHS, MONTHS_24, getSentiment } from '../data/trendMock';
import './TrendDashboard.css';

const TIME_OPTIONS = [
    { label: '3 tháng', value: 3 },
    { label: '6 tháng', value: 6 },
    { label: '12 tháng', value: 12 },
    { label: '24 tháng', value: 24 },
];

const TECH_OPTIONS = ALL_TECHS.map(t => ({ value: t.id, label: t.name, color: t.color }));

const selectStyles = {
    control: (base) => ({
        ...base,
        background: 'var(--surface-2)',
        borderColor: 'var(--border)',
        color: 'var(--text)',
        minHeight: '38px',
        boxShadow: 'none',
        '&:hover': { borderColor: 'var(--primary)' },
    }),
    menu: (base) => ({ ...base, background: 'var(--surface-2)', border: '1px solid var(--border)', zIndex: 200 }),
    option: (base, state) => ({
        ...base,
        background: state.isFocused ? 'var(--surface)' : 'transparent',
        color: 'var(--text)',
        cursor: 'pointer',
    }),
    multiValue: (base) => ({ ...base, background: 'var(--primary-glow)', borderRadius: 4 }),
    multiValueLabel: (base) => ({ ...base, color: 'var(--primary-light)' }),
    multiValueRemove: (base) => ({ ...base, color: 'var(--primary-light)', '&:hover': { background: 'var(--primary)', color: '#fff' } }),
    input: (base) => ({ ...base, color: 'var(--text)' }),
    singleValue: (base) => ({ ...base, color: 'var(--text)' }),
    placeholder: (base) => ({ ...base, color: 'var(--text-3)' }),
};

// Custom tooltip
function CustomTooltip({ active, payload, label, monthIdx }) {
    if (!active || !payload?.length) return null;
    return (
        <div className="chart-tooltip">
            <p className="tooltip-month">{label}</p>
            {payload.map(p => {
                const techId = p.dataKey;
                const sentVal = getSentiment(techId, monthIdx);
                return (
                    <div key={p.dataKey} className="tooltip-row">
                        <span className="tooltip-dot" style={{ background: p.color }} />
                        <span className="tooltip-tech">{ALL_TECHS.find(t => t.id === p.dataKey)?.name || p.dataKey}</span>
                        <span className="tooltip-jobs">{p.value.toLocaleString()} jobs</span>
                        <span className="tooltip-sentiment">Sentiment: {sentVal}%</span>
                    </div>
                );
            })}
        </div>
    );
}

function GrowthTooltip({ active, payload, label }) {
    if (!active || !payload?.length) return null;
    return (
        <div className="chart-tooltip">
            <p className="tooltip-month">{label}</p>
            {payload.map(p => (
                <div key={p.dataKey} className="tooltip-row">
                    <span className="tooltip-dot" style={{ background: p.color }} />
                    <span className="tooltip-tech">{ALL_TECHS.find(t => t.id === p.dataKey)?.name || p.dataKey}</span>
                    <span className={`tooltip-jobs ${p.value >= 0 ? 'up' : 'down'}`}>
                        {p.value >= 0 ? '+' : ''}{p.value}%
                    </span>
                </div>
            ))}
        </div>
    );
}

export default function TrendDashboard() {

    const [selectedTechs, setSelectedTechs] = useState(
        TECH_OPTIONS.slice(0, 5)
    );
    const [timeRange, setTimeRange] = useState(12);
    const [chartMode, setChartMode] = useState('line'); // 'line' | 'bar' | 'growth'
    const [hoveredMonthIdx, setHoveredMonthIdx] = useState(0);

    const sliceStart = Math.max(0, 24 - timeRange);
    const visibleData = (chartMode === 'growth' ? growthData : timelineData).slice(sliceStart);
    const activeTechIds = selectedTechs.map(t => t.value);
    const techColorMap = Object.fromEntries(ALL_TECHS.map(t => [t.id, t.color]));

    const handleExportCSV = useCallback(() => {
        const headers = ['Month', ...activeTechIds];
        const rows = visibleData.map(row => [row.month, ...activeTechIds.map(id => row[id] ?? 0)]);
        const csv = [headers, ...rows].map(r => r.join(',')).join('\n');
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = 'tech_trend_export.csv'; a.click();
        URL.revokeObjectURL(url);
    }, [visibleData, activeTechIds]);

    const handleExportPNG = useCallback(() => {
        import('html2canvas').then(({ default: html2canvas }) => {
            const el = document.getElementById('main-chart-wrapper');
            if (!el) return;
            html2canvas(el, { backgroundColor: '#000000' }).then(canvas => {
                const a = document.createElement('a');
                a.href = canvas.toDataURL('image/png');
                a.download = 'tech_trend_chart.png';
                a.click();
            });
        });
    }, []);

    return (
        <div className="dashboard-page">
            {/* ── Top Stats ── */}
            <div className="stats-row">
                {topTechs.slice(0, 4).map(t => (
                    <div key={t.id} className="stat-card">
                        <div className="stat-header">
                            <span className="stat-name">{t.name}</span>
                            <span className={`badge ${t.growthPct > 30 ? 'badge-up' : t.growthPct < 0 ? 'badge-down' : 'badge-flat'}`}>
                                {t.growthPct > 0 ? '+' : ''}{t.growthPct}%
                            </span>
                        </div>
                        <div className="stat-jobs">{t.jobs.toLocaleString()} <span>jobs</span></div>
                        <div className="stat-meta">Sentiment: {t.sentiment}% • YoY: {t.yoy > 0 ? '+' : ''}{t.yoy}%</div>
                    </div>
                ))}
            </div>

            {/* ── Controls ── */}
            <div className="card dashboard-controls">
                <div className="controls-left">
                    <div className="control-group">
                        <label className="control-label">Công nghệ</label>
                        <Select
                            isMulti
                            options={TECH_OPTIONS}
                            value={selectedTechs}
                            onChange={setSelectedTechs}
                            styles={selectStyles}
                            placeholder="Chọn công nghệ..."
                            closeMenuOnSelect={false}
                        />
                    </div>
                    <div className="control-group">
                        <label className="control-label">Thời gian</label>
                        <div className="pill-group">
                            {TIME_OPTIONS.map(opt => (
                                <button
                                    key={opt.value}
                                    className={`pill${timeRange === opt.value ? ' active' : ''}`}
                                    onClick={() => setTimeRange(opt.value)}
                                >{opt.label}</button>
                            ))}
                        </div>
                    </div>
                    <div className="control-group">
                        <label className="control-label">Dạng biểu đồ</label>
                        <div className="pill-group">
                            <button className={`pill${chartMode === 'line' ? ' active' : ''}`} onClick={() => setChartMode('line')}>Line</button>
                            <button className={`pill${chartMode === 'bar' ? ' active' : ''}`} onClick={() => setChartMode('bar')}>Bar</button>
                            <button className={`pill${chartMode === 'growth' ? ' active' : ''}`} onClick={() => setChartMode('growth')}>Tăng trưởng %</button>
                        </div>
                    </div>
                </div>
                <div className="controls-right">
                    <button className="btn btn-secondary" onClick={handleExportPNG}>Export PNG</button>
                    <button className="btn btn-primary" onClick={handleExportCSV}>Export CSV</button>
                </div>
            </div>

            {/* ── Main Chart ── */}
            <div className="card" id="main-chart-wrapper" style={{ marginTop: 16 }}>
                <div className="flex-between" style={{ marginBottom: 16 }}>
                    <h2 className="section-title">
                        {chartMode === 'growth' ? 'Tăng trưởng % theo thời gian' : 'Số lượng Job Postings theo thời gian'}
                    </h2>
                    {chartMode === 'growth' && (
                        <span className="badge badge-primary" style={{ fontSize: '0.7rem' }}>So với tháng đầu tiên</span>
                    )}
                </div>
                <ResponsiveContainer width="100%" height={360}>
                    {chartMode === 'bar' ? (
                        <BarChart data={visibleData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
                            onMouseMove={e => e.activeTooltipIndex != null && setHoveredMonthIdx(sliceStart + e.activeTooltipIndex)}>
                            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                            <XAxis dataKey="month" tick={{ fill: 'var(--text-3)', fontSize: 11 }} />
                            <YAxis tick={{ fill: 'var(--text-3)', fontSize: 11 }} />
                            <Tooltip content={<CustomTooltip monthIdx={hoveredMonthIdx} />} />
                            <Legend wrapperStyle={{ paddingTop: 12, fontSize: '0.8rem', color: 'var(--text-2)' }} />
                            {activeTechIds.map(id => (
                                <Bar key={id} dataKey={id} fill={techColorMap[id]} name={ALL_TECHS.find(t => t.id === id)?.name} radius={[3, 3, 0, 0]} />
                            ))}
                        </BarChart>
                    ) : (
                        <LineChart data={visibleData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
                            onMouseMove={e => e.activeTooltipIndex != null && setHoveredMonthIdx(sliceStart + e.activeTooltipIndex)}>
                            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                            <XAxis dataKey="month" tick={{ fill: 'var(--text-3)', fontSize: 11 }} />
                            <YAxis tick={{ fill: 'var(--text-3)', fontSize: 11 }} unit={chartMode === 'growth' ? '%' : ''} />
                            {chartMode === 'growth' && <ReferenceLine y={0} stroke="var(--border-2)" strokeDasharray="4 4" />}
                            <Tooltip content={chartMode === 'growth' ? <GrowthTooltip /> : <CustomTooltip monthIdx={hoveredMonthIdx} />} />
                            <Legend wrapperStyle={{ paddingTop: 12, fontSize: '0.8rem', color: 'var(--text-2)' }} />
                            {activeTechIds.map(id => (
                                <Line key={id} type="monotone" dataKey={id}
                                    stroke={techColorMap[id]} strokeWidth={2} dot={false}
                                    activeDot={{ r: 5, strokeWidth: 0 }}
                                    name={ALL_TECHS.find(t => t.id === id)?.name}
                                />
                            ))}
                        </LineChart>
                    )}
                </ResponsiveContainer>
            </div>

            {/* ── Top 10 ── */}
            <div className="card top10-card" style={{ marginTop: 16 }}>
                <h2 className="section-title">Top 10 Công nghệ Hot nhất</h2>
                <div className="top10-grid">
                    {topTechs.map((t, i) => (
                        <div key={t.id} className={`top10-item${t.growthPct > 30 ? ' hot' : ''}`}>
                            <span className="top10-rank">#{i + 1}</span>
                            <span className="top10-dot" style={{ background: t.color }} />
                            <span className="top10-name">{t.name}</span>
                            <span className={`badge ${t.growthPct > 30 ? 'badge-up' : t.growthPct < 0 ? 'badge-down' : 'badge-flat'}`}>
                                {t.growthPct > 0 ? '+' : ''}{t.growthPct}%
                            </span>
                            <span className="top10-jobs">{t.jobs.toLocaleString()} jobs</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
