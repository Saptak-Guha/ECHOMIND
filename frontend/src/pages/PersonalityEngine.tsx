import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { GlassPanel, NeuralLoader, staggerContainer, staggerItem } from '../components/ui';
import { personalityAPI } from '../api';
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from 'recharts';

export default function PersonalityEngine() {
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    personalityAPI.getProfile()
      .then((res) => setProfile(res.data))
      .catch(() => setProfile(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <NeuralLoader />;

  const p = profile || {};
  const bigFiveData = [
    { trait: 'Openness', value: (p.openness || 0.5) * 100, fullMark: 100 },
    { trait: 'Conscientiousness', value: (p.conscientiousness || 0.5) * 100, fullMark: 100 },
    { trait: 'Extraversion', value: (p.extraversion || 0.5) * 100, fullMark: 100 },
    { trait: 'Agreeableness', value: (p.agreeableness || 0.5) * 100, fullMark: 100 },
    { trait: 'Neuroticism', value: (p.neuroticism || 0.5) * 100, fullMark: 100 },
  ];

  const toneData = Object.entries(p.tone_profile || {}).map(([key, val]) => ({
    tone: key.charAt(0).toUpperCase() + key.slice(1),
    value: ((val as number) || 0) * 100,
  }));

  const COLORS = ['#6366f1', '#818cf8', '#a5b4fc', '#c7d2fe', '#e0e7ff', '#0ea5e9', '#38bdf8'];

  return (
    <motion.div variants={staggerContainer} initial="hidden" animate="show" className="space-y-6">
      <div>
        <h1 className="text-3xl font-display font-bold gradient-text mb-1">Personality Engine</h1>
        <p className="text-white/40 text-sm">
          Your continuously evolving personality profile — {p.data_points_count || 0} data points analyzed
        </p>
      </div>

      <motion.div variants={staggerItem} className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Big Five Radar */}
        <GlassPanel title="Big Five Personality" icon="◎" subtitle="Core personality dimensions">
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={bigFiveData}>
                <PolarGrid stroke="rgba(255,255,255,0.1)" />
                <PolarAngleAxis dataKey="trait" tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }} />
                <Radar dataKey="value" stroke="#6366f1" fill="#6366f1" fillOpacity={0.2} strokeWidth={2} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </GlassPanel>

        {/* Tone Profile */}
        <GlassPanel title="Tone Profile" icon="🎭" subtitle="Communication tone distribution">
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={toneData} layout="vertical">
                <XAxis type="number" domain={[0, 100]} stroke="rgba(255,255,255,0.2)" fontSize={11} />
                <YAxis dataKey="tone" type="category" stroke="rgba(255,255,255,0.2)" fontSize={11} width={90} />
                <Tooltip contentStyle={{ background: 'rgba(26,21,40,0.9)', border: '1px solid rgba(99,102,241,0.2)', borderRadius: '12px', color: '#fff' }} />
                <Bar dataKey="value" radius={[0, 6, 6, 0]}>
                  {toneData.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} opacity={0.8} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </GlassPanel>
      </motion.div>

      {/* Writing Style Metrics */}
      <GlassPanel title="Writing Style" icon="✍️" subtitle="Your unique communication fingerprint">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: 'Formality', value: p.formality_score, desc: p.formality_score > 0.6 ? 'Formal' : p.formality_score < 0.4 ? 'Informal' : 'Balanced' },
            { label: 'Complexity', value: p.complexity_score, desc: 'Text sophistication' },
            { label: 'Vocab Richness', value: p.vocabulary_richness, desc: 'Lexical diversity' },
            { label: 'Confidence', value: p.confidence_score, desc: 'Profile reliability' },
          ].map((metric) => (
            <div key={metric.label} className="p-4 rounded-xl bg-white/5 border border-white/5">
              <span className="text-xs text-white/40 block mb-2">{metric.label}</span>
              <span className="text-2xl font-display font-bold text-white">{((metric.value || 0) * 100).toFixed(0)}%</span>
              <span className="text-[10px] text-white/30 block mt-1">{metric.desc}</span>
              <div className="mt-2 h-1 rounded-full bg-white/5 overflow-hidden">
                <motion.div
                  className="h-full rounded-full gradient-primary"
                  initial={{ width: '0%' }}
                  animate={{ width: `${(metric.value || 0) * 100}%` }}
                  transition={{ duration: 1, delay: 0.5 }}
                />
              </div>
            </div>
          ))}
        </div>
      </GlassPanel>

      {/* Beliefs, Interests, Values */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { title: 'Beliefs', data: p.beliefs || [], icon: '💭', color: 'primary-400' },
          { title: 'Interests', data: p.interests || [], icon: '✨', color: 'accent-400' },
          { title: 'Values', data: p.values || [], icon: '💎', color: 'neural-400' },
        ].map((section) => (
          <GlassPanel key={section.title} title={section.title} icon={section.icon}>
            {section.data.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {section.data.map((item: string, i: number) => (
                  <motion.span
                    key={i}
                    className="px-3 py-1 rounded-full bg-white/5 text-xs text-white/60 border border-white/5"
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: i * 0.05 }}
                  >
                    {item}
                  </motion.span>
                ))}
              </div>
            ) : (
              <p className="text-xs text-white/30">Upload more data to discover {section.title.toLowerCase()}</p>
            )}
          </GlassPanel>
        ))}
      </div>
    </motion.div>
  );
}
