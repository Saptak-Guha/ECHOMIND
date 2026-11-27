import { useEffect, useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { GlassPanel, PageHeader, EmptyState, Skeleton, staggerContainer } from '../components/ui';
import { analyticsAPI } from '../api';

interface TimelineEvent {
  date: string;
  time: string;
  title: string;
  desc: string;
  category: string;
  icon: string;
}

const catColors: Record<string, string> = {
  system: 'border-primary-500/30 bg-primary-500/10',
  learning: 'border-accent-500/30 bg-accent-500/10',
  prediction: 'border-amber-500/30 bg-amber-500/10',
  knowledge: 'border-emerald-500/30 bg-emerald-500/10',
  personal: 'border-rose-500/30 bg-rose-500/10',
};

export default function LifeTimeline() {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [active, setActive] = useState<string | null>(null);

  useEffect(() => {
    analyticsAPI
      .getTimeline()
      .then((res) => setEvents(Array.isArray(res.data) ? res.data : []))
      .catch(() => setEvents([]))
      .finally(() => setLoading(false));
  }, []);

  // Only offer filters for categories that actually occur in the data.
  const categories = useMemo(
    () => Object.keys(catColors).filter((c) => events.some((e) => e.category === c)),
    [events],
  );

  const visible = active ? events.filter((e) => e.category === active) : events;

  return (
    <motion.div variants={staggerContainer} initial="hidden" animate="show" className="space-y-6">
      <PageHeader
        title="Life Timeline"
        subtitle={
          loading
            ? 'Your digital legacy — key events, milestones, and growth'
            : `${events.length} recorded events in your twin's history`
        }
      />

      {categories.length > 0 && (
        <motion.div className="flex flex-wrap gap-2" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <motion.button
            onClick={() => setActive(null)}
            whileHover={{ scale: 1.06 }}
            whileTap={{ scale: 0.95 }}
            className={`text-[10px] px-3 py-1 rounded-full border transition-colors ${
              active === null ? 'border-white/40 bg-white/10 text-white' : 'border-white/10 text-white/50'
            }`}
          >
            all ({events.length})
          </motion.button>
          {categories.map((cat) => (
            <motion.button
              key={cat}
              onClick={() => setActive(active === cat ? null : cat)}
              whileHover={{ scale: 1.06 }}
              whileTap={{ scale: 0.95 }}
              className={`text-[10px] px-3 py-1 rounded-full border capitalize transition-opacity ${catColors[cat]} ${
                active && active !== cat ? 'opacity-40' : 'opacity-100'
              }`}
            >
              {cat} ({events.filter((e) => e.category === cat).length})
            </motion.button>
          ))}
        </motion.div>
      )}

      {loading ? (
        <div className="space-y-4">
          {[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-24" />)}
        </div>
      ) : events.length === 0 ? (
        <GlassPanel>
          <EmptyState
            icon="⧗"
            title="No Timeline Yet"
            description="Upload data, chat with your twin, or run a prediction. Every action your twin takes is recorded here in order."
          />
        </GlassPanel>
      ) : (
        <div className="relative">
          {/* Vertical spine */}
          <motion.div
            className="absolute left-[70px] top-0 w-px bg-gradient-to-b from-primary-500/50 via-accent-500/30 to-transparent"
            initial={{ height: 0 }}
            animate={{ height: '100%' }}
            transition={{ duration: 1.2, ease: 'easeOut' }}
          />

          <div className="space-y-6">
            <AnimatePresence mode="popLayout">
              {visible.map((event, i) => (
                <motion.div
                  key={`${event.date}-${event.time}-${event.title}-${i}`}
                  layout
                  className="relative pl-28"
                  initial={{ opacity: 0, x: -30 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 30 }}
                  transition={{ delay: Math.min(i * 0.05, 0.6), duration: 0.4 }}
                >
                  <motion.div
                    className="absolute left-[60px] top-4 w-5 h-5 rounded-full border-2 border-primary-500 bg-surface-50 flex items-center justify-center z-10"
                    whileHover={{ scale: 1.4 }}
                  >
                    <motion.div
                      className="w-2 h-2 rounded-full bg-primary-400"
                      animate={{ opacity: [0.5, 1, 0.5] }}
                      transition={{ duration: 2.5, repeat: Infinity, delay: i * 0.15 }}
                    />
                  </motion.div>

                  <div className="absolute left-0 top-3 text-[10px] text-white/30 w-12 text-right leading-tight tabular-nums">
                    {event.date.slice(5)}
                    <span className="block text-white/20">{event.time}</span>
                  </div>

                  <motion.div
                    whileHover={{ x: 6 }}
                    transition={{ type: 'spring', stiffness: 300, damping: 22 }}
                    className={`glass-card p-5 rounded-2xl border ${catColors[event.category] || 'border-white/10'}`}
                  >
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-xl">{event.icon}</span>
                      <div>
                        <h3 className="font-medium text-white/90 text-sm">{event.title}</h3>
                        <span className={`text-[10px] px-2 py-0.5 rounded-full border capitalize ${catColors[event.category]}`}>
                          {event.category}
                        </span>
                      </div>
                    </div>
                    <p className="text-xs text-white/50 leading-relaxed">{event.desc}</p>
                  </motion.div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>

          <motion.div
            className="relative pl-28 mt-6"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8 }}
          >
            <div className="absolute left-[60px] top-3 w-5 h-5 rounded-full border-2 border-dashed border-white/20 bg-surface-50" />
            <p className="text-xs text-white/25 pt-3">The story continues as your twin learns…</p>
          </motion.div>
        </div>
      )}
    </motion.div>
  );
}
