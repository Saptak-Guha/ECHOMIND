import { motion } from 'framer-motion';
import { useEffect, useRef, useState } from 'react';
import type { ReactNode } from 'react';

// ─── Animated Score Card ───────────────────────────────────────────────

interface ScoreCardProps {
  title: string;
  value: number;
  suffix?: string;
  icon: string;
  color: string;
  description?: string;
}

export function ScoreCard({ title, value, suffix = '%', icon, color, description }: ScoreCardProps) {
  const colorMap: Record<string, string> = {
    primary: 'from-primary-600 to-primary-400',
    accent: 'from-accent-600 to-accent-400',
    neural: 'from-neural-500 to-neural-400',
    danger: 'from-red-600 to-red-400',
    warning: 'from-amber-600 to-amber-400',
  };

  return (
    <motion.div
      className="glass-card p-5 rounded-2xl"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02 }}
      transition={{ duration: 0.3 }}
    >
      <div className="flex items-start justify-between mb-4">
        <motion.div
          className={`w-10 h-10 rounded-xl bg-gradient-to-br ${colorMap[color] || colorMap.primary} flex items-center justify-center text-white text-lg`}
          whileHover={{ rotate: 8, scale: 1.08 }}
          transition={{ type: 'spring', stiffness: 300, damping: 15 }}
        >
          {icon}
        </motion.div>
        <span className="text-xs text-white/40 uppercase tracking-wider">{title}</span>
      </div>
      <div className="flex items-end gap-1 mb-1">
        <motion.span
          className="text-3xl font-display font-bold text-white"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          <AnimatedNumber value={value} decimals={1} />
        </motion.span>
        <span className="text-lg text-white/40 mb-0.5">{suffix}</span>
      </div>
      {description && <p className="text-xs text-white/30">{description}</p>}
      <div className="mt-3 h-1.5 rounded-full bg-white/5 overflow-hidden">
        <motion.div
          className={`h-full rounded-full bg-gradient-to-r ${colorMap[color] || colorMap.primary}`}
          initial={{ width: '0%' }}
          animate={{ width: `${Math.min(value, 100)}%` }}
          transition={{ duration: 1.5, ease: 'easeOut', delay: 0.3 }}
        />
      </div>
    </motion.div>
  );
}

// ─── Glass Panel ───────────────────────────────────────────────────────

interface GlassPanelProps {
  children: ReactNode;
  className?: string;
  title?: string;
  subtitle?: string;
  icon?: string;
}

