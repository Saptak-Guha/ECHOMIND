import { motion } from 'framer-motion';
import { NavLink } from 'react-router-dom';
import { useStore } from '../store';

const navItems = [
  { path: '/', label: 'Dashboard', icon: '◈', description: 'Overview & Metrics' },
  { path: '/twin', label: 'Digital Twin', icon: '⟐', description: 'Chat with your twin' },
  { path: '/memory', label: 'Memory Vault', icon: '◉', description: 'Long-term memories' },
  { path: '/personality', label: 'Personality', icon: '◎', description: 'Personality engine' },
  { path: '/behavior', label: 'Behavior', icon: '◇', description: 'Behavior analytics' },
  { path: '/simulator', label: 'Simulator', icon: '⟡', description: 'Future simulations' },
  { path: '/graph', label: 'Knowledge', icon: '⬡', description: 'Knowledge graph' },
  { path: '/emotions', label: 'Emotions', icon: '❋', description: 'Emotional insights' },
  { path: '/timeline', label: 'Timeline', icon: '⧖', description: 'Life timeline' },
  { path: '/settings', label: 'Settings', icon: '⚙', description: 'Configuration' },
];

export default function Sidebar() {
  const { sidebarOpen, toggleSidebar, user, signOut } = useStore();

  return (
    <motion.aside
      initial={{ x: -280 }}
      animate={{ x: 0, width: sidebarOpen ? 280 : 72 }}
      transition={{ type: 'spring', damping: 25, stiffness: 200 }}
      className="fixed left-0 top-0 h-screen z-50 glass flex flex-col"
      style={{ borderRight: '1px solid rgba(99, 102, 241, 0.15)' }}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-6 border-b border-white/5">
        <motion.div
          className="w-10 h-10 rounded-xl gradient-primary flex items-center justify-center text-white font-bold text-lg flex-shrink-0"
          whileHover={{ scale: 1.1, rotate: 10 }}
          whileTap={{ scale: 0.95 }}
          onClick={toggleSidebar}
          style={{ cursor: 'pointer' }}
        >
          E
        </motion.div>
        {sidebarOpen && (
          <motion.div
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -10 }}
          >
            <h1 className="font-display text-lg font-bold gradient-text">EchoMind</h1>
            <p className="text-[10px] text-white/40 tracking-wider uppercase">Digital Twin AI</p>
          </motion.div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
        {navItems.map((item, i) => (
          <motion.div
            key={item.path}
            initial={{ opacity: 0, x: -18 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.05 + i * 0.035, type: 'spring', stiffness: 260, damping: 22 }}
          >
          <NavLink
            to={item.path}
            className={({ isActive }) =>
              `relative flex items-center gap-3 px-3 py-2.5 rounded-xl transition-colors duration-200 group ${
                isActive ? 'text-primary-300' : 'text-white/50 hover:text-white/80 hover:bg-white/5'
              }`
            }
          >
            {({ isActive }) => (
              <>
                {/* Sliding highlight: one element that travels between items. */}
                {isActive && (
                  <motion.span
                    layoutId="nav-active-bg"
                    className="absolute inset-0 rounded-xl bg-primary-600/20 border border-primary-500/20"
                    transition={{ type: 'spring', stiffness: 380, damping: 32 }}
                  />
                )}
                <motion.span
                  className={`relative z-10 text-lg flex-shrink-0 w-6 text-center ${isActive ? 'text-primary-400' : ''}`}
                  whileHover={{ scale: 1.25, rotate: 6 }}
                  transition={{ type: 'spring', stiffness: 300, damping: 14 }}
                >
                  {item.icon}
                </motion.span>
                {sidebarOpen && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="relative z-10 min-w-0"
                  >
                    <span className="text-sm font-medium block">{item.label}</span>
                    <span className="text-[10px] text-white/30 block truncate">{item.description}</span>
                  </motion.div>
                )}
                {isActive && sidebarOpen && (
                  <motion.div
                    layoutId="active-indicator"
                    className="relative z-10 ml-auto w-1.5 h-1.5 rounded-full bg-primary-400"
                    transition={{ type: 'spring', damping: 25 }}
                  />
                )}
              </>
            )}
          </NavLink>
          </motion.div>
        ))}
      </nav>

      {/* Bottom Section */}
      {sidebarOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="p-4 border-t border-white/5"
        >
          {/* Signed-in identity — the twin below belongs to this account only. */}
          <div className="glass-card p-3 rounded-xl mb-3">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center text-sm font-display font-bold flex-shrink-0">
                {(user?.full_name || user?.username || '?').charAt(0).toUpperCase()}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-xs text-white/80 truncate">{user?.full_name || user?.username}</p>
                <p className="text-[10px] text-white/35 truncate">@{user?.username}</p>
              </div>
            </div>
            <motion.button
              onClick={signOut}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.97 }}
              className="mt-2 w-full text-[11px] text-white/45 hover:text-white/80 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
            >
              Sign out
            </motion.button>
          </div>

          <div className="glass-card p-3 rounded-xl">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-2 h-2 rounded-full bg-neural-400 animate-pulse" />
              <span className="text-xs text-white/60">Twin Status</span>
            </div>
            <p className="text-[11px] text-white/40">Learning & Evolving</p>
            <div className="mt-2 h-1 rounded-full bg-white/5 overflow-hidden">
              <motion.div
                className="h-full rounded-full gradient-primary"
                initial={{ width: '0%' }}
                animate={{ width: '45%' }}
                transition={{ duration: 2, ease: 'easeOut' }}
              />
            </div>
          </div>
        </motion.div>
      )}
    </motion.aside>
  );
}
