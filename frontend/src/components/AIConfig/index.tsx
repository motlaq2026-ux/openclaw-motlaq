import { useAppStore } from '../../stores/appStore';
import { useEffect, useState } from 'react';
import { api, AITestResult } from '../../lib/api';
import { Trash2, Star, Loader2, CheckCircle, Eye, EyeOff, Zap, Clock, TestTube, Plus, Edit } from 'lucide-react';

export function AIConfig() {
  const { aiConfig, loadAIConfig, loading } = useAppStore();
  const [testing, setTesting] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<Record<string, AITestResult>>({});
  const [showAddModel, setShowAddModel] = useState(false);
  const [newModelProvider, setNewModelProvider] = useState('');
  const [newModelId, setNewModelId] = useState('');
  const [newModelName, setNewModelName] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadAIConfig();
  }, []);

  const handleSetPrimary = async (modelId: string) => {
    await api.setPrimaryModel(modelId);
    await loadAIConfig();
  };

  const handleDelete = async (name: string) => {
    if (confirm(`Delete provider ${name}? This will remove all associated models.`)) {
      await api.deleteProvider(name);
      await loadAIConfig();
    }
  };

  const handleTest = async (providerName: string) => {
    const provider = aiConfig?.configured_providers.find(p => p.name === providerName);
    if (!provider) return;
    
    setTesting(providerName);
    try {
      const modelId = provider.models[0]?.full_id?.split('/')[1] || 'test';
      const result = await api.testProvider({
        provider: providerName,
        base_url: provider.base_url,
        model_id: modelId,
      });
      setTestResults(prev => ({ ...prev, [providerName]: result }));
    } catch (e) {
      setTestResults(prev => ({ 
        ...prev, 
        [providerName]: { success: false, provider: providerName, model: 'unknown', error: String(e) } 
      }));
    } finally {
      setTesting(null);
    }
  };

  const handleAddModel = async () => {
    if (!newModelProvider || !newModelId || !newModelName) return;
    setSaving(true);
    try {
      await api.addModel({
        name: newModelName,
        provider: newModelProvider,
        model_id: newModelId,
      });
      await loadAIConfig();
      setShowAddModel(false);
      setNewModelProvider('');
      setNewModelId('');
      setNewModelName('');
    } catch (e) {
      console.error(e);
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
          <h2 className="text-2xl font-bold text-white mb-2">AI Configuration</h2>
          <p className="text-gray-400">Manage your AI providers and models</p>
        </div>
        <button onClick={() => setShowAddModel(true)} className="btn-primary flex items-center gap-2">
          <Plus size={18} /> Add Model
        </button>
      </div>

      {!aiConfig?.configured_providers.length && (
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-2xl p-6 mb-8">
          <p className="text-amber-400">No providers configured. Go to Dashboard to add one.</p>
        </div>
      )}

      <div className="grid gap-6">
        {aiConfig?.configured_providers.map((provider) => {
          const testResult = testResults[provider.name];
          return (
            <div key={provider.name} className="bg-dark-800 border border-dark-600 rounded-2xl p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-claw-500/20 to-purple-500/20 flex items-center justify-center">
                    <Zap className="text-claw-400" size={24} />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white capitalize">{provider.name}</h3>
                    <p className="text-sm text-gray-400 truncate max-w-xs">{provider.base_url}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {provider.has_api_key ? (
                    <div className="flex items-center gap-1 text-green-400 text-sm">
                      <CheckCircle size={14} />
                      <span>Key Set</span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-1 text-red-400 text-sm">
                      <span>No Key</span>
                    </div>
                  )}
                  <button
                    onClick={() => handleTest(provider.name)}
                    disabled={testing === provider.name}
                    className="btn-secondary text-sm flex items-center gap-2"
                  >
                    {testing === provider.name ? (
                      <Loader2 className="animate-spin" size={14} />
                    ) : (
                      <TestTube size={14} />
                    )}
                    Test
                  </button>
                  <button
                    onClick={() => handleDelete(provider.name)}
                    className="btn-secondary text-sm text-red-400"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>

              {testResult && (
                <div className={`mb-4 p-3 rounded-xl ${testResult.success ? 'bg-green-500/10 border border-green-500/30' : 'bg-red-500/10 border border-red-500/30'}`}>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className={`text-sm font-medium ${testResult.success ? 'text-green-400' : 'text-red-400'}`}>
                        {testResult.success ? '✓ Connection successful' : '✗ Connection failed'}
                      </p>
                      {testResult.response && (
                        <p className="text-xs text-gray-400 mt-1">Response: {testResult.response}</p>
                      )}
                      {testResult.error && (
                        <p className="text-xs text-gray-400 mt-1">{testResult.error}</p>
                      )}
                    </div>
                    {testResult.latency_ms && (
                      <div className="text-xs text-gray-400">
                        <Clock size={12} className="inline mr-1" />
                        {testResult.latency_ms}ms
                      </div>
                    )}
                  </div>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {provider.models.map((model) => (
                  <div
                    key={model.full_id}
                    className="bg-dark-700 rounded-xl p-3 flex items-center justify-between group"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="font-medium text-white truncate">{model.name}</p>
                        {model.is_primary && (
                          <span className="px-2 py-0.5 bg-yellow-500/20 text-yellow-400 text-xs rounded-full">
                            Primary
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-gray-500 truncate">{model.full_id}</p>
                    </div>
                    {!model.is_primary && (
                      <button
                        onClick={() => handleSetPrimary(model.full_id)}
                        className="p-1.5 text-gray-600 hover:text-yellow-400 hover:bg-dark-600 rounded-lg opacity-0 group-hover:opacity-100 transition-all"
                        title="Set as primary"
                      >
                        <Star size={16} />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {showAddModel && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-dark-800 border border-dark-600 rounded-2xl p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold text-white mb-4">Add Custom Model</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Provider</label>
                <input
                  value={newModelProvider}
                  onChange={(e) => setNewModelProvider(e.target.value)}
                  className="input-base"
                  placeholder="e.g., groq, openai"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Model ID</label>
                <input
                  value={newModelId}
                  onChange={(e) => setNewModelId(e.target.value)}
                  className="input-base"
                  placeholder="e.g., llama-3.3-70b-versatile"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Display Name</label>
                <input
                  value={newModelName}
                  onChange={(e) => setNewModelName(e.target.value)}
                  className="input-base"
                  placeholder="e.g., Llama 3.3 70B"
                />
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button onClick={handleAddModel} disabled={saving || !newModelProvider || !newModelId || !newModelName} className="btn-primary flex items-center gap-2">
                {saving && <Loader2 className="animate-spin" size={16} />} Add Model
              </button>
              <button onClick={() => setShowAddModel(false)} className="btn-secondary">Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
