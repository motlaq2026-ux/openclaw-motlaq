import { useState, useEffect } from 'react';
import { api, OfficialProvider } from '../../lib/api';
import {
  CheckCircle2,
  Loader2,
  ArrowRight,
  Zap,
  Bot,
  Key,
  Check,
} from 'lucide-react';
import clsx from 'clsx';

interface SetupStep {
  id: string;
  title: string;
  description: string;
  completed: boolean;
}

interface SetupProps {
  onComplete: () => void;
  embedded?: boolean;
}

export function Setup({ onComplete, embedded = false }: SetupProps) {
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [officialProviders, setOfficialProviders] = useState<OfficialProvider[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<OfficialProvider | null>(null);
  const [apiKey, setApiKey] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadProviders();
  }, []);

  const loadProviders = async () => {
    setLoading(true);
    try {
      const { providers } = await api.getOfficialProviders();
      setOfficialProviders(providers);
    } catch (e) {
      setError('Failed to load providers');
    } finally {
      setLoading(false);
    }
  };

  const steps: SetupStep[] = [
    { id: 'welcome', title: 'Welcome', description: 'Get started with OpenClaw', completed: step > 0 },
    { id: 'provider', title: 'Add Provider', description: 'Configure your first AI provider', completed: step > 1 },
    { id: 'complete', title: 'Complete', description: 'Start using OpenClaw', completed: step > 2 },
  ];

  const handleNext = () => {
    if (step < steps.length - 1) {
      setStep(step + 1);
    }
  };

  const handleProviderSelect = (provider: OfficialProvider) => {
    setSelectedProvider(provider);
  };

  const handleSaveProvider = async () => {
    if (!selectedProvider) return;
    
    setSaving(true);
    setError(null);
    
    try {
      await api.saveProvider({
        provider_name: selectedProvider.id,
        base_url: selectedProvider.default_base_url || '',
        api_key: apiKey || undefined,
        api_type: selectedProvider.api_type,
        models: selectedProvider.suggested_models.map(m => ({
          id: m.id,
          name: m.name,
          context_window: m.context_window,
          max_tokens: m.max_tokens,
        })),
      });
      
      setStep(2);
    } catch (e) {
      setError('Failed to save provider: ' + String(e));
    } finally {
      setSaving(false);
    }
  };

  const handleComplete = () => {
    onComplete();
  };

  const recommendedProviders = officialProviders.filter(p => 
    ['groq', 'gemini', 'cerebras'].includes(p.id)
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-claw-500" />
      </div>
    );
  }

  return (
    <div className={clsx(embedded ? '' : 'min-h-screen bg-dark-950 flex items-center justify-center p-4')}>
      <div className={clsx('w-full', embedded ? 'max-w-3xl' : 'max-w-2xl')}>
        {!embedded && (
          <div className="text-center mb-8">
            <div className="text-6xl mb-4">🦞</div>
            <h1 className="text-3xl font-bold text-white mb-2">Welcome to OpenClaw</h1>
            <p className="text-gray-400">Let's set up your AI assistant</p>
          </div>
        )}

        <div className="flex items-center justify-center gap-4 mb-8">
          {steps.map((s, idx) => (
            <div key={s.id} className="flex items-center">
              <div
                className={clsx(
                  'w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium',
                  s.completed
                    ? 'bg-green-500 text-white'
                    : idx === step
                    ? 'bg-claw-500 text-white'
                    : 'bg-dark-700 text-gray-400'
                )}
              >
                {s.completed ? <Check size={16} /> : idx + 1}
              </div>
              {idx < steps.length - 1 && (
                <div
                  className={clsx(
                    'w-16 h-0.5 mx-2',
                    s.completed ? 'bg-green-500' : 'bg-dark-700'
                  )}
                />
              )}
            </div>
          ))}
        </div>

        <div className="bg-dark-800 border border-dark-600 rounded-2xl p-6">
          {step === 0 && (
            <div className="text-center">
              <Zap size={48} className="text-claw-400 mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-white mb-2">Quick Setup</h2>
              <p className="text-gray-400 mb-6">
                OpenClaw Fortress is a powerful AI assistant platform. 
                Let's configure your first AI provider to get started.
              </p>
              <div className="bg-dark-700 rounded-xl p-4 mb-6">
                <h3 className="font-medium text-white mb-2">Free Providers Available:</h3>
                <div className="flex justify-center gap-4">
                  {['Groq', 'Gemini', 'Cerebras'].map((name) => (
                    <div key={name} className="flex items-center gap-2 text-gray-300">
                      <CheckCircle2 size={16} className="text-green-400" />
                      {name}
                    </div>
                  ))}
                </div>
              </div>
              <button onClick={handleNext} className="btn-primary flex items-center gap-2 mx-auto">
                Get Started <ArrowRight size={16} />
              </button>
            </div>
          )}

          {step === 1 && (
            <div>
              <h2 className="text-xl font-semibold text-white mb-4">Add Your First Provider</h2>
              
              {!selectedProvider ? (
                <>
                  <p className="text-gray-400 mb-4">
                    Choose a provider to get started. Free providers like Groq, Gemini, and Cerebras are recommended.
                  </p>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-6">
                    {officialProviders.slice(0, 6).map((provider) => (
                      <button
                        key={provider.id}
                        onClick={() => handleProviderSelect(provider)}
                        className="bg-dark-700 hover:bg-dark-600 border border-dark-500 rounded-xl p-4 text-left transition-all"
                      >
                        <div className="text-2xl mb-2">{provider.icon}</div>
                        <p className="font-medium text-white">{provider.name}</p>
                        <p className="text-xs text-gray-400">{provider.suggested_models.length} models</p>
                        {['groq', 'gemini', 'cerebras'].includes(provider.id) && (
                          <span className="text-xs text-green-400 mt-1 block">Free tier available</span>
                        )}
                      </button>
                    ))}
                  </div>
                </>
              ) : (
                <div>
                  <button
                    onClick={() => setSelectedProvider(null)}
                    className="text-gray-400 hover:text-white text-sm mb-4"
                  >
                    ← Back to providers
                  </button>
                  
                  <div className="flex items-center gap-4 mb-6">
                    <div className="text-4xl">{selectedProvider.icon}</div>
                    <div>
                      <h3 className="font-medium text-white text-lg">{selectedProvider.name}</h3>
                      <p className="text-gray-400 text-sm">{selectedProvider.suggested_models[0]?.name}</p>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm text-gray-400 mb-2">
                        API Key
                        {!selectedProvider.requires_api_key && (
                          <span className="text-gray-600 ml-2">(Optional for this provider)</span>
                        )}
                      </label>
                      <input
                        type="password"
                        value={apiKey}
                        onChange={(e) => setApiKey(e.target.value)}
                        className="input-base w-full"
                        placeholder={selectedProvider.requires_api_key ? "Enter your API key" : "Optional"}
                      />
                    </div>

                    <div>
                      <label className="block text-sm text-gray-400 mb-2">Models to Add</label>
                      <div className="flex flex-wrap gap-2">
                        {selectedProvider.suggested_models.slice(0, 3).map((model) => (
                          <div
                            key={model.id}
                            className="bg-dark-700 rounded-lg px-3 py-1 text-sm text-gray-300"
                          >
                            {model.name}
                            {model.recommended && (
                              <span className="text-green-400 ml-1">★</span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {error && (
                    <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
                      <p className="text-sm text-red-400">{error}</p>
                    </div>
                  )}

                  <div className="flex gap-3 mt-6">
                    <button
                      onClick={handleSaveProvider}
                      disabled={saving || (selectedProvider.requires_api_key && !apiKey)}
                      className="btn-primary flex items-center gap-2"
                    >
                      {saving ? (
                        <>
                          <Loader2 className="animate-spin" size={16} />
                          Saving...
                        </>
                      ) : (
                        <>
                          <Key size={16} />
                          Save & Continue
                        </>
                      )}
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {step === 2 && (
            <div className="text-center">
              <CheckCircle2 size={64} className="text-green-400 mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-white mb-2">You're All Set!</h2>
              <p className="text-gray-400 mb-6">
                Your AI provider has been configured. You can now start using OpenClaw Fortress.
              </p>
              <button onClick={handleComplete} className="btn-primary flex items-center gap-2 mx-auto">
                <Bot size={18} />
                Start Using OpenClaw
              </button>
            </div>
          )}
        </div>

        {!embedded && (
          <p className="text-center text-gray-500 text-sm mt-6">
            Need help? Check the{' '}
            <a href="https://github.com/motlaq2026-ux/openclaw-motlaq" target="_blank" rel="noopener" className="text-claw-400 hover:underline">
              documentation
            </a>
          </p>
        )}
      </div>
    </div>
  );
}
