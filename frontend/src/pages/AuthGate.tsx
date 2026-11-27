import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { authAPI } from '../api';
import { useStore } from '../store';
import { NeuralBackground, staggerContainer, staggerItem } from '../components/ui';

type Mode = 'login' | 'register';

/**
 * Sign-in / sign-up screen. Shown whenever there is no token — every data route
 * is scoped to the authenticated user, so the app cannot render without one.
 */
export default function AuthGate() {
  const signIn = useStore((s) => s.signIn);
  const [mode, setMode] = useState<Mode>('login');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (busy) return;
    setError('');
    setBusy(true);
    try {
      if (mode === 'register') {
        await authAPI.register({ email, username, password, full_name: fullName || undefined });
      }
      const { data } = await authAPI.login(username, password);
      // Store the token first: authAPI.me() needs it on the request.
      localStorage.setItem('echomind_token', data.access_token);
      const me = await authAPI.me();
      signIn(data.access_token, me.data);
    } catch (err: any) {
      localStorage.removeItem('echomind_token');
      const detail = err?.response?.data?.detail;
      setError(
        typeof detail === 'string'
          ? detail
          : mode === 'register'
            ? 'Could not create that account.'
            : 'Incorrect username or password.',
      );
    } finally {
      setBusy(false);
    }
  };

  const switchMode = (next: Mode) => {
    setMode(next);
    setError('');
  };

  return (
    <div className="min-h-screen bg-surface-50 text-white flex items-center justify-center p-6 relative">
      <NeuralBackground />

      <motion.div
        className="relative z-10 w-full max-w-md"
        initial={{ opacity: 0, y: 24, scale: 0.97 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
      >
        <motion.div
          className="text-center mb-8"
          initial={{ opacity: 0, y: -14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1, duration: 0.5 }}
        >
          <motion.div
            className="w-16 h-16 rounded-2xl gradient-primary mx-auto mb-4 flex items-center justify-center text-3xl font-display font-bold"
            animate={{ scale: [1, 1.05, 1] }}
            transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
          >
            E
          </motion.div>
          <h1 className="text-3xl font-display font-bold gradient-text">EchoMind</h1>
          <p className="text-white/40 text-sm mt-1">
            <AnimatePresence mode="wait">
              <motion.span
                key={mode}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                transition={{ duration: 0.22 }}
                className="inline-block"
              >
                {mode === 'login' ? 'Sign in to your digital twin' : 'Create your digital twin'}
              </motion.span>
            </AnimatePresence>
          </p>
        </motion.div>

        <motion.div
          className="glass-card p-6 rounded-2xl"
          variants={staggerContainer}
          initial="hidden"
          animate="show"
          layout
          transition={{ layout: { type: 'spring', stiffness: 260, damping: 28 } }}
        >
          <motion.div variants={staggerItem} className="flex gap-2 mb-6">
            {(['login', 'register'] as const).map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => switchMode(m)}
                className={`relative flex-1 px-4 py-2 rounded-xl text-sm font-medium transition-colors ${
                  mode === m ? 'text-white' : 'bg-white/5 text-white/50 hover:text-white/80'
                }`}
              >
                {mode === m && (
                  <motion.span
                    layoutId="auth-mode-pill"
                    className="absolute inset-0 rounded-xl gradient-primary"
                    transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                  />
                )}
                <span className="relative z-10">{m === 'login' ? 'Sign In' : 'Create Account'}</span>
              </button>
            ))}
          </motion.div>

          <form onSubmit={submit} className="space-y-3">
            <AnimatePresence mode="popLayout">
              {mode === 'register' && (
                <motion.div
                  key="register-fields"
                  className="space-y-3"
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                >
                  <motion.input
                    initial={{ opacity: 0, y: -8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.05 }}
                    whileFocus={{ scale: 1.015 }}
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="Email"
                    className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder:text-white/30 focus:outline-none focus:border-primary-500/50 text-sm transition-colors"
                  />
                  <motion.input
                    initial={{ opacity: 0, y: -8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.12 }}
                    whileFocus={{ scale: 1.015 }}
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Full name (optional)"
                    className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder:text-white/30 focus:outline-none focus:border-primary-500/50 text-sm transition-colors"
                  />
                </motion.div>
              )}
            </AnimatePresence>

            <motion.input
              variants={staggerItem}
              whileFocus={{ scale: 1.015 }}
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Username"
              autoComplete="username"
              className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder:text-white/30 focus:outline-none focus:border-primary-500/50 text-sm transition-colors"
            />
            <motion.input
              variants={staggerItem}
              whileFocus={{ scale: 1.015 }}
              required
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder:text-white/30 focus:outline-none focus:border-primary-500/50 text-sm transition-colors"
            />

            <AnimatePresence>
              {error && (
                <motion.p
                  className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2"
                  initial={{ opacity: 0, y: -6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                >
                  {error}
                </motion.p>
              )}
            </AnimatePresence>

            <motion.button
              variants={staggerItem}
              type="submit"
              disabled={busy}
              whileHover={{ scale: busy ? 1 : 1.02 }}
              whileTap={{ scale: busy ? 1 : 0.97 }}
              className="w-full px-4 py-3 rounded-xl gradient-primary text-white text-sm font-medium disabled:opacity-50"
            >
              {busy ? 'Working…' : mode === 'login' ? 'Sign In' : 'Create Twin'}
            </motion.button>
          </form>
        </motion.div>

        <p className="text-center text-[11px] text-white/25 mt-6">
          Your twin is private to your account.
        </p>
      </motion.div>
    </div>
  );
}
