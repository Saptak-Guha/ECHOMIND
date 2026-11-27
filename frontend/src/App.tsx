import { useEffect, useState } from 'react';
import { BrowserRouter, Navigate, Routes, Route, useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { useStore } from './store';
import { authAPI } from './api';
import { NeuralBackground, NeuralLoader } from './components/ui';
import Sidebar from './components/Sidebar';
import AuthGate from './pages/AuthGate';
import Dashboard from './pages/Dashboard';
import TwinChat from './pages/TwinChat';
import MemoryVault from './pages/MemoryVault';
import PersonalityEngine from './pages/PersonalityEngine';
import BehaviorAnalytics from './pages/BehaviorAnalytics';
import FutureSimulator from './pages/FutureSimulator';
import KnowledgeGraph from './pages/KnowledgeGraph';
import EmotionalInsights from './pages/EmotionalInsights';
import LifeTimeline from './pages/LifeTimeline';
import Settings from './pages/Settings';

/**
 * Routes wrapped in AnimatePresence so leaving a page fades out before the next
 * one rises in, instead of the hard swap the app had before.
 */
function AnimatedRoutes() {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={location.pathname}
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -8 }}
        transition={{ duration: 0.28, ease: 'easeOut' }}
      >
        <Routes location={location}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/twin" element={<TwinChat />} />
          <Route path="/memory" element={<MemoryVault />} />
          <Route path="/personality" element={<PersonalityEngine />} />
          <Route path="/behavior" element={<BehaviorAnalytics />} />
          <Route path="/simulator" element={<FutureSimulator />} />
          <Route path="/graph" element={<KnowledgeGraph />} />
          <Route path="/emotions" element={<EmotionalInsights />} />
          <Route path="/timeline" element={<LifeTimeline />} />
          <Route path="/settings" element={<Settings />} />
          {/* Unknown paths rendered a blank screen; send them home instead. */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </motion.div>
    </AnimatePresence>
  );
}

export default function App() {
  const { sidebarOpen, token, user, setUser, signOut } = useStore();
  // A stored token can be expired or revoked; confirm it before rendering the
  // app, otherwise every panel would mount and immediately 401.
  const [checking, setChecking] = useState(!!token);

  useEffect(() => {
    if (!token) {
      setChecking(false);
      return;
    }
    let cancelled = false;
    authAPI
      .me()
      .then((res) => !cancelled && setUser(res.data))
      .catch(() => !cancelled && signOut())
      .finally(() => !cancelled && setChecking(false));
    return () => {
      cancelled = true;
    };
    // Re-validate whenever the identity changes (sign-in, sign-out).
  }, [token, setUser, signOut]);

  if (checking) {
    return (
      <div className="min-h-screen bg-surface-50 text-white flex items-center justify-center">
        <NeuralLoader />
      </div>
    );
  }

  if (!token || !user) return <AuthGate />;

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-surface-50 text-white">
        <NeuralBackground />
        <Sidebar />
        <main
          className="relative z-10 transition-all duration-300 p-6"
          style={{ marginLeft: sidebarOpen ? 280 : 72 }}
        >
          <AnimatedRoutes />
        </main>
      </div>
    </BrowserRouter>
  );
}
