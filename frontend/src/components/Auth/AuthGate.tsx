import { useState, useEffect } from 'react';
import { api, APIError } from '../../lib/api';
import { Key, Eye, EyeOff, Check, X, AlertCircle, Loader2 } from 'lucide-react';
import { motion } from 'framer-motion';

interface AuthGateProps {
  children: React.ReactNode;
}

export function AuthGate({ children }: AuthGateProps) {
  const [apiKey, setApiKey] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Try to get system status - requires valid API key
      await api.getSystemStatus();
      setIsAuthenticated(true);
    } catch (err) {
      if (err instanceof APIError && err.status === 401) {
        // Not authenticated - show login
        setIsAuthenticated(false);
      } else {
        // Other error - still show login but with error
        setIsAuthenticated(false);
        if (err instanceof Error) {
          setError(err.message);
        }
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!apiKey.trim()) return;

    setIsLoading(true);
    setError(null);
    setSuccess(false);

    // Temporarily set the key
    api.setApiKey(apiKey.trim());

    try {
      // Try to authenticate
      await api.getSystemStatus();
      setIsAuthenticated(true);
      setSuccess(true);
    } catch (err) {
      // Clear the key on failure
      api.clearApiKey();
      
      if (err instanceof APIError) {
        setError(err.message);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Authentication failed');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    api.clearApiKey();
    setIsAuthenticated(false);
    setApiKey('');
    setSuccess(false);
    setError(null);
  };

  if (isLoading && !isAuthenticated) {
    return (
      <div className="min-h-screen bg-dark-950 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-claw-500 mx-auto mb-4" />
          <p className="text-gray-400">Checking authentication...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-dark-950 flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-md"
        >
          <div className="text-center mb-8">
            <div className="text-6xl mb-4">🦞</div>
            <h1 className="text-3xl font-bold text-white mb-2">OpenClaw Fortress</h1>
            <p className="text-gray-400">Secure AI Assistant Platform</p>
          </div>

          <div className="bg-dark-800 border border-dark-600 rounded-2xl p-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-lg bg-claw-500/20 flex items-center justify-center">
                <Key className="text-claw-400" size={20} />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-white">Authentication Required</h2>
                <p className="text-sm text-gray-400">Enter your API key to continue</p>
              </div>
            </div>

            {error && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg flex items-center gap-2"
              >
                <AlertCircle size={16} className="text-red-400 shrink-0" />
                <p className="text-sm text-red-400">{error}</p>
              </motion.div>
            )}

            {success && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="mb-4 p-3 bg-green-500/10 border border-green-500/30 rounded-lg flex items-center gap-2"
              >
                <Check size={16} className="text-green-400 shrink-0" />
                <p className="text-sm text-green-400">Authentication successful!</p>
              </motion.div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">API Key</label>
                <div className="relative">
                  <input
                    type={showKey ? 'text' : 'password'}
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder="oc_admin_xxxxx"
                    className="input-base w-full pr-10"
                    disabled={isLoading}
                  />
                  <button
                    type="button"
                    onClick={() => setShowKey(!showKey)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white"
                  >
                    {showKey ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Your API key is stored locally in your browser.
                </p>
              </div>

              <button
                type="submit"
                disabled={isLoading || !apiKey.trim()}
                className="btn-primary w-full flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="animate-spin" size={16} />
                    Authenticating...
                  </>
                ) : (
                  <>
                    <Key size={16} />
                    Authenticate
                  </>
                )}
              </button>
            </form>

            <div className="mt-6 pt-4 border-t border-dark-600">
              <p className="text-xs text-gray-500 text-center">
                The API key is generated on first server startup and shown in the console.
                <br />
                Look for: "🔐 Generated admin API key: oc_admin_xxxxx"
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    );
  }

  // User is authenticated - render children with logout option
  return (
    <>
      {children}
      {/* Logout button in corner */}
      <button
        onClick={handleLogout}
        className="fixed bottom-4 right-4 p-2 bg-dark-700 hover:bg-dark-600 rounded-lg text-gray-400 hover:text-white transition-colors z-50"
        title="Logout"
      >
        <X size={16} />
      </button>
    </>
  );
}
