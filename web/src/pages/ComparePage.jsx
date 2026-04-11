import { useState } from 'react';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
    Legend, ResponsiveContainer, ReferenceLine, Label
} from 'recharts';
import Select from 'react-select';
import { growthData, timelineData, ALL_TECHS, MONTHS_24, getPeakMonth, getSaturationMonth } from '../data/trendMock';
import './ComparePage.css';

const TECH_OPTIONS = ALL_TECHS.map(t => ({ value: t.id, label: t.name, color: t.color }));

const selectStyles = {
    control: (b) => ({ ...b, background: 'var(--surface-2)', borderColor: 'var(--border)', color: 'var(--text)', minHeight: 38, boxShadow: 'none', '&:hover': { borderColor: 'var(--primary)' } }),
    menu: (b) => ({ ...b, background: 'var(--surface-2)', border: '1px solid var(--border)', zIndex: 200 }),
    option: (b, s) => ({ ...b, background: s.isFocused ? 'var(--surface)' : 'transparent', color: 'var(--text)', cursor: 'pointer' }),
    multiValue: (b) => ({ ...b, background: 'var(--primary-glow)', borderRadius: 4 }),
    multiValueLabel: (b) => ({ ...b, color: 'var(--primary-light)' }),
    multiValueRemove: (b) => ({ ...b, color: 'var(--primary-light)', '&:hover': { background: 'var(--primary)', color: '#fff' } }),
    input: (b) => ({ ...b, color: 'var(--text)' }),
    placeholder: (b) => ({ ...b, color: 'var(--text-3)' }),
};

function CompareTooltip({ active, payload, label }) {
    if (!active || !payload?.length) return null;
    return (
        <div className="chart-tooltip">
            <p className="tooltip-month">{label}</p>
            {payload.map(p => (
                <div key={p.dataKey} className="tooltip-row">
                    <span className="tooltip-dot" style={{ background: p.color }} />
                    <span className="tooltip-tech">{ALL_TECHS.find(t => t.id === p.dataKey)?.name || p.dataKey}</span>
                    <span className={`tooltip-jobs ${p.value >= 0 ? 'up' : 'down'}`}>{p.value >= 0 ? '+' : ''}{p.value}%</span>
                </div>
            ))}
        </div>
    );
}

