'use client';
import AppShell from '@/components/layout/AppShell';
import { useEffect, useState, useRef, useCallback } from 'react';
import { getGraphViz } from '@/lib/api';
import { Network, Loader2, ZoomIn, ZoomOut, Focus, Info } from 'lucide-react';

/* ── Force-directed layout helpers ─────────────────────── */
function initPositions(nodes, W, H) {
  return nodes.map((n, i) => ({
    ...n,
    x: W / 2 + Math.cos((i / nodes.length) * 2 * Math.PI) * (Math.min(W, H) * 0.32),
    y: H / 2 + Math.sin((i / nodes.length) * 2 * Math.PI) * (Math.min(W, H) * 0.32),
    vx: 0, vy: 0,
  }));
}

function runTick(nodes, edges, W, H) {
  const k = 0.012;
  const repulsion = 2800;
  const spring = 0.04;
  const damping = 0.78;
  const ideal = 130;

  const nodeMap = {};
  nodes.forEach(n => (nodeMap[n.id] = n));

  // Repulsion between all pairs
  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      const a = nodes[i], b = nodes[j];
      const dx = b.x - a.x, dy = b.y - a.y;
      const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 1);
      const force = repulsion / (dist * dist);
      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;
      a.vx -= fx; a.vy -= fy;
      b.vx += fx; b.vy += fy;
    }
  }

  // Spring attraction along edges
  edges.forEach(e => {
    const a = nodeMap[e.source || e.from];
    const b = nodeMap[e.target || e.to];
    if (!a || !b) return;
    const dx = b.x - a.x, dy = b.y - a.y;
    const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 1);
    const force = spring * (dist - ideal);
    const fx = (dx / dist) * force;
    const fy = (dy / dist) * force;
    a.vx += fx; a.vy += fy;
    b.vx -= fx; b.vy -= fy;
  });

  // Center gravity
  nodes.forEach(n => {
    n.vx += (W / 2 - n.x) * k;
    n.vy += (H / 2 - n.y) * k;
    n.vx *= damping;
    n.vy *= damping;
    n.x += n.vx;
    n.y += n.vy;
    // Keep in bounds
    n.x = Math.max(40, Math.min(W - 40, n.x));
    n.y = Math.max(40, Math.min(H - 40, n.y));
  });

  return [...nodes];
}

// Maps every node_type / type the backend actually emits
const NODE_TYPES = {
  // Structural
  chapter:    '#4A9FFF',  // blue
  section:    '#F47B6E',  // red  → shown as "Topic" in legend
  // Semantic concept sub-types
  concept:    '#7C5CFC',  // purple (default concept)
  definition: '#4CAF82',  // green → shown as "Term"
  example:    '#4CAF82',  // green (same as term)
  question:   '#F9A825',  // amber
  // Fallback
  default:    '#6366F1',
};

// Human-readable legend labels
const LEGEND = [
  { key: 'concept',    label: 'Concept' },
  { key: 'section',   label: 'Topic'   },
  { key: 'definition',label: 'Term'    },
  { key: 'chapter',   label: 'Chapter' },
  { key: 'question',  label: 'Question'},
];

/** Pick colour for a node — semantic type wins over structural type */
function nodeColor(node) {
  return (
    NODE_TYPES[node.node_type] ||
    NODE_TYPES[node.type]      ||
    NODE_TYPES.default
  );
}

