import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer,
  AreaChart, Area, XAxis, YAxis, Tooltip,
} from 'recharts';
import {
  GlassPanel, PageHeader, EmptyState, Skeleton,
  staggerContainer, staggerItem,
} from '../components/ui';
import { analyticsAPI } from '../api';

interface EmotionPoint { emotion: string; value: number }
interface MoodPoint { date: string; valence: number; intensity: number }

interface EmotionsResponse {
  emotion_profile: EmotionPoint[];
  mood_timeline: MoodPoint[];
  current_mood: string;
  stress_level: string;
  energy_level: string;
  trend: string;
  documents_analyzed: number;
  data_points: number;
}

const MOOD_STYLES: Record<string, { icon: string; color: string }> = {
  positive: { icon: '😊', color: 'from-emerald-500 to-emerald-400' },
  balanced: { icon: '😌', color: 'from-blue-500 to-blue-400' },
  strained: { icon: '😰', color: 'from-amber-500 to-amber-400' },
  unknown: { icon: '🌫️', color: 'from-white/40 to-white/20' },
};

const LEVEL_STYLES: Record<string, string> = {
  high: 'from-amber-500 to-amber-400',
  moderate: 'from-blue-500 to-blue-400',
  low: 'from-emerald-500 to-emerald-400',
};

function titleCase(value: string) {
  return value ? value.charAt(0).toUpperCase() + value.slice(1) : '—';
}

/**
 * Derive plain-language patterns from the real emotion scores. These replace
 * the previously hardcoded "insights" — each one is only shown when the data
 * actually supports it.
 */
function derivePatterns(data: EmotionsResponse): { icon: string; text: string }[] {
  const scores = Object.fromEntries(
    data.emotion_profile.map((e) => [e.emotion.toLowerCase(), e.value]),
  );
  const ranked = [...data.emotion_profile].sort((a, b) => b.value - a.value);
  const patterns: { icon: string; text: string }[] = [];

  if (ranked[0]?.value > 0) {
    patterns.push({
      icon: '🎯',
      text: `${ranked[0].emotion} is your strongest signal, averaging ${ranked[0].value.toFixed(1)}% across ${data.documents_analyzed} documents.`,
    });
  }
  if ((scores.stress ?? 0) > (scores.contentment ?? 0) && (scores.stress ?? 0) > 0) {
    patterns.push({ icon: '⚠️', text: 'Stress currently outweighs contentment in your writing.' });
  }
  if ((scores.motivation ?? 0) > 0 && (scores.confidence ?? 0) > 0) {
    patterns.push({ icon: '🌟', text: 'Motivation and confidence appear together — a productive pairing.' });
  }
  if ((scores.anxiety ?? 0) > 0 && (scores.excitement ?? 0) > 0) {
    patterns.push({ icon: '💡', text: 'Anxiety and excitement co-occur, often a sign of meaningful stakes.' });
  }
  if (data.mood_timeline.length >= 2) {
    const first = data.mood_timeline[0].valence;
    const last = data.mood_timeline[data.mood_timeline.length - 1].valence;
    patterns.push({
      icon: last >= first ? '📈' : '📉',
      text: `Mood valence has moved from ${first.toFixed(2)} to ${last.toFixed(2)} across ${data.mood_timeline.length} recorded memories.`,
    });
  }
  return patterns;
}