export function GlassPanel({ children, className = '', title, subtitle, icon }: GlassPanelProps) {
  return (
    <motion.div
      className={`glass-card p-6 rounded-2xl ${className}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      {(title || icon) && (
        <div className="flex items-center gap-3 mb-4">
          {icon && <span className="text-xl text-primary-400">{icon}</span>}
          <div>
            {title && <h3 className="font-display font-semibold text-white">{title}</h3>}
            {subtitle && <p className="text-xs text-white/40">{subtitle}</p>}
          </div>
        </div>
      )}
      {children}
    </motion.div>
  );
}

// ─── Neural Background ─────────────────────────────────────────────────

export function NeuralBackground() {
  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
      {/* Gradient orbs */}
      <div className="absolute -top-40 -right-40 w-96 h-96 bg-primary-600/10 rounded-full blur-3xl animate-float" />
      <div className="absolute top-1/2 -left-40 w-80 h-80 bg-accent-500/8 rounded-full blur-3xl animate-float" style={{ animationDelay: '2s' }} />
      <div className="absolute -bottom-40 right-1/3 w-72 h-72 bg-neural-400/5 rounded-full blur-3xl animate-float" style={{ animationDelay: '4s' }} />

      {/* Grid pattern */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `
            linear-gradient(rgba(99, 102, 241, 0.3) 1px, transparent 1px),
            linear-gradient(90deg, rgba(99, 102, 241, 0.3) 1px, transparent 1px)
          `,
          backgroundSize: '60px 60px',
        }}
      />
    </div>
  );
}

// ─── Loading Spinner ───────────────────────────────────────────────────

export function NeuralLoader() {
  return (
    <div className="flex flex-col items-center justify-center py-20">
      <div className="relative w-16 h-16">
        <motion.div
          className="absolute inset-0 rounded-full border-2 border-primary-500/30"
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
        />
        <motion.div
          className="absolute inset-1 rounded-full border-2 border-t-accent-400 border-r-transparent border-b-transparent border-l-transparent"
          animate={{ rotate: -360 }}
          transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
        />
        <motion.div
          className="absolute inset-3 rounded-full bg-primary-500/20"
          animate={{ scale: [1, 1.2, 1] }}
          transition={{ duration: 2, repeat: Infinity }}
        />
      </div>
      <motion.p
        className="mt-4 text-sm text-white/40"
        animate={{ opacity: [0.4, 1, 0.4] }}
        transition={{ duration: 2, repeat: Infinity }}
      >
        Neural processing...
      </motion.p>
    </div>
  );
}

// ─── Stat Badge ────────────────────────────────────────────────────────

export function StatBadge({ label, value, icon }: { label: string; value: string | number; icon?: string }) {
  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/5">
      {icon && <span className="text-sm">{icon}</span>}
      <span className="text-xs text-white/40">{label}:</span>
      <span className="text-xs font-medium text-white/80">{value}</span>
    </div>
  );
}

// ─── Empty State ───────────────────────────────────────────────────────

export function EmptyState({ title, description, icon }: { title: string; description: string; icon: string }) {
  return (
    <motion.div
      className="flex flex-col items-center justify-center py-16 text-center"
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
    >
      <span className="text-5xl mb-4 opacity-30">{icon}</span>
      <h3 className="text-lg font-display font-semibold text-white/60 mb-2">{title}</h3>
      <p className="text-sm text-white/30 max-w-md">{description}</p>
    </motion.div>
  );
}

// ─── Animated Counter ──────────────────────────────────────────────────

/**
 * Counts up to `value` on mount and re-animates whenever it changes, so numbers
 * arriving from the API feel earned rather than snapping into place.
 */
export function AnimatedNumber({
  value,
  decimals = 0,
  suffix = '',
  prefix = '',
  duration = 1.2,
  className = '',
}: {
  value: number;
  decimals?: number;
  suffix?: string;
  prefix?: string;
  duration?: number;
  className?: string;
}) {
  const [display, setDisplay] = useState(0);
  const fromRef = useRef(0);

  useEffect(() => {
    const from = fromRef.current;
    const target = Number.isFinite(value) ? value : 0;
    if (from === target) return;

    let frame = 0;
    const start = performance.now();
    const tick = (now: number) => {
      const t = Math.min((now - start) / (duration * 1000), 1);
      // easeOutCubic — fast start, gentle landing
      const eased = 1 - Math.pow(1 - t, 3);
      setDisplay(from + (target - from) * eased);
      if (t < 1) frame = requestAnimationFrame(tick);
      else fromRef.current = target;
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [value, duration]);

  return (
    <span className={className}>
      {prefix}
      {display.toFixed(decimals)}
      {suffix}
    </span>
  );
}

// ─── Stagger Helpers ───────────────────────────────────────────────────

/** Parent variant: children animate in one after another. */
export const staggerContainer = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.07, delayChildren: 0.05 },
  },
};

/** Child variant paired with `staggerContainer`. */
export const staggerItem = {
  hidden: { opacity: 0, y: 16 },
  show: {
    opacity: 1,
    y: 0,
    transition: { type: 'spring' as const, stiffness: 260, damping: 24 },
  },
};

// ─── Page Shell ────────────────────────────────────────────────────────

/**
 * Standard page wrapper: animated heading plus a staggered body. Keeps every
 * route entering the same way instead of each page inventing its own timing.
 */
export function PageHeader({
  title,
  subtitle,
  actions,
}: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}) {
  return (
    <motion.div
      className="flex items-end justify-between gap-4 flex-wrap"
      initial={{ opacity: 0, y: -12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
    >
      <div>
        <h1 className="text-3xl font-display font-bold gradient-text mb-1">{title}</h1>
        {subtitle && <p className="text-white/40 text-sm">{subtitle}</p>}
      </div>
      {actions}
    </motion.div>
  );
}

// ─── Animated Progress Bar ─────────────────────────────────────────────

export function ProgressBar({
  value,
  gradient = 'from-primary-500 to-accent-400',
  delay = 0,
}: {
  value: number;
  gradient?: string;
  delay?: number;
}) {
  return (
    <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
      <motion.div
        className={`h-full rounded-full bg-gradient-to-r ${gradient}`}
        initial={{ width: '0%' }}
        animate={{ width: `${Math.max(0, Math.min(value, 100))}%` }}
        transition={{ duration: 1.2, ease: 'easeOut', delay }}
      />
    </div>
  );
}

// ─── Shimmer Skeleton ──────────────────────────────────────────────────

/** Placeholder block shown while a panel's data is in flight. */
export function Skeleton({ className = 'h-24' }: { className?: string }) {
  return (
    <div className={`rounded-xl bg-white/5 overflow-hidden relative ${className}`}>
      <motion.div
        className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent"
        animate={{ x: ['-100%', '100%'] }}
        transition={{ duration: 1.6, repeat: Infinity, ease: 'linear' }}
      />
    </div>
  );
}
