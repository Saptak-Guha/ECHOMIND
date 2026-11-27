import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { ScoreCard, GlassPanel, NeuralLoader, PageHeader } from '../components/ui';
import { analyticsAPI } from '../api';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  RadialBarChart, RadialBar, PieChart, Pie, Cell,
} from 'recharts';

const defaultMetrics = {
  twin_accuracy: 0, decision_accuracy: 0, personality_match: 0,
  behavior_similarity: 0, communication_similarity: 0,
  total_memories: 0, total_documents: 0, total_predictions: 0,
  total_simulations: 0, knowledge_nodes: 0,
  emotional_trend: [], knowledge_growth: [], memory_growth: [], recent_activity: [],
};

export default function Dashboard() {
  const [metrics, setMetrics] = useState(defaultMetrics);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    analyticsAPI.getDashboard()
      .then((res) => setMetrics(res.data))
      .catch(() => setMetrics(defaultMetrics))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <NeuralLoader />;

  const gaugeData = [
    { name: 'Twin Accuracy', value: metrics.twin_accuracy, fill: '#6366f1' },
  ];

  const statsData = [
    { name: 'Memories', value: metrics.total_memories },
    { name: 'Documents', value: metrics.total_documents },
    { name: 'Predictions', value: metrics.total_predictions },
    { name: 'Simulations', value: metrics.total_simulations },
    { name: 'Knowledge', value: metrics.knowledge_nodes },
  ];

  const COLORS = ['#6366f1', '#0ea5e9', '#22c55e', '#f59e0b', '#ef4444'];

  const container = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.1 } },
  };

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-6">
      <PageHeader title="Command Center" subtitle="Your Digital Twin Intelligence Overview" />

      {/* Score Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <ScoreCard title="Twin Accuracy" value={metrics.twin_accuracy} icon="⟐" color="primary" description="Overall twin fidelity" />
        <ScoreCard title="Decision Accuracy" value={metrics.decision_accuracy} icon="◇" color="accent" description="Prediction accuracy" />
        <ScoreCard title="Personality Match" value={metrics.personality_match} icon="◎" color="neural" description="Profile confidence" />
        <ScoreCard title="Behavior Match" value={metrics.behavior_similarity} icon="◈" color="warning" description="Behavioral alignment" />
      </div>

      {/* Main Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Twin Gauge */}
        <GlassPanel title="Twin Fidelity" icon="⟐" subtitle="Overall accuracy gauge">
          <div className="h-48 flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <RadialBarChart cx="50%" cy="50%" innerRadius="60%" outerRadius="90%" data={gaugeData} startAngle={180} endAngle={0}>
                <RadialBar dataKey="value" cornerRadius={10} fill="#6366f1" background={{ fill: 'rgba(255,255,255,0.05)' }} />
              </RadialBarChart>
            </ResponsiveContainer>
            <div className="absolute text-center">
              <span className="text-3xl font-display font-bold text-white">{metrics.twin_accuracy.toFixed(1)}%</span>
              <p className="text-xs text-white/40">Fidelity</p>
            </div>
          </div>
        </GlassPanel>

        {/* Memory Growth */}
        <GlassPanel title="Data Growth" icon="◉" subtitle="Knowledge & memory expansion" className="lg:col-span-2">
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={metrics.memory_growth.length > 0 ? metrics.memory_growth : [
                { date: 'Week 1', memories: 0, knowledge: 0 },
                { date: 'Week 2', memories: metrics.total_memories * 0.3, knowledge: metrics.knowledge_nodes * 0.2 },
                { date: 'Week 3', memories: metrics.total_memories * 0.6, knowledge: metrics.knowledge_nodes * 0.5 },
                { date: 'Now', memories: metrics.total_memories, knowledge: metrics.knowledge_nodes },
              ]}>
                <defs>
                  <linearGradient id="memGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="knowGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" stroke="rgba(255,255,255,0.2)" fontSize={11} />
                <YAxis stroke="rgba(255,255,255,0.2)" fontSize={11} />
                <Tooltip contentStyle={{ background: 'rgba(26,21,40,0.9)', border: '1px solid rgba(99,102,241,0.2)', borderRadius: '12px', color: '#fff' }} />
                <Area type="monotone" dataKey="memories" stroke="#6366f1" fill="url(#memGrad)" strokeWidth={2} />
                <Area type="monotone" dataKey="knowledge" stroke="#0ea5e9" fill="url(#knowGrad)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </GlassPanel>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Data Distribution */}
        <GlassPanel title="Data Distribution" icon="⬡" subtitle="Breakdown of ingested data">
          <div className="h-48 flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={statsData} cx="50%" cy="50%" innerRadius={40} outerRadius={70} paddingAngle={3} dataKey="value">
                  {statsData.map((_, i) => (
                    <Cell key={i} fill={COLORS[i]} opacity={0.8} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: 'rgba(26,21,40,0.9)', border: '1px solid rgba(99,102,241,0.2)', borderRadius: '12px', color: '#fff' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex flex-wrap gap-2 mt-2">
            {statsData.map((s, i) => (
              <div key={s.name} className="flex items-center gap-1.5 text-xs">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[i] }} />
                <span className="text-white/50">{s.name}: {s.value}</span>
              </div>
            ))}
          </div>
        </GlassPanel>

        {/* Quick Actions */}
        <GlassPanel title="Quick Actions" icon="⚡" subtitle="Get started with your twin">
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: 'Upload Data', desc: 'Feed your twin', path: '/settings', icon: '📄' },
              { label: 'Chat with Twin', desc: 'Start a conversation', path: '/twin', icon: '⟐' },
              { label: 'Predict Decision', desc: 'Test prediction', path: '/simulator', icon: '🔮' },
              { label: 'View Memories', desc: 'Explore memory vault', path: '/memory', icon: '◉' },
            ].map((action) => (
              <motion.a
                key={action.label}
                href={action.path}
                className="p-3 rounded-xl bg-white/5 border border-white/5 hover:border-primary-500/20 transition-all group"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <span className="text-xl block mb-1">{action.icon}</span>
                <span className="text-sm font-medium text-white/80 block">{action.label}</span>
                <span className="text-[10px] text-white/30">{action.desc}</span>
              </motion.a>
            ))}
          </div>
        </GlassPanel>
      </div>

      {/* System Modules */}
      <GlassPanel title="Active Modules" icon="🧠" subtitle="10 AI engines powering your digital twin">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {[
            'Personality Engine', 'Behavior Modeling', 'Digital Twin',
            'Memory System', 'Decision Prediction', 'Future Simulator',
            'Communication Clone', 'Emotional Intelligence', 'Knowledge Graph', 'Digital Legacy',
          ].map((mod, i) => (
            <motion.div
              key={mod}
              className="p-3 rounded-xl bg-white/5 border border-white/5 text-center"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.05 }}
              whileHover={{ borderColor: 'rgba(99, 102, 241, 0.3)' }}
            >
              <div className="w-2 h-2 rounded-full bg-neural-400 mx-auto mb-2 animate-pulse" />
              <span className="text-[11px] text-white/60">{mod}</span>
            </motion.div>
          ))}
        </div>
      </GlassPanel>
    </motion.div>
  );
}