export default function EmotionalInsights() {
  const [data, setData] = useState<EmotionsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    analyticsAPI
      .getEmotions()
      .then((res) => setData(res.data))
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, []);

  const mood = MOOD_STYLES[data?.current_mood ?? 'unknown'] ?? MOOD_STYLES.unknown;

  const cards = [
    { label: 'Current Mood', value: titleCase(data?.current_mood ?? ''), icon: mood.icon, color: mood.color },
    {
      label: 'Stress Level',
      value: titleCase(data?.stress_level ?? ''),
      icon: '🧘',
      color: LEVEL_STYLES[data?.stress_level ?? ''] ?? 'from-white/40 to-white/20',
    },
    {
      label: 'Energy',
      value: titleCase(data?.energy_level ?? ''),
      icon: '⚡',
      color: LEVEL_STYLES[data?.energy_level ?? ''] ?? 'from-white/40 to-white/20',
    },
    { label: 'Trend', value: titleCase(data?.trend ?? ''), icon: '📈', color: 'from-primary-500 to-primary-400' },
  ];

  const hasData = !!data && data.data_points > 0;
  const patterns = data ? derivePatterns(data) : [];

  return (
    <motion.div variants={staggerContainer} initial="hidden" animate="show" className="space-y-6">
      <PageHeader
        title="Emotional Insights"
        subtitle={
          data
            ? `Derived from ${data.documents_analyzed} documents and ${data.mood_timeline.length} memories`
            : 'Track emotional patterns, mood trends, and behavioral changes'
        }
      />

      {loading ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-28" />)}
        </div>
      ) : (
        <motion.div variants={staggerContainer} className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {cards.map((item) => (
            <motion.div
              key={item.label}
              variants={staggerItem}
              className="glass-card p-4 rounded-2xl"
              whileHover={{ scale: 1.03, y: -3 }}
              transition={{ type: 'spring', stiffness: 300, damping: 20 }}
            >
              <motion.span
                className="text-2xl block mb-2"
                animate={{ scale: [1, 1.12, 1] }}
                transition={{ duration: 3.5, repeat: Infinity, ease: 'easeInOut' }}
              >
                {item.icon}
              </motion.span>
              <span className="text-xs text-white/40 block">{item.label}</span>
              <span className={`text-lg font-display font-bold bg-gradient-to-r ${item.color} bg-clip-text text-transparent`}>
                {item.value}
              </span>
            </motion.div>
          ))}
        </motion.div>
      )}

      {!loading && !hasData ? (
        <GlassPanel>
          <EmptyState
            icon="❋"
            title="No Emotional Data Yet"
            description="Upload journal entries, notes, or conversations. The emotional engine scores each one and this page fills in with your real patterns."
          />
        </GlassPanel>
      ) : (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <motion.div variants={staggerItem}>
              <GlassPanel title="Emotional Profile" icon="❋" subtitle="Averaged across your ingested data">
                <div className="h-72">
                  {loading ? <Skeleton className="h-full" /> : (
                    <ResponsiveContainer width="100%" height="100%">
                      <RadarChart data={data?.emotion_profile ?? []}>
                        <PolarGrid stroke="rgba(255,255,255,0.1)" />
                        <PolarAngleAxis dataKey="emotion" tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }} />
                        <Tooltip
                          contentStyle={{ background: 'rgba(26,21,40,0.95)', border: '1px solid rgba(236,72,153,0.25)', borderRadius: '12px', color: '#fff' }}
                          formatter={(v) => [`${Number(v ?? 0).toFixed(1)}%`, 'Intensity']}
                        />
                        <Radar
                          dataKey="value"
                          stroke="#ec4899"
                          fill="#ec4899"
                          fillOpacity={0.25}
                          strokeWidth={2}
                          isAnimationActive
                          animationDuration={1400}
                        />
                      </RadarChart>
                    </ResponsiveContainer>
                  )}
                </div>
              </GlassPanel>
            </motion.div>

            <motion.div variants={staggerItem}>
              <GlassPanel title="Mood Timeline" icon="📊" subtitle="Valence and intensity per memory">
                <div className="h-72">
                  {loading ? <Skeleton className="h-full" /> : (
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={data?.mood_timeline ?? []}>
                        <defs>
                          <linearGradient id="moodGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#ec4899" stopOpacity={0.4} />
                            <stop offset="95%" stopColor="#ec4899" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <XAxis dataKey="date" stroke="rgba(255,255,255,0.2)" fontSize={11} />
                        <YAxis stroke="rgba(255,255,255,0.2)" fontSize={11} domain={[0, 1]} />
                        <Tooltip contentStyle={{ background: 'rgba(26,21,40,0.95)', border: '1px solid rgba(236,72,153,0.25)', borderRadius: '12px', color: '#fff' }} />
                        <Area
                          type="monotone" dataKey="valence" name="Valence"
                          stroke="#ec4899" fill="url(#moodGrad)" strokeWidth={2}
                          isAnimationActive animationDuration={1400}
                        />
                        <Area
                          type="monotone" dataKey="intensity" name="Intensity"
                          stroke="#a855f7" fill="transparent" strokeWidth={1.5} strokeDasharray="4 4"
                          isAnimationActive animationDuration={1600}
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  )}
                </div>
              </GlassPanel>
            </motion.div>
          </div>

          {patterns.length > 0 && (
            <motion.div variants={staggerItem}>
              <GlassPanel title="Emotional Patterns" icon="🔍" subtitle="Computed from your actual scores">
                <motion.div variants={staggerContainer} initial="hidden" animate="show" className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {patterns.map((p, i) => (
                    <motion.div
                      key={i}
                      variants={staggerItem}
                      whileHover={{ x: 4 }}
                      className="p-4 rounded-xl bg-white/5 border border-white/5 flex items-start gap-3"
                    >
                      <span className="text-xl">{p.icon}</span>
                      <p className="text-sm text-white/60">{p.text}</p>
                    </motion.div>
                  ))}
                </motion.div>
              </GlassPanel>
            </motion.div>
          )}
        </>
      )}
    </motion.div>
  );
}
