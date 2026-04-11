import { useState, useEffect, useCallback, useRef } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { ALL_NODES, ALL_LINKS, NODE_TYPES, buildSubgraph, searchNodes, nodeIndex, findPath } from '../data/graphMock';
import './GraphExplorer.css';

const LINK_TYPE_COLORS = {
    USES: '#6C63FF',
    REQUIRES: '#00D68F',
    LOCATED_IN: '#FFC94D',
    RELATED_TO: '#FF6584',
    TAGGED_WITH: '#54C5F8',
};

export default function GraphExplorer() {

    const fgRef = useRef();
    const [graphData, setGraphData] = useState({ nodes: [], links: [] });
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [selectedEdge, setSelectedEdge] = useState(null);
    const [hoveredNode, setHoveredNode] = useState(null);
    const [filterOpen, setFilterOpen] = useState(false);
    const [filters, setFilters] = useState({ salary: 0, sentiment: 0, location: 'all' });
    const [focusNodeId, setFocusNodeId] = useState(null);
    const [depth, setDepth] = useState(1);
    const [nodeCount, setNodeCount] = useState(0);
    const [activeFeature, setActiveFeature] = useState('explore'); // 'explore' or 'journey'
    const [pathStart, setPathStart] = useState(null);
    const [pathEnd, setPathEnd] = useState(null);
    const [activePath, setActivePath] = useState(null);
    const [journeyStartQuery, setJourneyStartQuery] = useState('');
    const [journeyEndQuery, setJourneyEndQuery] = useState('');
    const [journeyStartResults, setJourneyStartResults] = useState([]);
    const [journeyEndResults, setJourneyEndResults] = useState([]);

    // Load initial graph centered on Golang
    useEffect(() => {
        loadGraph('tech_golang', 1);
    }, []);

    // Adjust force simulation for longer links and more space
    useEffect(() => {
        if (fgRef.current) {
            fgRef.current.d3Force('link').distance(200); // Tăng lên 200 để dãn cực đại
            fgRef.current.d3Force('charge').strength(-500); // Tăng lực đẩy mạnh hơn để tránh chồng lấn
            fgRef.current.d3ReheatSimulation(); // Khởi động lại simulation để áp dụng lực mới
        }
    }, [graphData]);

    function loadGraph(nodeId, d = depth) {
        const sub = buildSubgraph(nodeId, d, 80);
        setGraphData({ nodes: sub.nodes.map(n => ({ ...n })), links: sub.links.map(l => ({ ...l })) });
        setNodeCount(sub.nodes.length);
        setFocusNodeId(nodeId);
    }

    function loadMore(nodeId) {
        const sub = buildSubgraph(nodeId, 2, 120);
        setGraphData({ nodes: sub.nodes.map(n => ({ ...n })), links: sub.links.map(l => ({ ...l })) });
        setNodeCount(sub.nodes.length);
    }

    // Search
    useEffect(() => {
        if (searchQuery.length > 0) setSearchResults(searchNodes(searchQuery));
        else setSearchResults([]);
    }, [searchQuery]);

    const handleSearch = (node) => {
        setSearchQuery(node.label);
        setSearchResults([]);
        loadGraph(node.id, depth);
        setTimeout(() => {
            if (fgRef.current) fgRef.current.centerAt(0, 0, 400);
        }, 300);
    };

    // Journey search handlers
    useEffect(() => {
        if (journeyStartQuery.length > 0) setJourneyStartResults(searchNodes(journeyStartQuery));
        else setJourneyStartResults([]);
    }, [journeyStartQuery]);

    useEffect(() => {
        if (journeyEndQuery.length > 0) setJourneyEndResults(searchNodes(journeyEndQuery));
        else setJourneyEndResults([]);
    }, [journeyEndQuery]);

    const handleJourneySelectStart = (node) => {
        setPathStart(node);
        setJourneyStartQuery(node.label);
        setJourneyStartResults([]);
        // Show the node on the graph too
        const sub = buildSubgraph(node.id, 1, 80);
        setGraphData({ nodes: sub.nodes.map(n => ({ ...n })), links: sub.links.map(l => ({ ...l })) });
        setFocusNodeId(node.id);
        // Recalculate path if end is already set
        if (pathEnd) {
            const path = findPath(node.id, pathEnd.id);
            setActivePath(path);
        }
    };

    const handleJourneySelectEnd = (node) => {
        setPathEnd(node);
        setJourneyEndQuery(node.label);
        setJourneyEndResults([]);
        // Calculate path
        if (pathStart) {
            const path = findPath(pathStart.id, node.id);
            setActivePath(path);
        }
    };

    const handleReset = () => {
        loadGraph('tech_golang', 1);
        setSearchQuery('');
        setSelectedEdge(null);
        setPathStart(null);
        setPathEnd(null);
        setActivePath(null);
        setJourneyStartQuery('');
        setJourneyEndQuery('');
        setFilters({ salary: 0, sentiment: 0, location: 'all' });
    };

    const handleFocusNode = () => {
        if (fgRef.current && focusNodeId) fgRef.current.centerAt(0, 0, 600);
    };

    const toggleFeature = (feat) => {
        setActiveFeature(feat);
        if (feat === 'explore') {
            setPathStart(null);
            setPathEnd(null);
            setActivePath(null);
        }
    };

    // Filter nodes visibility
    const isNodeVisible = useCallback((node) => {
        if (node.type === 'company') {
            if (filters.salary > 0 && (node.avg_salary || 0) < filters.salary) return false;
            if (filters.location !== 'all' && node.location !== filters.location) return false;
        }
        if (node.type === 'technology') {
            if (filters.sentiment > 0 && (node.sentiment || 0) < filters.sentiment) return false;
        }
        return true;
    }, [filters]);

    // Node canvas paint
    const paintNode = useCallback((node, ctx, globalScale) => {
        const nt = NODE_TYPES[node.type] || { color: '#9FA8C7', size: 8 };
        const visible = isNodeVisible(node);
        const isCenter = node.id === focusNodeId;
        const isPathNode = activeFeature === 'journey' && activePath?.nodes.some(n => n.id === node.id);
        const r = nt.size + (isCenter ? 4 : 0);

        ctx.globalAlpha = visible ? 1 : 0.15;
        if (isCenter) {
            ctx.shadowBlur = 16; ctx.shadowColor = nt.color;
        }
        if (isPathNode) {
            ctx.shadowBlur = 20; ctx.shadowColor = '#FFD700';
            ctx.lineWidth = 2 / globalScale;
            ctx.strokeStyle = '#FFD700';
        }

        ctx.beginPath();
        ctx.arc(node.x, node.y, r, 0, 2 * Math.PI);
        ctx.fillStyle = nt.color;
        ctx.fill();

        if (isPathNode) ctx.stroke();

        ctx.shadowBlur = 0;

        if (globalScale >= 0.8) {
            ctx.font = `600 ${Math.min(14 / globalScale, 12)}px Inter, sans-serif`;
            ctx.fillStyle = '#E8EAF6';
            ctx.textAlign = 'center';
            ctx.fillText(node.label, node.x, node.y + r + 10);
        }
        ctx.globalAlpha = 1;
    }, [focusNodeId, isNodeVisible, activePath, activeFeature]);

    const handleNodeClick = useCallback((node) => {
        setSelectedEdge(null);

        if (activeFeature === 'journey') {
            if (!pathStart) {
                setPathStart(node);
            } else if (!pathEnd && pathStart.id !== node.id) {
                setPathEnd(node);
                const path = findPath(pathStart.id, node.id);
                setActivePath(path);
            } else {
                setPathStart(node);
                setPathEnd(null);
                setActivePath(null);
            }
        } else {
            loadGraph(node.id, depth);
            if (fgRef.current) {
                fgRef.current.centerAt(node.x, node.y, 600);
                fgRef.current.zoom(2, 800);
            }
        }
    }, [depth, pathStart, pathEnd, activeFeature]);

    const handleNodeHover = useCallback((node) => {
        setHoveredNode(node || null);
        document.body.style.cursor = node ? 'pointer' : 'default';
    }, []);

    const handleLinkClick = useCallback((link) => {
        setSelectedEdge(link);
    }, []);

    const isLinkInPath = useCallback((link) => {
        if (activeFeature !== 'journey' || !activePath) return false;
        return activePath.links.some(l =>
            (l.source === link.source.id && l.target === link.target.id) ||
            (l.source === link.target.id && l.target === link.source.id)
        );
    }, [activePath, activeFeature]);

    const linkColor = useCallback((link) => isLinkInPath(link) ? '#FFD700' : (LINK_TYPE_COLORS[link.type] || '#5c6494'), [isLinkInPath]);
    const linkWidth = useCallback((link) => isLinkInPath(link) ? 5 : (selectedEdge === link ? 3 : 1.2), [selectedEdge, isLinkInPath]);

    // Link canvas paint for labels
    const paintLink = useCallback((link, ctx, globalScale) => {
        if (globalScale < 1.2) return; // Hiển thị sớm hơn (từ 1.2 thay vì 1.5)

        const start = link.source;
        const end = link.target;
        if (typeof start !== 'object' || typeof end !== 'object') return;

        const label = link.label || link.type;
        const fontSize = 18 / globalScale; // Tăng lên 18 để cực kỳ dễ đọc
        ctx.font = `bold ${fontSize}px Inter, sans-serif`; // Dùng bold luôn
        const textWidth = ctx.measureText(label).width;

        const textPos = {
            x: start.x + (end.x - start.x) / 2,
            y: start.y + (end.y - start.y) / 2
        };

        const relAngle = Math.atan2(end.y - start.y, end.x - start.x);

        // Keep text upright
        let rotation = relAngle;
        if (rotation > Math.PI / 2) rotation -= Math.PI;
        if (rotation < -Math.PI / 2) rotation += Math.PI;

        ctx.save();
        ctx.translate(textPos.x, textPos.y);
        ctx.rotate(rotation);

        // Draw background pill
        ctx.fillStyle = 'rgba(13, 15, 26, 0.85)'; // Tăng opacity nền
        ctx.beginPath();
        const padding = 3 / globalScale; // Tăng padding
        const h = fontSize + padding * 2;
        const w = textWidth + padding * 4;
        ctx.roundRect(-w / 2, -h / 2, w, h, 3 / globalScale);
        ctx.fill();

        // Draw text
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillStyle = LINK_TYPE_COLORS[link.type] || '#9FA8C7';
        ctx.fillText(label, 0, 0);
        ctx.restore();
    }, []);

    const locations = ['all', 'Hồ Chí Minh', 'Hà Nội', 'Đà Nẵng'];

    return (
        <div className="graph-page">
            {/* Search bar & Feature Switcher */}
            <div className="graph-search-bar card">
                <div className="feature-switcher-tabs">
                    <button className={`feat-tab${activeFeature === 'explore' ? ' active' : ''}`} onClick={() => toggleFeature('explore')}>
                        <span className="feat-icon">&#128269;</span> Khám phá
                    </button>
                    <button className={`feat-tab${activeFeature === 'journey' ? ' active' : ''}`} onClick={() => toggleFeature('journey')}>
                        <span className="feat-icon">&#128739;</span> Phân tích lộ trình
                    </button>
                </div>

                {activeFeature === 'explore' ? (
                    <div className="search-input-wrap">
                        <span className="search-icon">&#128269;</span>
                        <input
                            className="search-input"
                            placeholder="Tìm node: Golang, VNG, Docker..."
                            value={searchQuery}
                            onChange={e => setSearchQuery(e.target.value)}
                        />
                        {searchResults.length > 0 && (
                            <div className="search-dropdown">
                                {searchResults.map(n => (
                                    <button key={n.id} className="search-result-item" onClick={() => handleSearch(n)}>
                                        <span className="srd-type-badge" style={{ background: NODE_TYPES[n.type]?.color + '33', color: NODE_TYPES[n.type]?.color }}>
                                            {n.type}
                                        </span>
                                        {n.label}
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                ) : (
                    <div className="journey-search-row">
                        {/* Start node */}
                        <div className="journey-search-field">
                            <label className="journey-search-label">
                                <span className="journey-tag start">Xuất phát</span>
                                {pathStart && <span className="journey-selected-badge" style={{ background: NODE_TYPES[pathStart.type]?.color + '33', color: NODE_TYPES[pathStart.type]?.color }}>✓ {pathStart.label}</span>}
                            </label>
                            <div className="search-input-wrap">
                                <span className="search-icon">&#128205;</span>
                                <input
                                    className="search-input"
                                    placeholder="Tìm điểm đi: Golang, VNG..."
                                    value={journeyStartQuery}
                                    onChange={e => setJourneyStartQuery(e.target.value)}
                                />
                                {journeyStartResults.length > 0 && (
                                    <div className="search-dropdown">
                                        {journeyStartResults.map(n => (
                                            <button key={n.id} className="search-result-item" onClick={() => handleJourneySelectStart(n)}>
                                                <span className="srd-type-badge" style={{ background: NODE_TYPES[n.type]?.color + '33', color: NODE_TYPES[n.type]?.color }}>{n.type}</span>
                                                {n.label}
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>

                        <div className="journey-arrow">→</div>

                        {/* End node */}
                        <div className="journey-search-field">
                            <label className="journey-search-label">
                                <span className="journey-tag end">Điểm đến</span>
                                {pathEnd && <span className="journey-selected-badge" style={{ background: NODE_TYPES[pathEnd.type]?.color + '33', color: NODE_TYPES[pathEnd.type]?.color }}>✓ {pathEnd.label}</span>}
                            </label>
                            <div className="search-input-wrap">
                                <span className="search-icon">&#127937;</span>
                                <input
                                    className="search-input"
                                    placeholder="Tìm điểm đến: Docker, Hà Nội..."
                                    value={journeyEndQuery}
                                    onChange={e => setJourneyEndQuery(e.target.value)}
                                />
                                {journeyEndResults.length > 0 && (
                                    <div className="search-dropdown">
                                        {journeyEndResults.map(n => (
                                            <button key={n.id} className="search-result-item" onClick={() => handleJourneySelectEnd(n)}>
                                                <span className="srd-type-badge" style={{ background: NODE_TYPES[n.type]?.color + '33', color: NODE_TYPES[n.type]?.color }}>{n.type}</span>
                                                {n.label}
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Clear button */}
                        {(pathStart || pathEnd) && (
                            <button className="btn btn-ghost" style={{ alignSelf: 'flex-end' }} onClick={() => { setPathStart(null); setPathEnd(null); setActivePath(null); setJourneyStartQuery(''); setJourneyEndQuery(''); }}>
                                ✕ Xóa
                            </button>
                        )}
                    </div>
                )}

                <div className="graph-controls">
                    <div className="control-group-inline">
                        <label className="control-label">Depth</label>
                        <div className="pill-group">
                            <button className={`pill${depth === 1 ? ' active' : ''}`} onClick={() => { setDepth(1); focusNodeId && loadGraph(focusNodeId, 1); }}>1 hop</button>
                            <button className={`pill${depth === 2 ? ' active' : ''}`} onClick={() => { setDepth(2); focusNodeId && loadGraph(focusNodeId, 2); }}>2 hops</button>
                        </div>
                    </div>
                    <button className="btn btn-ghost" onClick={() => setFilterOpen(o => !o)}>Lọc</button>
                    <button className="btn btn-ghost" onClick={handleFocusNode}>Focus</button>
                    <button className="btn btn-secondary" onClick={handleReset}>Reset</button>
                </div>
            </div>

            <div className="graph-body">
                {/* Filter panel */}
                {filterOpen && (
                    <div className="filter-panel card">
                        <h3 className="filter-title">Bộ lọc</h3>

                        <div className="filter-group">
                            <label className="filter-label">Lương tối thiểu (triệu)</label>
                            <div className="filter-slider-row">
                                <input type="range" min={0} max={60} step={5} value={filters.salary}
                                    onChange={e => setFilters(f => ({ ...f, salary: +e.target.value }))} />
                                <span className="filter-val">{filters.salary > 0 ? `>${filters.salary}tr` : 'Tất cả'}</span>
                            </div>
                        </div>

                        <div className="filter-group">
                            <label className="filter-label">Sentiment tối thiểu</label>
                            <div className="filter-slider-row">
                                <input type="range" min={0} max={100} step={5} value={filters.sentiment}
                                    onChange={e => setFilters(f => ({ ...f, sentiment: +e.target.value }))} />
                                <span className="filter-val">{filters.sentiment > 0 ? `>${filters.sentiment}%` : 'Tất cả'}</span>
                            </div>
                        </div>

                        <div className="filter-group">
                            <label className="filter-label">Địa điểm</label>
                            <div className="pill-group" style={{ flexWrap: 'wrap' }}>
                                {locations.map(loc => (
                                    <button key={loc} className={`pill${filters.location === loc ? ' active' : ''}`}
                                        onClick={() => setFilters(f => ({ ...f, location: loc }))}>
                                        {loc === 'all' ? 'Tất cả' : loc}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <button className="btn btn-ghost w-full mt-16" style={{ justifyContent: 'center' }}
                            onClick={() => setFilters({ salary: 0, sentiment: 0, location: 'all' })}>
                            Xóa bộ lọc
                        </button>
                    </div>
                )}

                {/* Graph canvas */}
                <div className="graph-canvas-wrapper">
                    <ForceGraph2D
                        ref={fgRef}
                        graphData={graphData}
                        nodeCanvasObject={paintNode}
                        nodeCanvasObjectMode={() => 'replace'}
                        onNodeClick={handleNodeClick}
                        onNodeHover={handleNodeHover}
                        onLinkClick={handleLinkClick}
                        linkColor={linkColor}
                        linkWidth={linkWidth}
                        linkCanvasObject={paintLink}
                        linkCanvasObjectMode={() => 'after'}
                        linkDirectionalArrowLength={5}
                        linkDirectionalArrowRelPos={1}
                        backgroundColor="#0d0f1a"
                        width={undefined}
                        height={undefined}
                    />

                    {/* Path selection hint */}
                    {pathStart && !pathEnd && (
                        <div className="path-hint-badge">
                            Chọn điểm kết thúc để xem lộ trình từ <b>{pathStart.label}</b>...
                        </div>
                    )}

                    {/* Node tooltip */}
                    {hoveredNode && (
                        <div className="node-tooltip">
                            <div className="nt-header">
                                <span className="nt-type-badge" style={{ background: NODE_TYPES[hoveredNode.type]?.color + '33', color: NODE_TYPES[hoveredNode.type]?.color }}>
                                    {hoveredNode.type}
                                </span>
                                <strong>{hoveredNode.label}</strong>
                            </div>
                            {hoveredNode.jobs != null && <div className="nt-row">Jobs: <b>{hoveredNode.jobs?.toLocaleString()}</b></div>}
                            {hoveredNode.avg_salary != null && <div className="nt-row">Lương TB: <b>{hoveredNode.avg_salary}tr</b></div>}
                            {hoveredNode.sentiment != null && <div className="nt-row">Sentiment: <b>{Math.round(hoveredNode.sentiment * 100)}%</b></div>}
                            {hoveredNode.growth != null && <div className="nt-row">Tăng trưởng: <b>+{hoveredNode.growth}%</b></div>}
                            {hoveredNode.location && <div className="nt-row">{hoveredNode.location}</div>}
                            <div className="nt-hint">{!pathStart ? 'Click để chọn làm điểm xuất phát' : 'Click để chọn làm điểm kết thúc'}</div>
                        </div>
                    )}

                    {/* Node count badge */}
                    <div className="graph-stats-badge">
                        <span>{nodeCount} nodes</span>
                        {nodeCount >= 80 && (
                            <button className="btn btn-primary" style={{ fontSize: '0.75rem', padding: '4px 10px' }}
                                onClick={() => focusNodeId && loadMore(focusNodeId)}>
                                Load more
                            </button>
                        )}
                    </div>

                    {/* Legend */}
                    <div className="graph-legend">
                        {Object.entries(NODE_TYPES).map(([type, cfg]) => (
                            <div key={type} className="legend-item">
                                <span className="legend-dot" style={{ background: cfg.color }} />
                                <span>{type.charAt(0).toUpperCase() + type.slice(1)}</span>
                            </div>
                        ))}
                        <div className="legend-sep" />
                        {Object.entries(LINK_TYPE_COLORS).map(([type, color]) => (
                            <div key={type} className="legend-item">
                                <span className="legend-line" style={{ background: color }} />
                                <span>{type}</span>
                            </div>
                        ))}
                        {activePath && (
                            <div className="legend-item">
                                <span className="legend-line" style={{ background: '#FFD700', height: '4px' }} />
                                <span style={{ color: '#FFD700', fontWeight: 'bold' }}>Lộ trình</span>
                            </div>
                        )}
                    </div>
                </div>

                <div className="graph-side-panels">
                    {/* Journey summary panel */}
                    {activePath && (
                        <div className="journey-panel card">
                            <div className="jp-header">
                                <h3>Lộ trình kết nối</h3>
                                <button className="btn btn-ghost" style={{ padding: '4px' }} onClick={() => { setPathStart(null); setPathEnd(null); setActivePath(null); }}>✕</button>
                            </div>
                            <div className="jp-body">
                                <div className="jp-summary">
                                    Từ <b>{pathStart?.label}</b> đến <b>{pathEnd?.label}</b>
                                </div>
                                <div className="jp-steps">
                                    {activePath.links.map((link, i) => {
                                        const source = activePath.nodes[i];
                                        const target = activePath.nodes[i + 1];
                                        return (
                                            <div key={i} className="jp-step">
                                                <div className="jp-step-node">
                                                    <span className="jp-step-dot" style={{ background: NODE_TYPES[source.type]?.color }} />
                                                    {source.label}
                                                </div>
                                                <div className="jp-step-link" style={{ borderLeftColor: LINK_TYPE_COLORS[link.type] }}>
                                                    <span className="jp-step-label">{link.label || link.type}</span>
                                                </div>
                                                {i === activePath.links.length - 1 && (
                                                    <div className="jp-step-node">
                                                        <span className="jp-step-dot" style={{ background: NODE_TYPES[target.type]?.color }} />
                                                        {target.label}
                                                    </div>
                                                )}
                                            </div>
                                        );
                                    })}
                                </div>
                                <button className="btn btn-primary w-full mt-16" onClick={() => {
                                    if (fgRef.current && activePath.nodes.length > 0) {
                                        fgRef.current.centerAt(0, 0, 800);
                                        fgRef.current.zoom(1.2, 800);
                                    }
                                }}>
                                    Xem toàn cảnh lộ trình
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Edge detail panel */}
                    {selectedEdge && (
                        <div className="edge-panel card">
                            <div className="ep-header">
                                <h3>Chi tiết mối quan hệ</h3>
                                <button className="btn btn-ghost" style={{ padding: '4px 8px' }} onClick={() => setSelectedEdge(null)}>✕</button>
                            </div>
                            <div className="ep-body">
                                <div className="ep-row">
                                    <span className="ep-label">Nguồn</span>
                                    <span className="ep-val">{nodeIndex[selectedEdge.source?.id || selectedEdge.source]?.label}</span>
                                </div>
                                <div className="ep-row">
                                    <span className="ep-label">Quan hệ</span>
                                    <span className="ep-type" style={{ color: LINK_TYPE_COLORS[selectedEdge.type] }}>{selectedEdge.type}</span>
                                </div>
                                <div className="ep-row">
                                    <span className="ep-label">Đích</span>
                                    <span className="ep-val">{nodeIndex[selectedEdge.target?.id || selectedEdge.target]?.label}</span>
                                </div>
                                {selectedEdge.label && (
                                    <div className="ep-desc">{selectedEdge.label}</div>
                                )}
                                {selectedEdge.job_count && <div className="ep-row"><span className="ep-label">Số job</span><span className="ep-val">{selectedEdge.job_count}</span></div>}
                                {selectedEdge.period && <div className="ep-row"><span className="ep-label">Trong</span><span className="ep-val">{selectedEdge.period}</span></div>}
                                {selectedEdge.weight && <div className="ep-row"><span className="ep-label">Trọng số</span><span className="ep-val">{selectedEdge.weight}</span></div>}
                                {selectedEdge.similarity && <div className="ep-row"><span className="ep-label">Độ tương đồng</span><span className="ep-val">{selectedEdge.similarity}</span></div>}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
