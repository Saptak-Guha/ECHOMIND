import { useEffect, useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { GlassPanel, NeuralLoader, EmptyState, PageHeader, staggerContainer, staggerItem } from '../components/ui';
import { graphAPI } from '../api';

const nodeColors: Record<string, string> = {
  person: '#6366f1', project: '#0ea5e9', event: '#f59e0b',
  interest: '#22c55e', goal: '#ef4444', experience: '#a855f7',
  skill: '#ec4899', organization: '#14b8a6', location: '#f97316', concept: '#64748b',
};

interface GraphNode {
  id: string;
  label: string;
  node_type: string;
  importance: number;
  properties?: Record<string, unknown>;
}

interface GraphEdge {
  id: string;
  source: string;
  target: string;
  relationship_type: string;
  weight: number;
}

const VIEW_W = 780;
const VIEW_H = 390;

/**
 * Lay nodes out on concentric rings ordered by importance: the entities the
 * twin cares about most sit near the centre, everything else orbits outward.
 * A deterministic layout beats a physics sim here — it is stable across
 * refreshes and costs nothing to compute.
 */
function useRadialLayout(nodes: GraphNode[]) {
  return useMemo(() => {
    const cx = VIEW_W / 2;
    const cy = VIEW_H / 2;
    const ranked = [...nodes].sort((a, b) => (b.importance || 0) - (a.importance || 0));
    const positions = new Map<string, { x: number; y: number; r: number }>();

    ranked.forEach((node, i) => {
      if (i === 0 && ranked.length > 3) {
        positions.set(node.id, { x: cx, y: cy, r: 24 });
        return;
      }
      const offset = ranked.length > 3 ? 1 : 0;
      const idx = i - offset;
      // Ring 0 holds 6, each ring outward holds 6 more.
      let ring = 0;
      let remaining = idx;
      while (remaining >= (ring + 1) * 6) {
        remaining -= (ring + 1) * 6;
        ring += 1;
      }
      const perRing = (ring + 1) * 6;
      const radius = 105 + ring * 92;
      // Stagger alternate rings so nodes do not line up spoke-on-spoke.
      const angle = (remaining / perRing) * Math.PI * 2 + (ring % 2 ? Math.PI / perRing : 0);
      positions.set(node.id, {
        x: cx + Math.cos(angle) * radius,
        y: cy + Math.sin(angle) * radius * 0.58, // squashed: the panel is wider than tall
        r: 10 + (node.importance || 0.5) * 12,
      });
    });

    return positions;
  }, [nodes]);
}

export default function KnowledgeGraph() {
  const [graphData, setGraphData] = useState<{ nodes: GraphNode[]; edges: GraphEdge[] }>({ nodes: [], edges: [] });
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [hovered, setHovered] = useState<string | null>(null);

  useEffect(() => {
    graphAPI.getVisualization()
      .then((res) => setGraphData({ nodes: res.data.nodes ?? [], edges: res.data.edges ?? [] }))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const positions = useRadialLayout(graphData.nodes);

  const filteredNodes = graphData.nodes.filter((n) =>
    !searchQuery || n.label.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  // Neighbours of the focused node, so hovering dims everything unrelated.
  const focusId = hovered || selectedNode?.id || null;
  const connected = useMemo(() => {
    if (!focusId) return null;
    const set = new Set<string>([focusId]);
    graphData.edges.forEach((e) => {
      if (e.source === focusId) set.add(e.target);
      if (e.target === focusId) set.add(e.source);
    });
    return set;
  }, [focusId, graphData.edges]);

  const isDimmed = (id: string) => !!connected && !connected.has(id);

  if (loading) return <NeuralLoader />;

  return (
    <motion.div variants={staggerContainer} initial="hidden" animate="show" className="space-y-6">
      <PageHeader
        title="Knowledge Graph"
        subtitle={`Your personal knowledge map — ${graphData.nodes.length} entities, ${graphData.edges.length} connections`}
      />

      <motion.input
        variants={staggerItem}
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        placeholder="Search entities..."
        className="w-full px-5 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder:text-white/30 focus:outline-none focus:border-primary-500/40 text-sm transition-colors"
      />

      <motion.div variants={staggerItem} className="flex flex-wrap gap-2">
        {Object.entries(nodeColors)
          .filter(([type]) => graphData.nodes.some((n) => n.node_type === type))
          .map(([type, color]) => (
            <div key={type} className="flex items-center gap-1.5 text-xs">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color, boxShadow: `0 0 8px ${color}80` }} />
              <span className="text-white/50 capitalize">{type}</span>
            </div>
          ))}
      </motion.div>

      {graphData.nodes.length === 0 ? (
        <GlassPanel>
          <EmptyState
            icon="⬡"
            title="No Knowledge Graph Yet"
            description="Upload documents and conversations to build your personal knowledge graph with people, projects, events, and more."
          />
        </GlassPanel>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <motion.div variants={staggerItem} className="lg:col-span-2">
            <GlassPanel title="Graph View" icon="⬡" subtitle="Hover a node to isolate its connections">
              <div className="relative h-96 overflow-hidden rounded-xl bg-surface-50/50">
                <svg width="100%" height="100%" viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}>
                  <defs>
                    <radialGradient id="graphGlow">
                      <stop offset="0%" stopColor="#6366f1" stopOpacity={0.18} />
                      <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
                    </radialGradient>
                  </defs>

                  {/* Ambient centre glow */}
                  <circle cx={VIEW_W / 2} cy={VIEW_H / 2} r={230} fill="url(#graphGlow)" />

                  {/* Edges — drawn first so nodes sit on top */}
                  {graphData.edges.slice(0, 120).map((edge, i) => {
                    const s = positions.get(edge.source);
                    const t = positions.get(edge.target);
                    if (!s || !t) return null;
                    const dim = isDimmed(edge.source) || isDimmed(edge.target);
                    return (
                      <motion.line
                        key={edge.id || i}
                        x1={s.x} y1={s.y} x2={t.x} y2={t.y}
                        stroke={dim ? 'rgba(99,102,241,0.06)' : 'rgba(129,140,248,0.45)'}
                        strokeWidth={dim ? 0.6 : 1.2}
                        initial={{ pathLength: 0, opacity: 0 }}
                        animate={{ pathLength: 1, opacity: 1 }}
                        transition={{ duration: 0.8, delay: 0.3 + Math.min(i * 0.02, 0.6) }}
                      />
                    );
                  })}

                  {/* Nodes */}
                  {graphData.nodes.map((node, i) => {
                    const pos = positions.get(node.id);
                    if (!pos) return null;
                    const color = nodeColors[node.node_type] || '#6366f1';
                    const dim = isDimmed(node.id);
                    const isFocus = focusId === node.id;
                    return (
                      <motion.g
                        key={node.id}
                        style={{ cursor: 'pointer' }}
                        onClick={() => setSelectedNode(node)}
                        onMouseEnter={() => setHovered(node.id)}
                        onMouseLeave={() => setHovered(null)}
                        initial={{ opacity: 0, scale: 0 }}
                        animate={{ opacity: dim ? 0.25 : 1, scale: 1 }}
                        transition={{ delay: Math.min(i * 0.04, 0.8), type: 'spring', stiffness: 220, damping: 18 }}
                      >
                        {/* Pulsing halo on the focused node */}
                        {isFocus && (
                          <motion.circle
                            cx={pos.x} cy={pos.y}
                            fill="none" stroke={color} strokeWidth={1}
                            initial={{ r: pos.r, opacity: 0.8 }}
                            animate={{ r: pos.r + 14, opacity: 0 }}
                            transition={{ duration: 1.4, repeat: Infinity, ease: 'easeOut' }}
                          />
                        )}
                        <circle
                          cx={pos.x} cy={pos.y} r={pos.r}
                          fill={color}
                          opacity={0.85}
                          style={{ filter: isFocus ? `drop-shadow(0 0 10px ${color})` : undefined }}
                        />
                        <circle cx={pos.x} cy={pos.y} r={pos.r + 5} fill="none" stroke={color} strokeWidth={1} opacity={0.35} />
                        <text
                          x={pos.x} y={pos.y + pos.r + 14}
                          textAnchor="middle"
                          fill={isFocus ? 'rgba(255,255,255,0.95)' : 'rgba(255,255,255,0.55)'}
                          fontSize={11}
                        >
                          {node.label.length > 14 ? `${node.label.slice(0, 13)}…` : node.label}
                        </text>
                      </motion.g>
                    );
                  })}
                </svg>
              </div>
            </GlassPanel>
          </motion.div>

          <motion.div variants={staggerItem}>
            <GlassPanel title="Entities" icon="📋" subtitle={`${filteredNodes.length} of ${graphData.nodes.length} shown`}>
              <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
                {filteredNodes.map((node, i) => (
                  <motion.div
                    key={node.id}
                    className={`p-3 rounded-xl border cursor-pointer transition-all ${
                      selectedNode?.id === node.id
                        ? 'bg-primary-600/20 border-primary-500/30'
                        : 'bg-white/5 border-white/5 hover:border-white/20'
                    }`}
                    onClick={() => setSelectedNode(node)}
                    onMouseEnter={() => setHovered(node.id)}
                    onMouseLeave={() => setHovered(null)}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    whileHover={{ x: 3 }}
                    transition={{ delay: Math.min(i * 0.03, 0.5) }}
                  >
                    <div className="flex items-center gap-2">
                      <div
                        className="w-3 h-3 rounded-full flex-shrink-0"
                        style={{ backgroundColor: nodeColors[node.node_type] || '#6366f1' }}
                      />
                      <span className="text-sm text-white/70 truncate">{node.label}</span>
                      <span className="ml-auto text-[10px] text-white/30">
                        {Math.round((node.importance || 0.5) * 100)}%
                      </span>
                    </div>
                    <span className="text-[10px] text-white/30 capitalize ml-5">{node.node_type}</span>
                  </motion.div>
                ))}
              </div>
            </GlassPanel>
          </motion.div>
        </div>
      )}

      <AnimatePresence>
        {selectedNode && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            <GlassPanel title={selectedNode.label} icon="🔍" subtitle={`Type: ${selectedNode.node_type}`}>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-xs text-white/40 block mb-1">Node Type</span>
                  <span className="text-sm text-white/70 capitalize">{selectedNode.node_type}</span>
                </div>
                <div>
                  <span className="text-xs text-white/40 block mb-1">Importance</span>
                  <span className="text-sm text-white/70">{((selectedNode.importance || 0.5) * 100).toFixed(0)}%</span>
                </div>
                <div className="col-span-2">
                  <span className="text-xs text-white/40 block mb-1">Connections</span>
                  <span className="text-sm text-white/70">
                    {graphData.edges.filter((e) => e.source === selectedNode.id || e.target === selectedNode.id).length}
                  </span>
                </div>
                {selectedNode.properties && Object.keys(selectedNode.properties).length > 0 && (
                  <div className="col-span-2">
                    <span className="text-xs text-white/40 block mb-1">Properties</span>
                    <pre className="text-[10px] text-white/40 bg-white/5 p-3 rounded-lg overflow-x-auto">
                      {JSON.stringify(selectedNode.properties, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </GlassPanel>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
