import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { EmptyState, NeuralLoader, PageHeader, staggerContainer, staggerItem } from '../components/ui';
import { memoryAPI } from '../api';

const typeColors: Record<string, string> = {
  semantic: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
  episodic: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
  behavioral: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
  preference: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
  emotional: 'bg-rose-500/20 text-rose-300 border-rose-500/30',
};

const typeIcons: Record<string, string> = {
  semantic: '📚', episodic: '🎭', behavioral: '⚡', preference: '💜', emotional: '🌊',
};

export default function MemoryVault() {
  const [memories, setMemories] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeType, setActiveType] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      memoryAPI.getTimeline(100).catch(() => ({ data: [] })),
      memoryAPI.getStats().catch(() => ({ data: { total_memories: 0, by_type: {}, avg_importance: 0 } })),
    ]).then(([timelineRes, statsRes]) => {
      setMemories(timelineRes.data);
      setStats(statsRes.data);
      setLoading(false);
    });
  }, []);

  const filteredMemories = memories.filter((m: any) => {
    if (activeType && m.type !== activeType) return false;
    if (searchQuery && !m.summary?.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  if (loading) return <NeuralLoader />;

  return (
    <motion.div variants={staggerContainer} initial="hidden" animate="show" className="space-y-6">
      <PageHeader
        title="Memory Vault"
        subtitle={`Your long-term memory system — ${stats?.total_memories || 0} memories stored`}
      />

      {/* Stats */}
      <motion.div variants={staggerItem} className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {Object.entries(typeColors).map(([type, colorClass]) => (
          <motion.button
            key={type}
            onClick={() => setActiveType(activeType === type ? null : type)}
            className={`p-3 rounded-xl border transition-all ${activeType === type ? colorClass : 'bg-white/5 border-white/5 text-white/50'}`}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <span className="text-lg block mb-1">{typeIcons[type]}</span>
            <span className="text-xs font-medium capitalize block">{type}</span>
            <span className="text-xs opacity-60">{stats?.by_type?.[type] || 0}</span>
          </motion.button>
        ))}
      </motion.div>

      {/* Search */}
      <motion.input
        variants={staggerItem}
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        placeholder="Search memories..."
        className="w-full px-5 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder:text-white/30 focus:outline-none focus:border-primary-500/40 transition-colors text-sm"
      />

      {/* Memory Cards */}
      {filteredMemories.length === 0 ? (
        <EmptyState icon="◉" title="No memories yet" description="Upload documents or chat with your twin to build memories." />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredMemories.map((memory: any, i: number) => (
            <motion.div
              key={memory.id || i}
              className="glass-card p-5 rounded-2xl"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
            >
              <div className="flex items-start justify-between mb-3">
                <span className={`text-[10px] px-2 py-0.5 rounded-full border capitalize ${typeColors[memory.type] || 'bg-white/10'}`}>
                  {typeIcons[memory.type] || '📝'} {memory.type}
                </span>
                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-1">
                    <div className="w-1.5 h-1.5 rounded-full bg-primary-400" />
                    <span className="text-[10px] text-white/30">{(memory.importance * 100).toFixed(0)}% important</span>
                  </div>
                </div>
              </div>
              <p className="text-sm text-white/70 leading-relaxed line-clamp-3">{memory.summary}</p>
              {memory.tags && memory.tags.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-3">
                  {memory.tags.map((tag: string) => (
                    <span key={tag} className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 text-white/30">#{tag}</span>
                  ))}
                </div>
              )}
              <div className="flex justify-between items-center mt-3 pt-3 border-t border-white/5">
                <span className="text-[10px] text-white/20">{memory.created_at ? new Date(memory.created_at).toLocaleDateString() : ''}</span>
                <div className="h-1 w-16 rounded-full bg-white/5 overflow-hidden">
                  <div
                    className="h-full rounded-full gradient-primary"
                    style={{ width: `${memory.emotional_valence ? (memory.emotional_valence + 1) * 50 : 50}%` }}
                  />
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </motion.div>
  );
}