export default function GraphPage() {
  const [rawData, setRawData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState(null);
  const [hovered, setHovered] = useState(null);
  const [simNodes, setSimNodes] = useState([]);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [dragging, setDragging] = useState(null);
  const svgRef = useRef(null);
  const animRef = useRef(null);
  const tickRef = useRef(0);
  const W = 760, H = 500;

  useEffect(() => {
    getGraphViz()
      .then(res => {
        if (res.success) setRawData(res.data);
        else setError('Could not load graph.');
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  // Initialize simulation once data arrives
  useEffect(() => {
    if (!rawData?.nodes?.length) return;
    const positioned = initPositions(rawData.nodes, W, H);
    setSimNodes(positioned);
    tickRef.current = 0;
  }, [rawData]);

  // Run simulation ticks
  useEffect(() => {
    if (!simNodes.length || tickRef.current > 180) return;
    animRef.current = requestAnimationFrame(() => {
      setSimNodes(prev => {
        const next = runTick([...prev], rawData?.edges || [], W, H);
        tickRef.current++;
        return next;
      });
    });
    return () => cancelAnimationFrame(animRef.current);
  }, [simNodes, rawData]);

  const edges = rawData?.edges || [];

  // Drag handlers
  const onNodeMouseDown = useCallback((e, nodeId) => {
    e.stopPropagation();
    setDragging(nodeId);
    setSelected(simNodes.find(n => n.id === nodeId) || null);
  }, [simNodes]);

  const onSvgMouseMove = useCallback((e) => {
    if (!dragging) return;
    const rect = svgRef.current.getBoundingClientRect();
    const x = (e.clientX - rect.left - pan.x) / zoom;
    const y = (e.clientY - rect.top - pan.y) / zoom;
    setSimNodes(prev => prev.map(n => n.id === dragging ? { ...n, x, y, vx: 0, vy: 0 } : n));
    tickRef.current = 0; // restart simulation after drag
  }, [dragging, pan, zoom]);

  const onSvgMouseUp = useCallback(() => setDragging(null), []);

  const zoomIn  = () => setZoom(z => Math.min(z + 0.2, 2.5));
  const zoomOut = () => setZoom(z => Math.max(z - 0.2, 0.4));
  const resetView = () => { setZoom(1); setPan({ x: 0, y: 0 }); };

  if (loading) return <AppShell><div className="flex-center" style={{ padding: '4rem' }}><div className="spinner"/></div></AppShell>;
  if (error)   return <AppShell><div className="error-box" style={{ margin: '2rem' }}>{error}</div></AppShell>;

  if (!rawData?.nodes?.length) return (
    <AppShell>
      <div className="page-header">
        <h1 className="page-title">Knowledge Map 🕸️</h1>
        <p className="page-subtitle">Visual map of concepts extracted from your study notes.</p>
      </div>
      <div className="empty-state">
        <div className="empty-icon"><Network size={48} color="var(--accent)" style={{ opacity: 0.4 }}/></div>
        <p className="empty-text">No knowledge graph yet. Upload a PDF to build your knowledge map!</p>
      </div>
    </AppShell>
  );

  const selNode = selected ? simNodes.find(n => n.id === selected.id) || selected : null;
  const connectedEdges = selNode
    ? edges.filter(e => e.source === selNode.id || e.from === selNode.id || e.target === selNode.id || e.to === selNode.id)
    : [];

  return (
    <AppShell>
      <div className="page-header">
        <h1 className="page-title">Knowledge Map 🕸️</h1>
        <p className="page-subtitle">
          {simNodes.length} nodes · {edges.length} connections — drag nodes to explore, click to inspect.
        </p>
      </div>

      <div style={{ display: 'flex', gap: 'var(--space-lg)', alignItems: 'flex-start' }}>
        {/* Graph Canvas */}
        <div className="card" style={{ flex: 1, padding: 0, overflow: 'hidden', position: 'relative' }}>
          {/* Controls */}
          <div style={{ position: 'absolute', top: 12, right: 12, display: 'flex', flexDirection: 'column', gap: 6, zIndex: 10 }}>
            {[{ icon: ZoomIn, fn: zoomIn, title: 'Zoom in' }, { icon: ZoomOut, fn: zoomOut, title: 'Zoom out' }, { icon: Focus, fn: resetView, title: 'Reset view' }]
              .map(({ icon: Icon, fn, title }) => (
                <button key={title} onClick={fn} title={title} className="btn-icon"
                  style={{ background: 'white', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', boxShadow: 'var(--shadow-sm)', color: 'var(--accent)' }}>
                  <Icon size={16}/>
                </button>
              ))}
          </div>

          <svg ref={svgRef} width="100%" height={H}
            viewBox={`${-pan.x / zoom} ${-pan.y / zoom} ${W / zoom} ${H / zoom}`}
            style={{ display: 'block', cursor: dragging ? 'grabbing' : 'default', background: 'linear-gradient(135deg, #FDF8F0 0%, #F5F0FF 100%)' }}
            onMouseMove={onSvgMouseMove}
            onMouseUp={onSvgMouseUp}
            onMouseLeave={onSvgMouseUp}>

            <defs>
              <marker id="arrow" viewBox="0 0 10 10" refX="20" refY="5"
                markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="rgba(124,92,252,0.3)"/>
              </marker>
              <filter id="glow">
                <feGaussianBlur stdDeviation="3" result="blur"/>
                <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
              </filter>
            </defs>

            {/* Edges */}
            {edges.map((e, i) => {
              const a = simNodes.find(n => n.id === (e.source || e.from));
              const b = simNodes.find(n => n.id === (e.target || e.to));
              if (!a || !b) return null;
              const isHighlit = selNode && (e.source === selNode.id || e.from === selNode.id || e.target === selNode.id || e.to === selNode.id);
              return (
                <g key={i}>
                  <line x1={a.x} y1={a.y} x2={b.x} y2={b.y}
                    stroke={isHighlit ? 'rgba(124,92,252,0.8)' : 'rgba(124,92,252,0.25)'}
                    strokeWidth={isHighlit ? 3 : 1.5}
                    strokeDasharray={isHighlit ? 'none' : '4 3'}
                    markerEnd="url(#arrow)"
                  />
                  {isHighlit && e.label && (
                    <text x={(a.x + b.x) / 2} y={(a.y + b.y) / 2 - 5}
                      textAnchor="middle" fontSize={9} fill="rgba(124,92,252,0.7)" fontWeight="600">
                      {e.label}
                    </text>
                  )}
                </g>
              );
            })}

            {/* Nodes */}
            {simNodes.map(node => {
              const color = nodeColor(node);
              const isSelected = selNode?.id === node.id;
              const isHovered = hovered === node.id;
              const r = isSelected ? 20 : isHovered ? 18 : 16;
              const isConnected = selNode && connectedEdges.some(e =>
                e.source === node.id || e.from === node.id || e.target === node.id || e.to === node.id
              );

              return (
                <g key={node.id} style={{ cursor: 'pointer' }}
                  onMouseEnter={() => setHovered(node.id)}
                  onMouseLeave={() => setHovered(null)}
                  onMouseDown={e => onNodeMouseDown(e, node.id)}>
                  {/* Glow ring on selected */}
                  {isSelected && (
                    <circle cx={node.x} cy={node.y} r={r + 7}
                      fill="none" stroke={color} strokeWidth={2} opacity={0.25} filter="url(#glow)"/>
                  )}
                  {/* Connected highlight ring */}
                  {isConnected && !isSelected && (
                    <circle cx={node.x} cy={node.y} r={r + 4}
                      fill="none" stroke={color} strokeWidth={1.5} opacity={0.3}/>
                  )}
                  {/* Main circle */}
                  <circle cx={node.x} cy={node.y} r={r}
                    fill={isSelected ? color : `${color}22`}
                    stroke={color}
                    strokeWidth={isSelected ? 0 : 2}
                    opacity={selNode && !isSelected && !isConnected ? 0.35 : 1}
                  />
                  {/* Label */}
                  <text x={node.x} y={node.y + r + 15} textAnchor="middle"
                    fontSize={12} fontWeight="600"
                    fill={selNode && !isSelected && !isConnected ? '#ccc' : 'var(--text, #3A3042)'}
                    style={{ pointerEvents: 'none', userSelect: 'none' }}>
                    {(node.label || node.id).slice(0, 18)}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>

        {/* Detail Panel */}
        <div className="card" style={{ width: 260, flexShrink: 0, padding: 'var(--space-lg)', minHeight: 300 }}>
          {selNode ? (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 'var(--space-md)' }}>
                <div style={{ width: 12, height: 12, borderRadius: '50%', background: nodeColor(selNode), flexShrink: 0 }}/>
                <h3 style={{ fontSize: 'var(--fs-base)', color: 'var(--accent)', margin: 0 }}>
                  {selNode.label || selNode.id}
                </h3>
              </div>
              {(selNode.node_type || selNode.type) && (
                <span className="badge" style={{ background: `${nodeColor(selNode)}22`, color: nodeColor(selNode), marginBottom: 'var(--space-md)', display: 'inline-block', textTransform: 'capitalize', border: `1px solid ${nodeColor(selNode)}44` }}>
                  {LEGEND.find(l => l.key === selNode.node_type || l.key === selNode.type)?.label || selNode.node_type || selNode.type}
                </span>
              )}
              {selNode.definition && (
                <p style={{ fontSize: 'var(--fs-sm)', color: 'var(--text-secondary)', lineHeight: 1.7, marginBottom: 'var(--space-md)' }}>
                  {selNode.definition}
                </p>
              )}
              {connectedEdges.length > 0 && (
                <div>
                  <div style={{ fontSize: 'var(--fs-xs)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)', marginBottom: 8 }}>
                    {connectedEdges.length} Connection{connectedEdges.length !== 1 ? 's' : ''}
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {connectedEdges.slice(0, 8).map((e, i) => {
                      const otherId = (e.source === selNode.id || e.from === selNode.id)
                        ? (e.target || e.to) : (e.source || e.from);
                      const other = simNodes.find(n => n.id === otherId);
                      return (
                        <button key={i} onClick={() => setSelected(other)}
                          style={{ textAlign: 'left', background: 'var(--bg-alt)', border: 'none', borderRadius: 'var(--radius-sm)', padding: '0.4rem 0.6rem', cursor: 'pointer', fontSize: 'var(--fs-xs)', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: 6 }}>
                          <span style={{ color: 'var(--accent)', flexShrink: 0 }}>→</span>
                          <span style={{ fontWeight: 600 }}>{other?.label || otherId}</span>
                          {e.label && <span style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>({e.label})</span>}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: 'var(--space-xl) 0' }}>
              <Info size={32} color="var(--accent)" style={{ opacity: 0.3, marginBottom: 12 }}/>
              <p style={{ color: 'var(--text-muted)', fontSize: 'var(--fs-sm)', lineHeight: 1.6 }}>
                Click any node to see details and connections.
              </p>
              <div style={{ marginTop: 'var(--space-lg)', display: 'flex', flexDirection: 'column', gap: 8, textAlign: 'left' }}>
                {LEGEND.map(({ key, label }) => (
                  <div key={key} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 'var(--fs-xs)', color: 'var(--text-muted)' }}>
                    <div style={{ width: 10, height: 10, borderRadius: '50%', background: NODE_TYPES[key], flexShrink: 0 }}/>
                    <span style={{ fontWeight: 600 }}>{label}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Stats footer */}
      <div style={{ display: 'flex', gap: 'var(--space-lg)', marginTop: 'var(--space-lg)' }}>
        {[
          { label: 'Total Nodes', value: simNodes.length },
          { label: 'Connections', value: edges.length },
          { label: 'Node Types', value: [...new Set(simNodes.map(n => n.node_type || n.type).filter(Boolean))].length || '—' },
        ].map(({ label, value }) => (
          <div key={label} className="card" style={{ flex: 1, padding: 'var(--space-md)', textAlign: 'center' }}>
            <div style={{ fontSize: 'var(--fs-2xl)', fontWeight: 800, color: 'var(--accent)' }}>{value}</div>
            <div style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginTop: 2 }}>{label}</div>
          </div>
        ))}
      </div>
    </AppShell>
  );
}
