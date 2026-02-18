import { useAppStore } from '../../stores/appStore';
import { useEffect, useState } from 'react';
import { api, AITestResult, OfficialProvider, ConfiguredProvider } from '../../lib/api';
import { Trash2, Star, Loader2, CheckCircle, Eye, EyeOff, Zap, Clock, TestTube, Plus, Edit, X } from 'lucide-react';
import clsx from 'clsx';

interface ProviderDialogProps {
  officialProviders: OfficialProvider[];
  onClose: () => void;
  onSave: () => void;
  editingProvider?: ConfiguredProvider | null;
}

function ProviderDialog({ officialProviders, onClose, onSave, editingProvider }: ProviderDialogProps) {
  const isEditing = !!editingProvider;
  const [step, setStep] = useState<'select' | 'configure'>(isEditing ? 'configure' : 'select');
  const [selectedOfficial, setSelectedOfficial] = useState<OfficialProvider | null>(() => {
    if (editingProvider) {
      return officialProviders.find(p => 
        editingProvider.name.includes(p.id) || p.id === editingProvider.name
      ) || null;
    }
    return null;
  });
  
  const [providerName, setProviderName] = useState(editingProvider?.name || '');
  const [baseUrl, setBaseUrl] = useState(editingProvider?.base_url || '');
  const [apiKey, setApiKey] = useState('');
  const [apiType, setApiType] = useState('openai-completions');
  const [showApiKey, setShowApiKey] = useState(false);
  const [selectedModels, setSelectedModels] = useState<string[]>(() => {
    if (editingProvider) {
      return editingProvider.models.map(m => m.id);
    }
    return [];
  });
  const [customModelId, setCustomModelId] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSelectOfficial = (provider: OfficialProvider) => {
    setSelectedOfficial(provider);
    setProviderName(provider.id);
    setBaseUrl(provider.default_base_url || '');
    setApiType(provider.api_type);
    const recommended = provider.suggested_models.filter(m => m.recommended).map(m => m.id);
    setSelectedModels(recommended.length > 0 ? recommended : [provider.suggested_models[0]?.id].filter(Boolean));
    setError(null);
    setStep('configure');
  };

  const handleSelectCustom = () => {
    setSelectedOfficial(null);
    setProviderName('');
    setBaseUrl('');
    setApiType('openai-completions');
    setSelectedModels([]);
    setError(null);
    setStep('configure');
  };

  const toggleModel = (modelId: string) => {
    setError(null);
    setSelectedModels(prev => 
      prev.includes(modelId) 
        ? prev.filter(id => id !== modelId)
        : [...prev, modelId]
    );
  };

  const addCustomModel = () => {
    if (customModelId && !selectedModels.includes(customModelId)) {
      setError(null);
      setSelectedModels(prev => [...prev, customModelId]);
      setCustomModelId('');
    }
  };

  const handleSave = async () => {
    setError(null);
    
    if (!providerName || !baseUrl || selectedModels.length === 0) {
      setError('Please fill in all fields and select at least one model');
      return;
    }
    
    setSaving(true);
    try {
      const models = selectedModels.map(modelId => {
        const suggested = selectedOfficial?.suggested_models.find(m => m.id === modelId);
        const existingModel = editingProvider?.models.find(m => m.id === modelId);
        return {
          id: modelId,
          name: suggested?.name || existingModel?.name || modelId,
          context_window: suggested?.context_window || existingModel?.context_window || 200000,
          max_tokens: suggested?.max_tokens || existingModel?.max_tokens || 8192,
        };
      });

      await api.saveProvider({
        provider_name: providerName,
        base_url: baseUrl,
        api_key: apiKey || undefined,
        api_type: apiType,
        models,
      });

      onSave();
      onClose();
    } catch (e) {
      setError('Failed to save: ' + String(e));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div 
        className="bg-dark-800 rounded-2xl border border-dark-600 w-full max-w-2xl max-h-[85vh] overflow-hidden"
        onClick={e => e.stopPropagation()}
      >
        <div className="px-6 py-4 border-b border-dark-600 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            {isEditing ? <Edit size={20} className="text-claw-400" /> : <Plus size={20} className="text-claw-400" />}
            {isEditing ? `Edit: ${editingProvider?.name}` : 'Add AI Provider'}
          </h2>
          <button onClick={onClose} className="text-gray-500 hover:text-white">
            <X size={20} />
          </button>
        </div>

        <div className="p-6 overflow-y-auto max-h-[calc(85vh-140px)]">
          {step === 'select' ? (
            <div className="space-y-4">
              <div className="space-y-3">
                <h3 className="text-sm font-medium text-gray-400">Official Providers</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {officialProviders.map(provider => (
                    <button
                      key={provider.id}
                      onClick={() => handleSelectOfficial(provider)}
                      className="flex items-center gap-3 p-4 rounded-xl bg-dark-700 border border-dark-500 hover:border-claw-500/50 hover:bg-dark-600 transition-all text-left group"
                    >
                      <span className="text-2xl">{provider.icon}</span>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-white truncate">{provider.name}</p>
                        <p className="text-xs text-gray-500">{provider.suggested_models.length} models</p>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
              <div className="pt-4 border-t border-dark-600">
                <button
                  onClick={handleSelectCustom}
                  className="w-full flex items-center justify-center gap-2 p-4 rounded-xl border-2 border-dashed border-dark-500 hover:border-claw-500/50 text-gray-400 hover:text-white transition-all"
                >
                  <Edit size={18} />
                  <span>Custom Provider</span>
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-5">
              <div>
                <label className="block text-sm text-gray-400 mb-2">Provider Name</label>
                <input
                  type="text"
                  value={providerName}
                  onChange={e => { setError(null); setProviderName(e.target.value); }}
                  placeholder="e.g., groq, anthropic"
                  className="input-base"
                  disabled={isEditing}
                />
                {isEditing && (
                  <p className="text-xs text-gray-500 mt-1">Provider name cannot be changed</p>
                )}
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-2">API URL</label>
                <input
                  type="text"
                  value={baseUrl}
                  onChange={e => { setError(null); setBaseUrl(e.target.value); }}
                  placeholder="https://api.example.com/v1"
                  className="input-base"
                />
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-2">
                  API Key
                  {!selectedOfficial?.requires_api_key && <span className="text-gray-600 text-xs ml-2">(Optional)</span>}
                </label>
                {isEditing && editingProvider?.has_api_key && (
                  <div className="mb-2 flex items-center gap-2 text-sm">
                    <span className="text-gray-500">Current:</span>
                    <code className="px-2 py-0.5 bg-dark-600 rounded text-gray-400">
                      {editingProvider.api_key_masked}
                    </code>
                    <CheckCircle size={14} className="text-green-400" />
                  </div>
                )}
                <div className="relative">
                  <input
                    type={showApiKey ? 'text' : 'password'}
                    value={apiKey}
                    onChange={e => setApiKey(e.target.value)}
                    placeholder={isEditing && editingProvider?.has_api_key 
                      ? "Leave empty to keep existing key" 
                      : "sk-..."}
                    className="input-base pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowApiKey(!showApiKey)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white"
                  >
                    {showApiKey ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
                {isEditing && editingProvider?.has_api_key && (
                  <p className="text-xs text-gray-500 mt-1">Leave empty to keep existing key</p>
                )}
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-2">API Type</label>
                <select
                  value={apiType}
                  onChange={e => setApiType(e.target.value)}
                  className="input-base"
                >
                  <option value="openai-completions">OpenAI Compatible</option>
                  <option value="anthropic-messages">Anthropic Compatible</option>
                </select>
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-2">
                  Models ({selectedModels.length} selected)
                </label>
                {selectedOfficial && (
                  <div className="grid grid-cols-2 gap-2 mb-3">
                    {selectedOfficial.suggested_models.map(model => (
                      <button
                        key={model.id}
                        onClick={() => toggleModel(model.id)}
                        className={clsx(
                          'p-3 rounded-lg text-left transition-all border',
                          selectedModels.includes(model.id)
                            ? 'bg-claw-500/20 border-claw-500/50 text-white'
                            : 'bg-dark-700 border-dark-500 text-gray-400 hover:border-dark-400'
                        )}
                      >
                        <p className="font-medium text-sm">{model.name}</p>
                        <p className="text-xs text-gray-500 truncate">{model.id}</p>
                      </button>
                    ))}
                  </div>
                )}
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={customModelId}
                    onChange={e => setCustomModelId(e.target.value)}
                    placeholder="Add custom model ID"
                    className="input-base flex-1"
                    onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addCustomModel())}
                  />
                  <button onClick={addCustomModel} className="btn-secondary">Add</button>
                </div>
                {selectedModels.filter(id => !selectedOfficial?.suggested_models.find(m => m.id === id)).length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {selectedModels
                      .filter(id => !selectedOfficial?.suggested_models.find(m => m.id === id))
                      .map(id => (
                        <span 
                          key={id} 
                          className="bg-dark-600 px-2 py-1 rounded text-xs text-gray-300 flex items-center gap-1"
                        >
                          {id}
                          <button onClick={() => toggleModel(id)} className="text-gray-500 hover:text-red-400">×</button>
                        </span>
                      ))}
                  </div>
                )}
              </div>

              {error && (
                <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
                  <p className="text-sm text-red-400">{error}</p>
                </div>
              )}

              <div className="flex gap-3 pt-2">
                {!isEditing && (
                  <button onClick={() => setStep('select')} className="btn-secondary">
                    Back
                  </button>
                )}
                <button
                  onClick={handleSave}
                  disabled={saving || !providerName || !baseUrl || selectedModels.length === 0}
                  className="btn-primary flex items-center gap-2"
                >
                  {saving && <Loader2 className="animate-spin" size={16} />}
                  {isEditing ? 'Save Changes' : 'Add Provider'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export function AIConfig() {
  const { aiConfig, officialProviders, loadAIConfig, loading } = useAppStore();
  const [testing, setTesting] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<Record<string, AITestResult>>({});
  const [showDialog, setShowDialog] = useState(false);
  const [editingProvider, setEditingProvider] = useState<ConfiguredProvider | null>(null);

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

  const handleEdit = (provider: ConfiguredProvider) => {
    setEditingProvider(provider);
    setShowDialog(true);
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
        <button onClick={() => { setEditingProvider(null); setShowDialog(true); }} className="btn-primary flex items-center gap-2">
          <Plus size={18} /> Add Provider
        </button>
      </div>

      {!aiConfig?.configured_providers.length && (
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-2xl p-6 mb-8">
          <p className="text-amber-400">No providers configured. Click "Add Provider" to get started.</p>
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
                    onClick={() => handleEdit(provider)}
                    className="btn-secondary text-sm flex items-center gap-1"
                  >
                    <Edit size={14} />
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
                        {testResult.success ? 'Connection successful' : 'Connection failed'}
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

      {showDialog && (
        <ProviderDialog
          officialProviders={officialProviders}
          onClose={() => { setShowDialog(false); setEditingProvider(null); }}
          onSave={() => loadAIConfig()}
          editingProvider={editingProvider}
        />
      )}
    </div>
  );
}
