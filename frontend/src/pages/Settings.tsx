import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { GlassPanel, PageHeader, staggerContainer, staggerItem } from '../components/ui';
import { analyticsAPI, ingestionAPI } from '../api';

export default function Settings() {
  const [docTitle, setDocTitle] = useState('');
  const [docContent, setDocContent] = useState('');
  const [docType, setDocType] = useState('note');
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [llm, setLlm] = useState<any>(null);
  const [llmError, setLlmError] = useState('');

  // Which provider is actually answering. Without this the user cannot tell a
  // real LLM reply from the local heuristic fallback.
  useEffect(() => {
    analyticsAPI
      .getLLMStatus()
      .then((r) => setLlm(r.data))
      .catch((e) => setLlmError(e?.response?.data?.detail || e.message || 'Unavailable'));
  }, []);

  const uploadDocument = async () => {
    if (!docTitle.trim() || !docContent.trim()) return;
    setUploading(true);
    setUploadResult(null);
    try {
      const res = await ingestionAPI.uploadDocument({ title: docTitle, content: docContent, doc_type: docType });
      setUploadResult({ success: true, data: res.data });
      setDocTitle('');
      setDocContent('');
    } catch (err: any) {
      setUploadResult({ success: false, error: err.message || 'Upload failed' });
    }
    setUploading(false);
  };

  return (
    <motion.div variants={staggerContainer} initial="hidden" animate="show" className="space-y-6">
      <PageHeader title="Settings" subtitle="Configure your digital twin and manage data" />

      {/* Data Upload */}
      <motion.div variants={staggerItem}>
      <GlassPanel title="Upload Data" icon="📄" subtitle="Feed your twin with documents, notes, and conversations">
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input
              value={docTitle}
              onChange={(e) => setDocTitle(e.target.value)}
              placeholder="Document title..."
              className="px-5 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder:text-white/30 focus:outline-none focus:border-primary-500/40 text-sm"
            />
            <select
              value={docType}
              onChange={(e) => setDocType(e.target.value)}
              className="px-5 py-3 rounded-xl bg-white/5 border border-white/10 text-white focus:outline-none focus:border-primary-500/40 text-sm"
            >
              {['note', 'email', 'journal', 'social', 'transcript', 'chat', 'article', 'resume', 'other'].map((t) => (
                <option key={t} value={t} className="bg-surface-100">{t.charAt(0).toUpperCase() + t.slice(1)}</option>
              ))}
            </select>
          </div>
          <textarea
            value={docContent}
            onChange={(e) => setDocContent(e.target.value)}
            placeholder="Paste your content here — emails, journal entries, chat logs, notes, social posts..."
            className="w-full h-48 px-5 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder:text-white/30 focus:outline-none focus:border-primary-500/40 text-sm resize-none"
          />
          <div className="flex items-center gap-4">
            <motion.button
              onClick={uploadDocument}
              disabled={uploading || !docTitle.trim() || !docContent.trim()}
              className="px-6 py-3 rounded-xl gradient-primary text-white font-medium text-sm disabled:opacity-40"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              {uploading ? '⏳ Processing...' : '🧠 Upload & Process'}
            </motion.button>
            <span className="text-xs text-white/30">Your data is processed through 10 AI engines</span>
          </div>
          {uploadResult && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`p-4 rounded-xl border ${uploadResult.success ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300' : 'bg-red-500/10 border-red-500/30 text-red-300'}`}
            >
              {uploadResult.success
                ? `✅ Document processed successfully! Status: ${uploadResult.data.processing_status}`
                : `❌ ${uploadResult.error}`}
            </motion.div>
          )}
        </div>
      </GlassPanel>
      </motion.div>

      {/* LLM Provider */}
      <GlassPanel title="LLM Provider" icon="🔑" subtitle="Which engine is answering your twin">
        {llmError ? (
          <div className="text-sm text-red-300">❌ {llmError}</div>
        ) : !llm ? (
          <div className="text-sm text-white/40">Checking…</div>
        ) : (
          <div className="space-y-3">
            <div className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/5">
              <div>
                <span className="text-sm text-white/70 block">Active provider</span>
                <span className="text-xs text-white/30">
                  {llm.mode === 'llm' ? 'Live model responses' : 'Local heuristics — no provider reachable'}
                </span>
              </div>
              <span
                className={`px-3 py-1.5 rounded-lg text-xs font-medium ${
                  llm.active_provider ? 'bg-emerald-500/20 text-emerald-300' : 'bg-amber-500/20 text-amber-300'
                }`}
              >
                {llm.active_provider || 'heuristics'}
              </span>
            </div>

            <div className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/5">
              <div>
                <span className="text-sm text-white/70 block">Ollama (local)</span>
                <span className="text-xs text-white/30">
                  model: {llm.ollama_model_configured}
                  {llm.ollama_models?.length ? ` — installed: ${llm.ollama_models.join(', ')}` : ''}
                </span>
              </div>
              <span
                className={`px-3 py-1.5 rounded-lg text-xs font-medium ${
                  llm.ollama_running ? 'bg-emerald-500/20 text-emerald-300' : 'bg-red-500/20 text-red-400'
                }`}
              >
                {llm.ollama_running ? 'running' : 'not running'}
              </span>
            </div>

            <div className="p-4 rounded-xl bg-white/5 border border-white/5 text-xs text-white/40 space-y-1">
              <p>
                <strong className="text-white/60">Chain:</strong>{' '}
                {llm.chain?.length ? llm.chain.join(' → ') : 'none configured'}
              </p>
              {llm.retired?.length > 0 && (
                <p>
                  <strong className="text-white/60">Retired this session:</strong> {llm.retired.join(', ')}
                </p>
              )}
              <p className="text-white/20 pt-1">Configured in .env (LLM_PROVIDER); restart the backend to change.</p>
            </div>
          </div>
        )}
      </GlassPanel>

      {/* Data Privacy */}
      <GlassPanel title="Data & Privacy" icon="🔒" subtitle="Control your digital identity data">
        <div className="space-y-3">
          {[
            { label: 'Encrypted Memory Storage', desc: 'All memories are encrypted at rest', enabled: true },
            { label: 'Data Export', desc: 'Export all your data as JSON', action: 'Export' },
            { label: 'Memory Deletion', desc: 'Delete all memories and start fresh', action: 'Delete All', danger: true },
          ].map((item) => (
            <div key={item.label} className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/5">
              <div>
                <span className="text-sm text-white/70 block">{item.label}</span>
                <span className="text-xs text-white/30">{item.desc}</span>
              </div>
              {'enabled' in item ? (
                <div className="w-10 h-6 rounded-full bg-emerald-500/30 flex items-center justify-end px-1">
                  <div className="w-4 h-4 rounded-full bg-emerald-400" />
                </div>
              ) : (
                <button className={`px-4 py-1.5 rounded-lg text-xs font-medium ${item.danger ? 'bg-red-500/20 text-red-400' : 'bg-white/5 text-white/50'}`}>
                  {item.action}
                </button>
              )}
            </div>
          ))}
        </div>
      </GlassPanel>

      {/* About */}
      <GlassPanel title="About EchoMind" icon="🧠">
        <div className="text-xs text-white/40 space-y-2">
          <p><strong className="text-white/60">Version:</strong> 1.0.0</p>
          <p><strong className="text-white/60">Modules:</strong> 10 AI Engines Active</p>
          <p><strong className="text-white/60">Architecture:</strong> React + FastAPI + PostgreSQL + Neo4j + ChromaDB + FAISS + Redis</p>
          <p className="pt-2 text-white/20">Human Digital Twin Intelligence Platform — Not a chatbot. Not RAG. A true Digital Identity Engine.</p>
        </div>
      </GlassPanel>
    </motion.div>
  );
}
