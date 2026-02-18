import { useAppStore } from '../../stores/appStore';
import { useEffect, useState } from 'react';
import { api } from '../../lib/api';
import { Loader2, Plus, Trash2, Brain } from 'lucide-react';

export function Agents() {
  const { agents, loadAgents, loading } = useAppStore();
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ name: '', description: '', system_prompt: '', model_id: '' });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadAgents();
  }, []);

  const handleAdd = async () => {
    if (!form.name) return;
    setSaving(true);
    try {
      await api.addAgent({ name: form.name, description: form.description, system_prompt: form.system_prompt, model_id: form.model_id || undefined });
      await loadAgents();
      setShowAdd(false);
      setForm({ name: '', description: '', system_prompt: '', model_id: '' });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (confirm('Delete this agent?')) {
      await api.deleteAgent(id);
      await loadAgents();
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><Loader2 className="w-8 h-8 animate-spin text-claw-500" /></div>;
  }

  return (
    <div className="h-full overflow-y-auto scroll-container p-6">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">Agents</h2>
          <p className="text-gray-400">Manage AI agents with different personalities</p>
        </div>
        <button onClick={() => setShowAdd(true)} className="btn-primary flex items-center gap-2">
          <Plus size={18} /> Add Agent
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {agents.map((agent) => (
          <div key={agent.id} className="bg-dark-800 border border-dark-600 rounded-2xl p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-indigo-500/20 flex items-center justify-center">
                  <Brain className="text-indigo-400" size={20} />
                </div>
                <div>
                  <h3 className="font-medium text-white">{agent.name}</h3>
                  <p className="text-xs text-gray-400">{agent.model_id || 'Default model'}</p>
                </div>
              </div>
              <button onClick={() => handleDelete(agent.id)} className="text-gray-400 hover:text-red-400">
                <Trash2 size={16} />
              </button>
            </div>
            {agent.description && <p className="text-sm text-gray-400">{agent.description}</p>}
          </div>
        ))}
      </div>

      {showAdd && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-dark-800 border border-dark-600 rounded-2xl p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold text-white mb-4">Add Agent</h3>
            <div className="space-y-4">
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="input-base" placeholder="Agent name" />
              <input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} className="input-base" placeholder="Description" />
              <textarea value={form.system_prompt} onChange={(e) => setForm({ ...form, system_prompt: e.target.value })} className="input-base min-h-24" placeholder="System prompt" />
              <input value={form.model_id} onChange={(e) => setForm({ ...form, model_id: e.target.value })} className="input-base" placeholder="Model ID (optional)" />
            </div>
            <div className="flex gap-3 mt-6">
              <button onClick={handleAdd} disabled={saving || !form.name} className="btn-primary flex items-center gap-2">
                {saving && <Loader2 className="animate-spin" size={16} />} Add
              </button>
              <button onClick={() => setShowAdd(false)} className="btn-secondary">Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
