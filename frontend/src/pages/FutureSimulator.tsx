import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { GlassPanel, NeuralLoader } from '../components/ui';
import { simulationAPI, predictionAPI } from '../api';

const simTypes = [
  { type: 'career', label: 'Career Path', icon: '💼', desc: 'Simulate career trajectory' },
  { type: 'life', label: 'Life Decision', icon: '🌟', desc: 'Life-changing decisions' },
  { type: 'skill', label: 'Skill Growth', icon: '📈', desc: 'Learning & skill development' },
  { type: 'startup', label: 'Startup', icon: '🚀', desc: 'Entrepreneurial outcomes' },
];

const riskColors: Record<string, string> = {
  low: 'text-emerald-400 bg-emerald-500/10',
  moderate: 'text-amber-400 bg-amber-500/10',
  high: 'text-red-400 bg-red-500/10',
  critical: 'text-red-500 bg-red-500/20',
};

export default function FutureSimulator() {
  const [mode, setMode] = useState<'simulate' | 'predict'>('predict');
  const [scenario, setScenario] = useState('');
  const [simType, setSimType] = useState('career');
  const [title, setTitle] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const runPrediction = async () => {
    if (!scenario.trim()) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await predictionAPI.predict(scenario);
      setResult({ type: 'prediction', data: res.data });
    } catch {
      setResult({ type: 'error', data: { message: 'Prediction failed. Ensure backend is running.' } });
    }
    setLoading(false);
  };

  const runSimulation = async () => {
    if (!title.trim()) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await simulationAPI.simulate({ simulation_type: simType, title, params: { scenario } });
      setResult({ type: 'simulation', data: res.data });
    } catch {
      setResult({ type: 'error', data: { message: 'Simulation failed. Ensure backend is running.' } });
    }
    setLoading(false);
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <div>
        <h1 className="text-3xl font-display font-bold gradient-text mb-1">Future Simulator</h1>
        <p className="text-white/40 text-sm">Predict decisions & simulate future outcomes</p>
      </div>

      {/* Mode Toggle */}
      <div className="flex gap-2">
        {(['predict', 'simulate'] as const).map((m) => (
          <motion.button
            key={m}
            // Each mode gets a clean scenario box; carrying text across the two
            // made the simulator look like it had pre-filled the other tab.
            onClick={() => { setMode(m); setResult(null); setScenario(''); setTitle(''); }}
            className={`relative px-5 py-2.5 rounded-xl text-sm font-medium transition-colors ${
              mode === m ? 'text-white' : 'bg-white/5 text-white/50 hover:text-white/80'
            }`}
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.95 }}
          >
            {mode === m && (
              <motion.span
                layoutId="simulator-mode-pill"
                className="absolute inset-0 rounded-xl gradient-primary"
                transition={{ type: 'spring', stiffness: 380, damping: 30 }}
              />
            )}
            <span className="relative z-10">
              {m === 'predict' ? '🔮 Decision Prediction' : '🌀 Future Simulation'}
            </span>
          </motion.button>
        ))}
      </div>

      {/* Input Area */}
      <GlassPanel>
        {mode === 'predict' ? (
          <div className="space-y-4">
            <label className="text-sm text-white/60 block">Describe the scenario for prediction:</label>
            <textarea
              value={scenario}
              onChange={(e) => setScenario(e.target.value)}
              placeholder="e.g., Would this person accept a startup job offer with 50% pay cut but equity?"
              className="w-full h-32 px-5 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder:text-white/30 focus:outline-none focus:border-primary-500/40 text-sm resize-none"
            />
            <motion.button
              onClick={runPrediction}
              disabled={loading || !scenario.trim()}
              className="px-6 py-3 rounded-xl gradient-primary text-white font-medium text-sm disabled:opacity-40"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              {loading ? 'Analyzing...' : '🔮 Predict Decision'}
            </motion.button>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {simTypes.map((st) => (
                <motion.button
                  key={st.type}
                  onClick={() => setSimType(st.type)}
                  className={`p-3 rounded-xl border transition-all text-left ${
                    simType === st.type
                      ? 'bg-primary-600/20 border-primary-500/30 text-white'
                      : 'bg-white/5 border-white/5 text-white/50'
                  }`}
                  whileHover={{ scale: 1.02 }}
                >
                  <span className="text-xl block mb-1">{st.icon}</span>
                  <span className="text-xs font-medium block">{st.label}</span>
                  <span className="text-[10px] opacity-50">{st.desc}</span>
                </motion.button>
              ))}
            </div>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Simulation title..."
              className="w-full px-5 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder:text-white/30 focus:outline-none focus:border-primary-500/40 text-sm"
            />
            <textarea
              value={scenario}
              onChange={(e) => setScenario(e.target.value)}
              placeholder="Describe the scenario to simulate..."
              className="w-full h-24 px-5 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder:text-white/30 focus:outline-none focus:border-primary-500/40 text-sm resize-none"
            />
            <motion.button
              onClick={runSimulation}
              disabled={loading || !title.trim()}
              className="px-6 py-3 rounded-xl gradient-primary text-white font-medium text-sm disabled:opacity-40"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              {loading ? 'Simulating...' : '🌀 Run Simulation'}
            </motion.button>
          </div>
        )}
      </GlassPanel>

      {loading && <NeuralLoader />}

      {/* Results */}
      <AnimatePresence>
        {result && result.type === 'prediction' && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="space-y-4">
            <GlassPanel title="Prediction Result" icon="🔮">
              <div className="space-y-4">
                <div className="flex items-center gap-4">
                  <div className="text-center">
                    <span className="text-4xl font-display font-bold gradient-text">{(result.data.confidence_pct || 0).toFixed(0)}%</span>
                    <p className="text-xs text-white/40">Confidence</p>
                  </div>
                </div>
                <p className="text-sm text-white/70 leading-relaxed">{result.data.prediction_text}</p>
                {result.data.reasoning && (
                  <div className="p-4 rounded-xl bg-white/5 border border-white/5">
                    <span className="text-xs text-white/40 block mb-2">Reasoning</span>
                    <p className="text-xs text-white/60 leading-relaxed">{result.data.reasoning}</p>
                  </div>
                )}
              </div>
            </GlassPanel>
          </motion.div>
        )}

        {result && result.type === 'simulation' && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="space-y-4">
            <GlassPanel title="Simulation Results" icon="🌀">
              <p className="text-sm text-white/60 mb-4">{result.data.summary}</p>
              <div className="space-y-3">
                {(result.data.outcomes || []).map((outcome: any, i: number) => (
                  <motion.div
                    key={i}
                    className="p-4 rounded-xl bg-white/5 border border-white/5"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.1 }}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <span className="text-sm font-medium text-white/80">{outcome.outcome}</span>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full ${riskColors[outcome.risk_level] || riskColors.moderate}`}>
                        {outcome.risk_level}
                      </span>
                    </div>
                    <p className="text-xs text-white/50 mb-2">{outcome.details}</p>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-2 rounded-full bg-white/5 overflow-hidden">
                        <motion.div
                          className="h-full rounded-full gradient-primary"
                          initial={{ width: '0%' }}
                          animate={{ width: `${(outcome.probability || 0) * 100}%` }}
                          transition={{ duration: 1 }}
                        />
                      </div>
                      <span className="text-xs text-white/40">{((outcome.probability || 0) * 100).toFixed(0)}%</span>
                    </div>
                  </motion.div>
                ))}
              </div>
            </GlassPanel>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
