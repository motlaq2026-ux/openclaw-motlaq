import { useAppStore } from '../../stores/appStore';
import { useEffect } from 'react';
import { api } from '../../lib/api';
import { useState } from 'react';
import { Trash2, Star, Loader2, CheckCircle, Eye, EyeOff } from 'lucide-react';

export function AIConfig() {
  const { aiConfig, officialProviders, loadAIConfig, loading } = useAppStore();
  const [testing, setTesting] = useState<string | null>(null);
  const [visibleKeys, setVisibleKeys] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadAIConfig();
  }, []);

  const handleSetPrimary = async (modelId: string) => {
    await api.setPrimaryModel(modelId);
    await loadAIConfig();
  };

  const handleDelete = async (name: string) => {
    if (confirm(`Delete provider ${name}?`)) {
      await api.deleteProvider(name);
      await loadAIConfig();
    }
  };

  const handleTest = async (provider: string, baseUrl: string) => {
    setTesting(provider);
    try {
      const result = await api.testProvider({ provider, base_url: baseUrl, model_id: 'test' });
      alert(result.success ? `✅ ${result.response}` : `❌ ${result.error}`);
    } finally {
      setTesting(null);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><Loader2 className="w-8 h-8 animate-spin text-claw-500" /></div>;
  }

  return (
    <div className="h-full overflow-y-auto scroll-container p-6">
      <h2 className="text-2xl font-bold text-white mb-2">AI Configuration</h2>
      <p className="text-gray-400 mb-8">Manage your AI providers and models</p>

      <div className="grid gap-4">
        {aiConfig?.configured_providers.map((provider) => (
          <div key={provider.name} className="bg-dark-800 border border-dark-600 rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold text-white">{provider.name}</h3>
                <p className="text-sm text-gray-400">{provider.base_url}</p>
              </div>
              <div className="flex gap-2">
                <button onClick={() => handleTest(provider.name, provider.base_url)} disabled={testing === provider.name} className="btn-secondary text-sm">
                  {testing === provider.name ? <Loader2 className="animate-spin" size={14} /> : 'Test'}
                </button>
                <button onClick={() => handleDelete(provider.name)} className="btn-secondary text-sm text-red-400">
                  <Trash2 size={14} />
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {provider.models.map((model) => (
                <div key={model.full_id} className="bg-dark-700 rounded-xl p-3 flex items-center justify-between">
                  <div>
                    <p className="font-medium text-white">{model.name}</p>
                    <p className="text-xs text-gray-400">{model.full_id}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    {model.is_primary && <Star className="text-yellow-500" size={16} fill="currentColor" />}
                    {!model.is_primary && (
                      <button onClick={() => handleSetPrimary(model.full_id)} className="p-1 hover:bg-dark-600 rounded">
                        <Star className="text-gray-500" size={16} />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}

        {(!aiConfig || aiConfig.configured_providers.length === 0) && (
          <div className="bg-dark-800 border border-dark-600 rounded-2xl p-12 text-center">
            <p className="text-gray-400">No providers configured. Go to Dashboard to add one.</p>
          </div>
        )}
      </div>
    </div>
  );
}
