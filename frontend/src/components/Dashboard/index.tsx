import { useEffect } from 'react';
import { useAppStore } from '../../stores/appStore';
import { api, OfficialProvider } from '../../lib/api';
import { Activity, Bot, Zap, Clock, CheckCircle, XCircle, Loader2, Plus } from 'lucide-react';
import { useState } from 'react';

export function Dashboard() {
  const { aiConfig, officialProviders, loadAIConfig, loading } = useAppStore();
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState<OfficialProvider | null>(null);
  const [apiKey, setApiKey] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadAIConfig();
  }, []);

  const handleAddProvider = async () => {
    if (!selectedProvider || !apiKey) return;
    setSaving(true);
    try {
      await api.saveProvider({
        provider_name: selectedProvider.id,
        base_url: selectedProvider.default_base_url || '',
        api_key: apiKey,
        api_type: selectedProvider.api_type,
        models: selectedProvider.suggested_models.map(m => ({
          id: m.id,
          name: m.name,
          context_window: m.context_window,
          max_tokens: m.max_tokens,
        })),
      });
      await loadAIConfig();
      setShowAddDialog(false);
      setSelectedProvider(null);
      setApiKey('');
    } catch (e) {
      console.error(e);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-claw-500" />
      </div>
    );
  }

  const hasConfig = aiConfig && aiConfig.configured_providers.length > 0;

  return (
    <div className="h-full overflow-y-auto scroll-container p-6">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">Dashboard</h2>
          <p className="text-gray-400">Welcome to OpenClaw Fortress</p>
        </div>
        <button
          onClick={() => setShowAddDialog(true)}
          className="btn-primary flex items-center gap-2"
        >
          <Plus size={18} />
          Add Provider
        </button>
      </div>

      {!hasConfig && (
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-2xl p-6 mb-8">
          <h3 className="text-lg font-semibold text-amber-400 mb-2">Setup Required</h3>
          <p className="text-gray-400 mb-4">
            No AI providers configured. Add a provider to get started.
          </p>
          <button
            onClick={() => setShowAddDialog(true)}
            className="btn-primary"
          >
            Add Your First Provider
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="bg-dark-800 border border-dark-600 rounded-xl p-4">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-lg bg-claw-500/20 flex items-center justify-center">
              <Bot className="text-claw-500" size={20} />
            </div>
            <span className="text-gray-400">Providers</span>
          </div>
          <p className="text-3xl font-bold text-white">
            {aiConfig?.configured_providers.length || 0}
          </p>
        </div>

        <div className="bg-dark-800 border border-dark-600 rounded-xl p-4">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
              <Activity className="text-purple-500" size={20} />
            </div>
            <span className="text-gray-400">Models</span>
          </div>
          <p className="text-3xl font-bold text-white">
            {aiConfig?.available_models.length || 0}
          </p>
        </div>

        <div className="bg-dark-800 border border-dark-600 rounded-xl p-4">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-lg bg-green-500/20 flex items-center justify-center">
              <Zap className="text-green-500" size={20} />
            </div>
            <span className="text-gray-400">Primary</span>
          </div>
          <p className="text-sm font-medium text-white truncate">
            {aiConfig?.primary_model?.split('/')[1] || 'Not set'}
          </p>
        </div>

        <div className="bg-dark-800 border border-dark-600 rounded-xl p-4">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
              <Clock className="text-blue-500" size={20} />
            </div>
            <span className="text-gray-400">Status</span>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle className="text-green-500" size={16} />
            <span className="text-green-400 text-sm">Running</span>
          </div>
        </div>
      </div>

      {hasConfig && (
        <div className="bg-dark-800 border border-dark-600 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Configured Providers</h3>
          <div className="space-y-3">
            {aiConfig?.configured_providers.map((provider) => (
              <div key={provider.name} className="bg-dark-700 rounded-xl p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium text-white">{provider.name}</h4>
                    <p className="text-sm text-gray-400">{provider.models.length} models</p>
                  </div>
                  <div className="flex items-center gap-2">
                    {provider.has_api_key ? (
                      <CheckCircle className="text-green-500" size={16} />
                    ) : (
                      <XCircle className="text-red-500" size={16} />
                    )}
                    <span className="text-xs text-gray-400">
                      {provider.has_api_key ? 'Key set' : 'No key'}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {showAddDialog && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-dark-800 border border-dark-600 rounded-2xl p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <h3 className="text-lg font-semibold text-white mb-4">Add AI Provider</h3>
            
            {!selectedProvider ? (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {officialProviders.map((provider) => (
                  <button
                    key={provider.id}
                    onClick={() => setSelectedProvider(provider)}
                    className="bg-dark-700 hover:bg-dark-600 border border-dark-500 rounded-xl p-4 text-left transition-colors"
                  >
                    <div className="text-2xl mb-2">{provider.icon}</div>
                    <p className="font-medium text-white">{provider.name}</p>
                    <p className="text-xs text-gray-400 mt-1">
                      {provider.suggested_models.length} models
                    </p>
                  </button>
                ))}
              </div>
            ) : (
              <div>
                <div className="flex items-center gap-3 mb-4">
                  <div className="text-3xl">{selectedProvider.icon}</div>
                  <div>
                    <h4 className="font-medium text-white">{selectedProvider.name}</h4>
                    <p className="text-sm text-gray-400">{selectedProvider.suggested_models[0]?.name}</p>
                  </div>
                </div>
                
                <label className="block text-sm text-gray-400 mb-2">API Key</label>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder={selectedProvider.requires_api_key ? "Enter your API key" : "Optional"}
                  className="input-base mb-4"
                />
                
                <div className="flex gap-3">
                  <button
                    onClick={handleAddProvider}
                    disabled={saving || (selectedProvider.requires_api_key && !apiKey)}
                    className="btn-primary flex items-center gap-2"
                  >
                    {saving && <Loader2 className="animate-spin" size={16} />}
                    Add Provider
                  </button>
                  <button
                    onClick={() => { setSelectedProvider(null); setApiKey(''); }}
                    className="btn-secondary"
                  >
                    Back
                  </button>
                  <button
                    onClick={() => { setShowAddDialog(false); setSelectedProvider(null); setApiKey(''); }}
                    className="btn-secondary"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
