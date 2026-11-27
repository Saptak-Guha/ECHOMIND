import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { GlassPanel, NeuralLoader, PageHeader, staggerContainer, staggerItem } from '../components/ui';
import { behaviorAPI } from '../api';
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer } from 'recharts';

export default function BehaviorAnalytics() {
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    behaviorAPI.getProfile()
      .then((res) => setProfile(res.data))
      .catch(() => setProfile(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <NeuralLoader />;
  const b = profile || {};

  const traitData = [
    { trait: 'Risk Tolerance', value: (b.risk_tolerance || 0.5) * 100 },
    { trait: 'Decisiveness', value: (b.decisiveness || 0.5) * 100 },
    { trait: 'Adaptability', value: (b.adaptability || 0.5) * 100 },
    { trait: 'Persistence', value: (b.persistence || 0.5) * 100 },
    { trait: 'Creativity', value: (b.creativity || 0.5) * 100 },
  ];

  return (
    <motion.div variants={staggerContainer} initial="hidden" animate="show" className="space-y-6">
      <PageHeader title="Behavior Analytics" subtitle="Decision patterns, habits, and behavioral insights" />

      <motion.div variants={staggerItem} className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <GlassPanel title="Behavioral Traits" icon="◇" subtitle="Core behavioral dimensions">
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={traitData}>
                <PolarGrid stroke="rgba(255,255,255,0.1)" />
                <PolarAngleAxis dataKey="trait" tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }} />
                <Radar dataKey="value" stroke="#0ea5e9" fill="#0ea5e9" fillOpacity={0.2} strokeWidth={2} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </GlassPanel>

        <GlassPanel title="Decision Profile" icon="⚡" subtitle="How you make decisions">
          <div className="space-y-6 py-4">
            {[
              { label: 'Decision Style', value: b.decision_style || 'Analytical', icon: '🧠' },
              { label: 'Decision Speed', value: b.decision_speed || 'Moderate', icon: '⚡' },
              { label: 'Problem Solving', value: b.problem_solving_style || 'Systematic', icon: '🔧' },
            ].map((item) => (
              <div key={item.label} className="flex items-center justify-between p-3 rounded-xl bg-white/5">
                <div className="flex items-center gap-3">
                  <span className="text-xl">{item.icon}</span>
                  <span className="text-sm text-white/50">{item.label}</span>
                </div>
                <span className="text-sm font-medium text-white/80 capitalize">{item.value}</span>
              </div>
            ))}

            <div className="p-4 rounded-xl bg-white/5 border border-white/5">
              <span className="text-xs text-white/40 block mb-3">Risk Tolerance</span>
              <div className="flex items-center gap-3">
                <span className="text-xs text-white/30">Risk-Averse</span>
                <div className="flex-1 h-3 rounded-full bg-white/5 overflow-hidden relative">
                  <motion.div
                    className="h-full rounded-full bg-gradient-to-r from-emerald-500 via-amber-500 to-red-500"
                    initial={{ width: '0%' }}
                    animate={{ width: `${(b.risk_tolerance || 0.5) * 100}%` }}
                    transition={{ duration: 1.5 }}
                  />
                </div>
                <span className="text-xs text-white/30">Risk-Seeking</span>
              </div>
            </div>
          </div>
        </GlassPanel>
      </motion.div>

      <GlassPanel title="Detected Habits" icon="🔄" subtitle="Recurring behavioral patterns">
        {(b.habits || []).length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {b.habits.map((habit: any, i: number) => (
              <motion.div
                key={i}
                className="p-4 rounded-xl bg-white/5 border border-white/5"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
              >
                <p className="text-sm text-white/70">{habit.habit || habit}</p>
                {habit.frequency && <span className="text-[10px] text-white/30 mt-1 block capitalize">{habit.frequency}</span>}
              </motion.div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-white/30 py-8 text-center">Upload more data to detect habits and behavioral patterns.</p>
        )}
      </GlassPanel>
    </motion.div>
  );
}
