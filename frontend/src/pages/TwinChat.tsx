import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { GlassPanel, StatBadge } from '../components/ui';
import { twinAPI } from '../api';

interface Message {
  role: 'user' | 'twin';
  content: string;
  timestamp: Date;
  confidence?: number;
}

export default function TwinChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [scores, setScores] = useState({ twin: 0, personality: 0, behavior: 0 });
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const userMsg: Message = { role: 'user', content: input.trim(), timestamp: new Date() };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await twinAPI.chat({
        message: userMsg.content,
        conversation_id: conversationId || undefined,
      });
      const data = res.data;
      setConversationId(data.conversation_id);
      setScores({
        twin: data.twin_confidence_score * 100,
        personality: data.personality_match_score * 100,
        behavior: data.behavior_similarity_score * 100,
      });
      setMessages((prev) => [
        ...prev,
        { role: 'twin', content: data.response, timestamp: new Date(), confidence: data.twin_confidence_score },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'twin', content: "I'm having trouble connecting to my neural core. Please ensure the backend is running.", timestamp: new Date() },
      ]);
    }
    setLoading(false);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-2rem)] gap-4">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-3xl font-display font-bold gradient-text mb-1">Digital Twin</h1>
          <p className="text-white/40 text-sm">Converse with your AI replica</p>
        </div>
        <div className="flex gap-2">
          <StatBadge label="Twin" value={`${scores.twin.toFixed(0)}%`} icon="⟐" />
          <StatBadge label="Personality" value={`${scores.personality.toFixed(0)}%`} icon="◎" />
          <StatBadge label="Behavior" value={`${scores.behavior.toFixed(0)}%`} icon="◇" />
        </div>
      </motion.div>

      {/* Chat Area */}
      <GlassPanel className="flex-1 flex flex-col overflow-hidden !p-0">
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 && (
            <motion.div
              className="flex flex-col items-center justify-center h-full text-center"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              <motion.div
                className="w-24 h-24 rounded-3xl gradient-primary flex items-center justify-center text-4xl mb-6"
                animate={{ scale: [1, 1.05, 1] }}
                transition={{ duration: 3, repeat: Infinity }}
              >
                ⟐
              </motion.div>
              <h2 className="text-xl font-display font-semibold text-white/70 mb-2">Your Digital Twin Awaits</h2>
              <p className="text-sm text-white/30 max-w-md">
                Start a conversation and your twin will respond based on your personality profile, behavioral patterns, and memories.
              </p>
              <div className="flex flex-wrap gap-2 mt-6 justify-center">
                {['Tell me about myself', 'What would I decide?', 'How am I feeling lately?', 'What are my goals?'].map((q) => (
                  <motion.button
                    key={q}
                    onClick={() => { setInput(q); }}
                    className="px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-sm text-white/50 hover:text-white/80 hover:border-primary-500/30 transition-all"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    {q}
                  </motion.button>
                ))}
              </div>
            </motion.div>
          )}

          <AnimatePresence>
            {messages.map((msg, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0 }}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`max-w-[70%] ${msg.role === 'user' ? 'order-2' : ''}`}>
                  <div
                    className={`px-5 py-3 rounded-2xl ${
                      msg.role === 'user'
                        ? 'bg-gradient-to-br from-primary-600 to-primary-700 text-white rounded-br-md'
                        : 'glass border border-white/10 text-white/90 rounded-bl-md'
                    }`}
                  >
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                  </div>
                  <div className={`flex items-center gap-2 mt-1 ${msg.role === 'user' ? 'justify-end' : ''}`}>
                    <span className="text-[10px] text-white/20">
                      {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                    {msg.confidence !== undefined && (
                      <span className="text-[10px] text-primary-400/60">
                        {(msg.confidence * 100).toFixed(0)}% confident
                      </span>
                    )}
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {loading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex justify-start"
            >
              <div className="glass px-5 py-3 rounded-2xl rounded-bl-md border border-white/10">
                <motion.div className="flex gap-1.5">
                  {[0, 1, 2].map((i) => (
                    <motion.div
                      key={i}
                      className="w-2 h-2 rounded-full bg-primary-400"
                      animate={{ scale: [1, 1.3, 1], opacity: [0.5, 1, 0.5] }}
                      transition={{ duration: 1, repeat: Infinity, delay: i * 0.2 }}
                    />
                  ))}
                </motion.div>
              </div>
            </motion.div>
          )}

          <div ref={endRef} />
        </div>

        {/* Input */}
        <div className="p-4 border-t border-white/5">
          <div className="flex gap-3">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
              placeholder="Talk to your digital twin..."
              className="flex-1 px-5 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder:text-white/30 focus:outline-none focus:border-primary-500/40 transition-colors text-sm"
            />
            <motion.button
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              className="px-6 py-3 rounded-xl gradient-primary text-white font-medium text-sm disabled:opacity-40 disabled:cursor-not-allowed"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              Send
            </motion.button>
          </div>
        </div>
      </GlassPanel>
    </div>
  );
}
