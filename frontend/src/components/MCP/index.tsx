import { useAppStore } from '../../stores/appStore';
import { api } from '../../lib/api';
import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Loader2, Plus, Trash2, ToggleLeft, ToggleRight,
  Edit, TestTube, Terminal, Globe,
  ChevronDown, ChevronUp, Copy, CheckCircle, XCircle
} from 'lucide-react';
import clsx from 'clsx';

interface MCPServerFull {
  name: string;
  enabled: boolean;
  command?: string;
  args?: string[];
  url?: string;
  env?: Record<string, string>;
  transport: 'stdio' | 'sse';
  status?: 'running' | 'stopped' | 'error';
  tools_count?: number;
}

export function MCP() {
  const { mcpServers, loadMCP, loading } = useAppStore();
  const [servers, setServers] = useState<MCPServerFull[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [editingServer, setEditingServer] = useState<MCPServerFull | null>(null);
  const [form, setForm] = useState({
    name: '',
    serverType: 'local' as 'local' | 'remote',
    command: '',
    args: '',
    url: '',
    env: '',
    enabled: true,
  });
  const [saving, setSaving] = useState(false);
  const [testingServer, setTestingServer] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<Record<string, { ok: boolean; msg: string }>>({});
  const [expandedServer, setExpandedServer] = useState<string | null>(null);

  useEffect(() => {
    loadMCP();
  }, []);

  useEffect(() => {
    setServers(mcpServers.map(s => ({
      ...s,
      transport: s.command ? 'stdio' : 'sse',
      status: s.enabled ? 'running' : 'stopped',
    })));
  }, [mcpServers]);

  const resetForm = () => {
    setForm({
      name: '',
      serverType: 'local',
      command: '',
      args: '',
      url: '',
      env: '',
      enabled: true,
    });
    setEditingServer(null);
  };

  const handleEdit = (server: MCPServerFull) => {
    setEditingServer(server);
    setForm({
      name: server.name,
      serverType: server.url ? 'remote' : 'local',
      command: server.command || '',
      args: (server.args || []).join(' '),
      url: server.url || '',
      env: Object.entries(server.env || {}).map(([k, v]) => `${k}=${v}`).join('\n'),
      enabled: server.enabled,
    });
    setShowAdd(true);
  };

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

  const handleTest = async (server: MCPServerFull) => {
    setTestingServer(server.name);
    setTestResults(prev => {
      const copy = { ...prev };
      delete copy[server.name];
      return copy;
    });
    
    try {
      const result = await fetch('/api/mcp/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: server.name }),
      }).then(r => r.json());
      
      setTestResults(prev => ({
        ...prev,
        [server.name]: { ok: result.success, msg: result.message || 'Connection successful' },
      }));
    } catch (e) {
      setTestResults(prev => ({
        ...prev,
        [server.name]: { ok: false, msg: String(e) },
      }));
    } finally {
      setTestingServer(null);
    }
  };

  const handleSave = async () => {
    if (!form.name) return;
    setSaving(true);
    
    try {
      const env: Record<string, string> = {};
      if (form.env) {
        form.env.split('\n').forEach(line => {
          const [key, ...values] = line.split('=');
          if (key && values.length > 0) {
            env[key.trim()] = values.join('=').trim();
          }
        });
      }

      const data = {
        name: form.name,
        transport: form.serverType === 'local' ? 'stdio' : 'sse',
        command: form.serverType === 'local' ? form.command : undefined,
        args: form.serverType === 'local' && form.args ? form.args.split(' ') : undefined,
        url: form.serverType === 'remote' ? form.url : undefined,
        env: Object.keys(env).length > 0 ? env : undefined,
        enabled: form.enabled,
      };

      if (editingServer) {
        await api.updateMCP(editingServer.name, data);
      } else {
        await api.addMCP(data);
      }
      
      await loadMCP();
      setShowAdd(false);
      resetForm();
    } finally {
      setSaving(false);
    }
  };

  const handleDuplicate = (server: MCPServerFull) => {
    setEditingServer(null);
    setForm({
      name: `${server.name}-copy`,
      serverType: server.url ? 'remote' : 'local',
      command: server.command || '',
      args: (server.args || []).join(' '),
      url: server.url || '',
      env: Object.entries(server.env || {}).map(([k, v]) => `${k}=${v}`).join('\n'),
      enabled: false,
    });
    setShowAdd(true);
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
        <button onClick={() => { resetForm(); setShowAdd(true); }} className="btn-primary flex items-center gap-2">
          <Plus size={18} /> Add Server
        </button>
      </div>

      <div className="space-y-4">
        {servers.map((server) => {
          const testResult = testResults[server.name];
          const isExpanded = expandedServer === server.name;
          
          return (
            <motion.div
              key={server.name}
              layout
              className="bg-dark-800 border border-dark-600 rounded-2xl overflow-hidden"
            >
              <div className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={clsx(
                      'w-10 h-10 rounded-lg flex items-center justify-center',
                      server.enabled ? 'bg-green-500/20' : 'bg-gray-500/20'
                    )}>
                      {server.url ? (
                        <Globe size={20} className={server.enabled ? 'text-green-400' : 'text-gray-400'} />
                      ) : (
                        <Terminal size={20} className={server.enabled ? 'text-green-400' : 'text-gray-400'} />
                      )}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-white">{server.name}</h3>
                        <span className={clsx(
                          'text-xs px-2 py-0.5 rounded-full',
                          server.enabled ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'
                        )}>
                          {server.enabled ? 'Enabled' : 'Disabled'}
                        </span>
                        {server.status === 'running' && (
                          <span className="flex items-center gap-1 text-xs text-green-400">
                            <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" />
                            Running
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-400 truncate max-w-md">
                        {server.command || server.url}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleTest(server)}
                      disabled={testingServer === server.name}
                      className="p-2 text-gray-400 hover:text-white hover:bg-dark-600 rounded-lg transition-all"
                      title="Test connection"
                    >
                      {testingServer === server.name ? (
                        <Loader2 size={18} className="animate-spin" />
                      ) : (
                        <TestTube size={18} />
                      )}
                    </button>
                    <button
                      onClick={() => handleEdit(server)}
                      className="p-2 text-gray-400 hover:text-white hover:bg-dark-600 rounded-lg transition-all"
                      title="Edit server"
                    >
                      <Edit size={18} />
                    </button>
                    <button
                      onClick={() => handleToggle(server.name, server.enabled)}
                      className="p-2"
                    >
                      {server.enabled ? (
                        <ToggleRight className="text-green-500" size={24} />
                      ) : (
                        <ToggleLeft className="text-gray-500" size={24} />
                      )}
                    </button>
                    <button
                      onClick={() => setExpandedServer(isExpanded ? null : server.name)}
                      className="p-2 text-gray-400 hover:text-white hover:bg-dark-600 rounded-lg transition-all"
                    >
                      {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                    </button>
                    <button
                      onClick={() => handleDelete(server.name)}
                      className="p-2 text-gray-400 hover:text-red-400 hover:bg-dark-600 rounded-lg transition-all"
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                </div>

                {testResult && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    className={clsx(
                      'mt-3 p-3 rounded-lg',
                      testResult.ok ? 'bg-green-500/10 border border-green-500/30' : 'bg-red-500/10 border border-red-500/30'
                    )}
                  >
                    <div className="flex items-center gap-2">
                      {testResult.ok ? (
                        <CheckCircle size={16} className="text-green-400" />
                      ) : (
                        <XCircle size={16} className="text-red-400" />
                      )}
                      <span className={testResult.ok ? 'text-green-400' : 'text-red-400'}>{testResult.msg}</span>
                    </div>
                  </motion.div>
                )}

                <AnimatePresence>
                  {isExpanded && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="mt-4 pt-4 border-t border-dark-600"
                    >
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <p className="text-gray-500 mb-1">Transport</p>
                          <p className="text-gray-300">{server.transport}</p>
                        </div>
                        {server.args && server.args.length > 0 && (
                          <div>
                            <p className="text-gray-500 mb-1">Arguments</p>
                            <p className="text-gray-300 font-mono text-xs">{server.args.join(' ')}</p>
                          </div>
                        )}
                        {server.env && Object.keys(server.env).length > 0 && (
                          <div className="col-span-2">
                            <p className="text-gray-500 mb-1">Environment Variables</p>
                            <div className="bg-dark-700 rounded-lg p-2 font-mono text-xs">
                              {Object.entries(server.env).map(([k]) => (
                                <div key={k} className="text-gray-300">
                                  <span className="text-claw-400">{k}</span>=****
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                      <div className="flex gap-2 mt-4">
                        <button
                          onClick={() => handleDuplicate(server)}
                          className="btn-secondary text-sm flex items-center gap-1"
                        >
                          <Copy size={14} /> Duplicate
                        </button>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </motion.div>
          );
        })}

        {servers.length === 0 && (
          <div className="bg-dark-800 border border-dark-600 rounded-2xl p-12 text-center">
            <Terminal size={48} className="text-gray-500 mx-auto mb-4" />
            <p className="text-gray-400 mb-4">No MCP servers configured</p>
            <p className="text-gray-500 text-sm mb-4">
              MCP servers extend your AI with tools like file access, web search, and more.
            </p>
            <button onClick={() => { resetForm(); setShowAdd(true); }} className="btn-primary">
              Add Your First Server
            </button>
          </div>
        )}
      </div>

      <AnimatePresence>
        {showAdd && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => { setShowAdd(false); resetForm(); }}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-dark-800 border border-dark-600 rounded-2xl p-6 max-w-lg w-full max-h-[80vh] overflow-y-auto"
              onClick={e => e.stopPropagation()}
            >
              <h3 className="text-lg font-semibold text-white mb-4">
                {editingServer ? `Edit: ${editingServer.name}` : 'Add MCP Server'}
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Server Name</label>
                  <input
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    className="input-base w-full"
                    placeholder="my-server"
                    disabled={!!editingServer}
                  />
                </div>

                <div>
                  <label className="block text-sm text-gray-400 mb-2">Server Type</label>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setForm({ ...form, serverType: 'local', url: '' })}
                      className={clsx(
                        'flex-1 p-3 rounded-lg border transition-all flex items-center justify-center gap-2',
                        form.serverType === 'local'
                          ? 'bg-claw-500/20 border-claw-500/50 text-claw-400'
                          : 'bg-dark-700 border-dark-500 text-gray-400'
                      )}
                    >
                      <Terminal size={16} /> Local (stdio)
                    </button>
                    <button
                      onClick={() => setForm({ ...form, serverType: 'remote', command: '', args: '' })}
                      className={clsx(
                        'flex-1 p-3 rounded-lg border transition-all flex items-center justify-center gap-2',
                        form.serverType === 'remote'
                          ? 'bg-claw-500/20 border-claw-500/50 text-claw-400'
                          : 'bg-dark-700 border-dark-500 text-gray-400'
                      )}
                    >
                      <Globe size={16} /> Remote (SSE)
                    </button>
                  </div>
                </div>

                {form.serverType === 'local' ? (
                  <>
                    <div>
                      <label className="block text-sm text-gray-400 mb-2">Command</label>
                      <input
                        value={form.command}
                        onChange={(e) => setForm({ ...form, command: e.target.value })}
                        className="input-base w-full"
                        placeholder="npx -y @modelcontextprotocol/server-filesystem"
                      />
                    </div>
                    <div>
                      <label className="block text-sm text-gray-400 mb-2">Arguments (space-separated)</label>
                      <input
                        value={form.args}
                        onChange={(e) => setForm({ ...form, args: e.target.value })}
                        className="input-base w-full"
                        placeholder="/path/to/directory"
                      />
                    </div>
                  </>
                ) : (
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Server URL</label>
                    <input
                      value={form.url}
                      onChange={(e) => setForm({ ...form, url: e.target.value })}
                      className="input-base w-full"
                      placeholder="http://localhost:3000/sse"
                    />
                  </div>
                )}

                <div>
                  <label className="block text-sm text-gray-400 mb-2">
                    Environment Variables
                    <span className="text-gray-600 ml-1">(one per line: KEY=value)</span>
                  </label>
                  <textarea
                    value={form.env}
                    onChange={(e) => setForm({ ...form, env: e.target.value })}
                    className="input-base w-full min-h-[80px] font-mono text-sm"
                    placeholder="API_KEY=your-key&#10;NODE_ENV=production"
                  />
                </div>

                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={form.enabled}
                    onChange={(e) => setForm({ ...form, enabled: e.target.checked })}
                    className="w-5 h-5 rounded border-dark-500 bg-dark-700 text-claw-500"
                  />
                  <span className="text-white">Enable this server</span>
                </label>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={handleSave}
                  disabled={saving || !form.name}
                  className="btn-primary flex items-center gap-2"
                >
                  {saving && <Loader2 className="animate-spin" size={16} />}
                  {editingServer ? 'Save Changes' : 'Add Server'}
                </button>
                <button
                  onClick={() => { setShowAdd(false); resetForm(); }}
                  className="btn-secondary"
                >
                  Cancel
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
