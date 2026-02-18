import { useAppStore } from '../../stores/appStore';
import { api } from '../../lib/api';
import { useEffect, useState } from 'react';
import { 
  Loader2, Plus, Trash2, Brain, GitMerge, TestTube,
  Bot, Zap, CheckCircle, XCircle, Save
} from 'lucide-react';
import clsx from 'clsx';

interface SubagentDefaults {
  max_spawn_depth: number;
  max_children_per_agent: number;
  max_concurrent: number;
}

interface AgentBinding {
  agent_id: string;
  match_rule: {
    channel: string | null;
    account_id: string | null;
    peer: any | null;
  };
}

interface RoutingTestResult {
  matched: boolean;
  agent_id: string;
  agent_dir?: string;
  model?: string;
  message?: string;
}

export function Agents() {
  const { agents, loadAgents, loading } = useAppStore();
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ name: '', description: '', system_prompt: '', model_id: '' });
  const [saving, setSaving] = useState(false);
  
  const [activeTab, setActiveTab] = useState<'agents' | 'bindings' | 'defaults'>('agents');
  const [bindings, setBindings] = useState<AgentBinding[]>([]);
  const [showBindingDialog, setShowBindingDialog] = useState(false);
  const [bindingForm, setBindingForm] = useState<AgentBinding>({
    agent_id: '',
    match_rule: { channel: null, account_id: null, peer: null }
  });
  
  const [defaults, setDefaults] = useState<SubagentDefaults>({
    max_spawn_depth: 3,
    max_children_per_agent: 5,
    max_concurrent: 3,
  });
  const [savingDefaults, setSavingDefaults] = useState(false);
  
  const [testChannel, setTestChannel] = useState('telegram');
  const [testAccountId, setTestAccountId] = useState('');
  const [testPeer, setTestPeer] = useState('');
  const [testResult, setTestResult] = useState<RoutingTestResult | null>(null);
  const [testing, setTesting] = useState(false);

  useEffect(() => {
    loadAgents();
    loadBindings();
    loadDefaults();
  }, []);

  const loadBindings = async () => {
    try {
      const result = await api.getAgents();
      setBindings(result.agents?.flatMap((a: any) => 
        (a.bindings || []).map((b: any) => ({
          agent_id: a.id,
          match_rule: b.match_rule || { channel: null, account_id: null, peer: null }
        }))
      ) || []);
    } catch {
      // Silent fail
    }
  };

  const loadDefaults = async () => {
    try {
      const config = await api.getConfig();
      if (config.subagent_defaults) {
        setDefaults(config.subagent_defaults as SubagentDefaults);
      }
    } catch {
      // Silent fail
    }
  };

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

  const handleAddBinding = async () => {
    if (!bindingForm.agent_id) return;
    setSaving(true);
    try {
      await api.updateAgent(bindingForm.agent_id, { bindings: [bindingForm.match_rule] });
      await loadBindings();
      setShowBindingDialog(false);
      setBindingForm({ agent_id: '', match_rule: { channel: null, account_id: null, peer: null } });
    } finally {
      setSaving(false);
    }
  };

  const handleSaveDefaults = async () => {
    setSavingDefaults(true);
    try {
      await api.saveConfig({ subagent_defaults: defaults });
      alert('Defaults saved!');
    } catch (e) {
      alert('Failed to save: ' + e);
    } finally {
      setSavingDefaults(false);
    }
  };

  const handleRoutingTest = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const result = await fetch('/api/agents/routing/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          channel: testChannel,
          account_id: testAccountId || null,
          peer: testPeer || null,
        }),
      }).then(r => r.json());
      setTestResult(result);
    } catch (e) {
      setTestResult({ matched: false, agent_id: '', message: String(e) });
    } finally {
      setTesting(false);
    }
  };

  const tabs = [
    { id: 'agents', label: 'Agents', icon: Bot },
    { id: 'bindings', label: 'Bindings', icon: GitMerge },
    { id: 'defaults', label: 'Defaults', icon: Zap },
  ] as const;

  if (loading) {
    return <div className="flex items-center justify-center h-64"><Loader2 className="w-8 h-8 animate-spin text-claw-500" /></div>;
  }

  return (
    <div className="h-full overflow-y-auto scroll-container p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">Agents</h2>
          <p className="text-gray-400">Manage AI agents with different personalities</p>
        </div>
      </div>

      <div className="flex gap-6 max-w-6xl">
        <div className="w-48 shrink-0 space-y-1">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={clsx(
                  'w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all text-left',
                  activeTab === tab.id
                    ? 'bg-claw-500/20 text-claw-400 border border-claw-500/30'
                    : 'text-gray-400 hover:text-white hover:bg-dark-700'
                )}
              >
                <Icon size={18} />
                <span className="font-medium">{tab.label}</span>
              </button>
            );
          })}
        </div>

        <div className="flex-1 min-w-0 space-y-6">
          {activeTab === 'agents' && (
            <>
              <div className="flex justify-end">
                <button onClick={() => setShowAdd(true)} className="btn-primary flex items-center gap-2">
                  <Plus size={18} /> Add Agent
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                      <div className="flex items-center gap-2">
                        {agent.enabled ? (
                          <CheckCircle className="text-green-500" size={16} />
                        ) : (
                          <XCircle className="text-gray-500" size={16} />
                        )}
                        <button onClick={() => handleDelete(agent.id)} className="text-gray-400 hover:text-red-400">
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                    {agent.description && <p className="text-sm text-gray-400">{agent.description}</p>}
                    {agent.system_prompt && (
                      <p className="text-xs text-gray-500 mt-2 line-clamp-2">{agent.system_prompt}</p>
                    )}
                  </div>
                ))}
                
                {agents.length === 0 && (
                  <div className="col-span-2 bg-dark-800 border border-dark-600 rounded-2xl p-12 text-center">
                    <Bot size={48} className="text-gray-500 mx-auto mb-4" />
                    <p className="text-gray-400 mb-4">No agents configured</p>
                    <button onClick={() => setShowAdd(true)} className="btn-primary">
                      Add Your First Agent
                    </button>
                  </div>
                )}
              </div>
            </>
          )}

          {activeTab === 'bindings' && (
            <>
              <div className="flex justify-between items-center">
                <p className="text-gray-400 text-sm">Route messages to specific agents based on channel, account, or peer</p>
                <button onClick={() => setShowBindingDialog(true)} className="btn-primary flex items-center gap-2">
                  <Plus size={18} /> Add Binding
                </button>
              </div>

              <div className="bg-dark-800 border border-dark-600 rounded-2xl p-6">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <TestTube size={18} className="text-purple-400" />
                  Routing Test
                </h3>
                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Channel</label>
                    <select
                      value={testChannel}
                      onChange={(e) => setTestChannel(e.target.value)}
                      className="input-base"
                    >
                      <option value="telegram">Telegram</option>
                      <option value="discord">Discord</option>
                      <option value="slack">Slack</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Account ID</label>
                    <input
                      value={testAccountId}
                      onChange={(e) => setTestAccountId(e.target.value)}
                      className="input-base"
                      placeholder="optional"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Peer</label>
                    <input
                      value={testPeer}
                      onChange={(e) => setTestPeer(e.target.value)}
                      className="input-base"
                      placeholder="optional"
                    />
                  </div>
                </div>
                <button
                  onClick={handleRoutingTest}
                  disabled={testing}
                  className="btn-secondary flex items-center gap-2"
                >
                  {testing ? <Loader2 className="animate-spin" size={16} /> : <TestTube size={16} />}
                  Test Routing
                </button>

                {testResult && (
                  <div className={`mt-4 p-4 rounded-xl ${testResult.matched ? 'bg-green-500/10 border border-green-500/30' : 'bg-amber-500/10 border border-amber-500/30'}`}>
                    <p className={`text-sm font-medium ${testResult.matched ? 'text-green-400' : 'text-amber-400'}`}>
                      {testResult.matched ? `Matched: ${testResult.agent_id}` : 'No match found'}
                    </p>
                    {testResult.model && <p className="text-xs text-gray-400 mt-1">Model: {testResult.model}</p>}
                    {testResult.message && <p className="text-xs text-gray-400 mt-1">{testResult.message}</p>}
                  </div>
                )}
              </div>

              <div className="space-y-3">
                {bindings.map((binding, idx) => (
                  <div key={idx} className="bg-dark-800 border border-dark-600 rounded-xl p-4 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-8 h-8 rounded-lg bg-purple-500/20 flex items-center justify-center">
                        <GitMerge size={16} className="text-purple-400" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-white">{binding.agent_id}</p>
                        <p className="text-xs text-gray-400">
                          {binding.match_rule.channel || '*'} / {binding.match_rule.account_id || '*'} / {binding.match_rule.peer || '*'}
                        </p>
                      </div>
                    </div>
                    <button className="text-gray-400 hover:text-red-400">
                      <Trash2 size={16} />
                    </button>
                  </div>
                ))}
                
                {bindings.length === 0 && (
                  <div className="bg-dark-800 border border-dark-600 rounded-2xl p-8 text-center">
                    <p className="text-gray-400">No bindings configured. All messages go to the default agent.</p>
                  </div>
                )}
              </div>
            </>
          )}

          {activeTab === 'defaults' && (
            <div className="bg-dark-800 border border-dark-600 rounded-2xl p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-lg font-semibold text-white">Subagent Defaults</h3>
                  <p className="text-sm text-gray-400">Default limits for spawned subagents</p>
                </div>
                <button onClick={handleSaveDefaults} disabled={savingDefaults} className="btn-primary flex items-center gap-2">
                  {savingDefaults ? <Loader2 className="animate-spin" size={16} /> : <Save size={16} />}
                  Save
                </button>
              </div>

              <div className="space-y-6">
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Max Spawn Depth</label>
                  <input
                    type="number"
                    value={defaults.max_spawn_depth}
                    onChange={(e) => setDefaults({ ...defaults, max_spawn_depth: Number(e.target.value) })}
                    className="input-base"
                  />
                  <p className="text-xs text-gray-500 mt-1">Maximum depth of agent spawning chain</p>
                </div>

                <div>
                  <label className="block text-sm text-gray-400 mb-2">Max Children Per Agent</label>
                  <input
                    type="number"
                    value={defaults.max_children_per_agent}
                    onChange={(e) => setDefaults({ ...defaults, max_children_per_agent: Number(e.target.value) })}
                    className="input-base"
                  />
                  <p className="text-xs text-gray-500 mt-1">Maximum subagents a single agent can spawn</p>
                </div>

                <div>
                  <label className="block text-sm text-gray-400 mb-2">Max Concurrent Agents</label>
                  <input
                    type="number"
                    value={defaults.max_concurrent}
                    onChange={(e) => setDefaults({ ...defaults, max_concurrent: Number(e.target.value) })}
                    className="input-base"
                  />
                  <p className="text-xs text-gray-500 mt-1">Maximum agents running simultaneously</p>
                </div>
              </div>
            </div>
          )}
        </div>
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

      {showBindingDialog && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-dark-800 border border-dark-600 rounded-2xl p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold text-white mb-4">Add Binding</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">Agent</label>
                <select
                  value={bindingForm.agent_id}
                  onChange={(e) => setBindingForm({ ...bindingForm, agent_id: e.target.value })}
                  className="input-base"
                >
                  <option value="">Select agent</option>
                  {agents.map((a) => (
                    <option key={a.id} value={a.id}>{a.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">Channel</label>
                <select
                  value={bindingForm.match_rule.channel || ''}
                  onChange={(e) => setBindingForm({ 
                    ...bindingForm, 
                    match_rule: { ...bindingForm.match_rule, channel: e.target.value || null }
                  })}
                  className="input-base"
                >
                  <option value="">Any</option>
                  <option value="telegram">Telegram</option>
                  <option value="discord">Discord</option>
                  <option value="slack">Slack</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">Account ID</label>
                <input
                  value={bindingForm.match_rule.account_id || ''}
                  onChange={(e) => setBindingForm({ 
                    ...bindingForm, 
                    match_rule: { ...bindingForm.match_rule, account_id: e.target.value || null }
                  })}
                  className="input-base"
                  placeholder="optional"
                />
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button onClick={handleAddBinding} disabled={saving || !bindingForm.agent_id} className="btn-primary flex items-center gap-2">
                {saving && <Loader2 className="animate-spin" size={16} />} Add
              </button>
              <button onClick={() => setShowBindingDialog(false)} className="btn-secondary">Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