export default function ComparePage() {

    const [selectedTechs, setSelectedTechs] = useState(TECH_OPTIONS.slice(0, 3));
    const [timeRange, setTimeRange] = useState(12);
    const [showAnnotations, setShowAnnotations] = useState(true);

    const sliceStart = Math.max(0, 24 - timeRange);
    const visibleData = growthData.slice(sliceStart);
    const activeTechIds = selectedTechs.map(t => t.value);
    const techColorMap = Object.fromEntries(ALL_TECHS.map(t => [t.id, t.color]));

    // Stats per selected tech
    const statsArr = activeTechIds.map(id => {
        const last = growthData[23][id];
        const half = growthData[11][id];
        const tech = ALL_TECHS.find(t => t.id === id);
        const jobs24 = timelineData[23][id];
        const jobs0 = timelineData[0][id];
        return {
            id, name: tech?.name || id, color: tech?.color || '#fff',
            yoy: last - half,
            mom: growthData[23][id] - growthData[22][id],
            total: Math.round(last),
            jobs: jobs24,
            peak: getPeakMonth(id),
            saturation: getSaturationMonth(id),
        };
    });

    return (
        <div className="compare-page">
            {/* Controls */}
            <div className="card compare-controls">
                <div className="control-group" style={{ flex: 1, maxWidth: 500 }}>
                    <label className="control-label">Chọn công nghệ (2–5)</label>
                    <Select isMulti options={TECH_OPTIONS} value={selectedTechs}
                        onChange={v => { if (v.length <= 5) setSelectedTechs(v); }}
                        styles={selectStyles} placeholder="Chọn công nghệ..." closeMenuOnSelect={false} />
                </div>
                <div className="control-group">
                    <label className="control-label">Thời gian</label>
                    <div className="pill-group">
                        {[3, 6, 12, 24].map(v => (
                            <button key={v} className={`pill${timeRange === v ? ' active' : ''}`}
                                onClick={() => setTimeRange(v)}>{v} tháng</button>
                        ))}
                    </div>
                </div>
                <div className="control-group">
                    <label className="control-label">Chú thích</label>
                    <button className={`pill${showAnnotations ? ' active' : ''}`}
                        onClick={() => setShowAnnotations(a => !a)}>
                        {showAnnotations ? 'Hiện Peak & Saturation' : 'Ẩn'}
                    </button>
                </div>
            </div>

            {/* Stats cards */}
            <div className="compare-stats-row" style={{ marginTop: 16 }}>
                {statsArr.map(s => (
                    <div key={s.id} className="compare-stat-card" style={{ borderColor: s.color + '55' }}>
                        <div className="cs-header">
                            <span className="cs-dot" style={{ background: s.color }} />
                            <span className="cs-name">{s.name}</span>
                        </div>
                        <div className="cs-big">+{s.total}%</div>
                        <div className="cs-meta-row">
                            <div className="cs-meta"><span>YoY</span><strong className={s.yoy >= 0 ? 'up' : 'down'}>{s.yoy >= 0 ? '+' : ''}{Math.round(s.yoy)}%</strong></div>
                            <div className="cs-meta"><span>MoM</span><strong className={s.mom >= 0 ? 'up' : 'down'}>{s.mom >= 0 ? '+' : ''}{Math.round(s.mom)}%</strong></div>
                            <div className="cs-meta"><span>Jobs</span><strong>{s.jobs?.toLocaleString()}</strong></div>
                        </div>
                        {s.peak && <div className="cs-annotation">Peak: {s.peak.month} ({s.peak.value?.toLocaleString()} jobs)</div>}
                        {s.saturation && <div className="cs-annotation">Bão hòa: {s.saturation.month}</div>}
                    </div>
                ))}
            </div>

            {/* Overlay chart */}
            <div className="card" style={{ marginTop: 16 }}>
                <h2 className="section-title">So sánh % Tăng trưởng (so với tháng đầu)</h2>
                <ResponsiveContainer width="100%" height={380}>
                    <LineChart data={visibleData} margin={{ top: 10, right: 20, left: 10, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                        <XAxis dataKey="month" tick={{ fill: 'var(--text-3)', fontSize: 11 }} />
                        <YAxis unit="%" tick={{ fill: 'var(--text-3)', fontSize: 11 }} />
                        <ReferenceLine y={0} stroke="var(--border-2)" strokeDasharray="4 4" />
                        <Tooltip content={<CompareTooltip />} />
                        <Legend wrapperStyle={{ fontSize: '0.8rem', color: 'var(--text-2)', paddingTop: 12 }} />
                        {activeTechIds.map(id => {
                            const peak = getPeakMonth(id);
                            const sat = getSaturationMonth(id);
                            const peakMonthLabel = peak?.month;
                            const satMonthLabel = sat?.month;
                            return (
                                <Line key={id} type="monotone" dataKey={id}
                                    stroke={techColorMap[id]} strokeWidth={2.5} dot={false}
                                    activeDot={{ r: 5, strokeWidth: 0 }}
                                    name={ALL_TECHS.find(t => t.id === id)?.name}
                                />
                            );
                        })}
                        {showAnnotations && activeTechIds.flatMap(id => {
                            const peak = getPeakMonth(id);
                            const sat = getSaturationMonth(id);
                            const color = techColorMap[id];
                            const refs = [];
                            if (peak) refs.push(
                                <ReferenceLine key={`peak-${id}`} x={peak.month} stroke={color} strokeDasharray="6 3" strokeOpacity={0.7}>
                                    <Label value="Peak" position="top" fill={color} fontSize={10} />
                                </ReferenceLine>
                            );
                            if (sat) refs.push(
                                <ReferenceLine key={`sat-${id}`} x={sat.month} stroke="#FFC94D" strokeDasharray="3 5" strokeOpacity={0.6}>
                                    <Label value="Sat." position="insideTopRight" fill="#FFC94D" fontSize={10} />
                                </ReferenceLine>
                            );
                            return refs;
                        })}
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
