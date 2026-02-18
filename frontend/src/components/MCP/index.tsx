import { useAppStore } from '../../stores/appStore';
import { useEffect } from 'react';
import { api } from '../../lib/api';
import { useState } from 'react';
import { Loader2, Plus, Trash2, ToggleLeft, ToggleRight, Play, Square } from 'lucide-react';

export function MCP() {
  const { mcpServers, loadMCP, loading } = useAppStore();
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ name: '', command: '', args: '', url: '' });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadMCP();
  }, []);

  const handleToggle = async (name: string, enabled: boolean) => {
    await api.toggleMCP(name, !enabled);
    await loadMCP();
  };

  const handleDelete = async (name: string) => {
    if (confirm(`Delete ${name}?`)) {
      await api.deleteMCP(name);
      await loadMCP();
    }
  };

  const handleAdd = async () => {
    if (!form.name) return;
    setSaving(true);
    try {
      await api.addMCP({
        name: form.name,
        transport: form.command ? 'stdio' : 'sse',
        command: form.command || undefined,
        args: form.args ? form.args.split(' ') : undefined,
        url: form.url || undefined,
        enabled: true,
      });
      await loadMCP();
      setShowAdd(false);
      setForm({ name: '', command: '', args: '', url: '' });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><Loader2 className="w-8 h-8 animate-spin text-claw-500" /></div>;
  }

  return (
    <div className="h-full overflow-y-auto scroll-container p-6">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">MCP Servers</h2>
          <p className="text-gray-400">Manage Model Context Protocol servers</p>
        </div>
        <button onClick={() => setShowAdd(true)} className="btn-primary flex items-center gap-2">
          <Plus size={18} /> Add Server
        </button>
      </div>

      <div className="grid gap-4">
        {mcpServers.map((server) => (
          <div key={server.name} className="bg-dark-800 border border-dark-600 rounded-2xl p-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-white">{server.name}</h3>
                <p className="text-sm text-gray-400">{server.command || server.url}</p>
              </div>
              <div className="flex items-center gap-2">
                <button onClick={() => handleToggle(server.name, server.enabled)} className="p-2">
                  {server.enabled ? <ToggleRight className="text-green-500" size={24} /> : <ToggleLeft className="text-gray-500" size={24} />}
                </button>
                <button onClick={() => handleDelete(server.name)} className="p-2 text-gray-400 hover:text-red-400">
                  <Trash2 size={18} />
                </button>
              </div>
            </div>
          </div>
        ))}

        {mcpServers.length === 0 && (
          <div className="bg-dark-800 border border-dark-600 rounded-2xl p-12 text-center">
            <p className="text-gray-400">No MCP servers configured</p>
          </div>
        )}
      </div>

      {showAdd && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-dark-800 border border-dark-600 rounded-2xl p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold text-white mb-4">Add MCP Server</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Name</label>
                <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="input-base" placeholder="my-server" />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Command (stdio)</label>
                <input value={form.command} onChange={(e) => setForm({ ...form, command: e.target.value })} className="input-base" placeholder="npx -y @modelcontextprotocol/server-filesystem" />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Or URL (SSE)</label>
                <input value={form.url} onChange={(e) => setForm({ ...form, url: e.target.value })} className="input-base" placeholder="http://localhost:3000/sse" />
              </div>
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
