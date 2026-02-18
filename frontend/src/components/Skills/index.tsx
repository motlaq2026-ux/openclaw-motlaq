import { useAppStore } from '../../stores/appStore';
import { api } from '../../lib/api';
import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Loader2, ToggleLeft, ToggleRight, Book, Package, Download, 
  Trash2, Plus, Search, Filter, Info, CheckCircle, XCircle,
  Zap, Code, Globe, FileText, Terminal
} from 'lucide-react';
import clsx from 'clsx';

interface SkillFull {
  id: string;
  name: string;
  description?: string;
  icon?: string;
  category: string;
  enabled: boolean;
  installed?: boolean;
  version?: string;
  author?: string;
  tools?: string[];
}

const categoryIcons: Record<string, React.ReactNode> = {
  search: <Globe size={16} />,
  code: <Code size={16} />,
  system: <Terminal size={16} />,
  info: <Info size={16} />,
  multimodal: <FileText size={16} />,
  default: <Zap size={16} />,
};

const categoryColors: Record<string, string> = {
  search: 'bg-blue-500/20 text-blue-400',
  code: 'bg-green-500/20 text-green-400',
  system: 'bg-amber-500/20 text-amber-400',
  info: 'bg-purple-500/20 text-purple-400',
  multimodal: 'bg-pink-500/20 text-pink-400',
  default: 'bg-gray-500/20 text-gray-400',
};

export function Skills() {
  const { skills, loadSkills, loading } = useAppStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [showInstallDialog, setShowInstallDialog] = useState(false);
  const [skillName, setSkillName] = useState('');
  const [installing, setInstalling] = useState(false);
  const [installResult, setInstallResult] = useState<{ success: boolean; message: string } | null>(null);
  const [expandedSkill, setExpandedSkill] = useState<string | null>(null);
  const [showUninstallConfirm, setShowUninstallConfirm] = useState<string | null>(null);

  useEffect(() => {
    loadSkills();
  }, []);

  const handleToggle = async (id: string, enabled: boolean) => {
    await api.toggleSkill(id, !enabled);
    await loadSkills();
  };

  const handleInstall = async () => {
    if (!skillName.trim()) return;
    setInstalling(true);
    setInstallResult(null);
    
    try {
      const result = await fetch('/api/skills/install', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: skillName.trim() }),
      }).then(r => r.json());
      
      setInstallResult({ success: result.success, message: result.message || 'Skill installed!' });
      if (result.success) {
        setSkillName('');
        setShowInstallDialog(false);
        await loadSkills();
      }
    } catch (e) {
      setInstallResult({ success: false, message: String(e) });
    } finally {
      setInstalling(false);
    }
  };

  const handleUninstall = async () => {
    if (!showUninstallConfirm) return;
    setInstalling(true);
    
    try {
      await fetch(`/api/skills/${showUninstallConfirm}`, { method: 'DELETE' });
      setShowUninstallConfirm(null);
      await loadSkills();
    } catch (e) {
      alert('Failed to uninstall: ' + e);
    } finally {
      setInstalling(false);
    }
  };

  const categories = [...new Set(skills.map(s => s.category))];
  
  const filteredSkills = skills.filter(skill => {
    const matchesSearch = !searchQuery || 
      skill.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (skill.description && skill.description.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesCategory = !selectedCategory || skill.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const enabledCount = skills.filter(s => s.enabled).length;

  if (loading) {
    return <div className="flex items-center justify-center h-64"><Loader2 className="w-8 h-8 animate-spin text-claw-500" /></div>;
  }

  return (
    <div className="h-full overflow-y-auto scroll-container p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">Skills</h2>
          <p className="text-gray-400">{enabledCount}/{skills.length} skills enabled</p>
        </div>
        <button onClick={() => setShowInstallDialog(true)} className="btn-primary flex items-center gap-2">
          <Plus size={18} /> Install Skill
        </button>
      </div>

      <div className="flex gap-4 mb-6">
        <div className="relative flex-1">
          <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search skills..."
            className="input-base w-full pl-10"
          />
        </div>
        <select
          value={selectedCategory || ''}
          onChange={(e) => setSelectedCategory(e.target.value || null)}
          className="input-base w-40"
        >
          <option value="">All Categories</option>
          {categories.map(cat => (
            <option key={cat} value={cat}>{cat}</option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <AnimatePresence>
          {filteredSkills.map((skill) => {
            const isExpanded = expandedSkill === skill.id;
            const categoryIcon = categoryIcons[skill.category] || categoryIcons.default;
            const categoryColor = categoryColors[skill.category] || categoryColors.default;
            
            return (
              <motion.div
                key={skill.id}
                layout
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className={clsx(
                  'bg-dark-800 border rounded-2xl overflow-hidden transition-colors',
                  skill.enabled ? 'border-dark-600' : 'border-dark-700 opacity-75'
                )}
              >
                <div className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={clsx('w-10 h-10 rounded-lg flex items-center justify-center text-xl', categoryColor)}>
                        {skill.icon || categoryIcon}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-medium text-white">{skill.name}</h3>
                          {skill.installed && (
                            <span className="text-xs text-green-400 bg-green-500/10 px-1.5 py-0.5 rounded">
                              installed
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-gray-400">{skill.category}</p>
                      </div>
                    </div>
                    <button
                      onClick={() => handleToggle(skill.id, skill.enabled)}
                      className="p-1"
                    >
                      {skill.enabled ? (
                        <ToggleRight className="text-green-500" size={24} />
                      ) : (
                        <ToggleLeft className="text-gray-500" size={24} />
                      )}
                    </button>
                  </div>
                  
                  {skill.description && (
                    <p className="text-sm text-gray-400 mt-3 line-clamp-2">{skill.description}</p>
                  )}

                  <div className="flex items-center justify-between mt-3">
                    <button
                      onClick={() => setExpandedSkill(isExpanded ? null : skill.id)}
                      className="text-xs text-gray-500 hover:text-gray-300 flex items-center gap-1"
                    >
                      {isExpanded ? 'Less' : 'More'}
                    </button>
                    {skill.installed && (
                      <button
                        onClick={() => setShowUninstallConfirm(skill.id)}
                        className="text-xs text-gray-500 hover:text-red-400 flex items-center gap-1"
                      >
                        <Trash2 size={12} /> Remove
                      </button>
                    )}
                  </div>
                </div>

                <AnimatePresence>
                  {isExpanded && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="border-t border-dark-600"
                    >
                      <div className="p-4 space-y-2 text-sm">
                        {skill.version && (
                          <div className="flex justify-between">
                            <span className="text-gray-500">Version</span>
                            <span className="text-gray-300">{skill.version}</span>
                          </div>
                        )}
                        {skill.author && (
                          <div className="flex justify-between">
                            <span className="text-gray-500">Author</span>
                            <span className="text-gray-300">{skill.author}</span>
                          </div>
                        )}
                        {skill.tools && skill.tools.length > 0 && (
                          <div>
                            <p className="text-gray-500 mb-1">Tools</p>
                            <div className="flex flex-wrap gap-1">
                              {skill.tools.map(tool => (
                                <span key={tool} className="text-xs bg-dark-600 px-2 py-0.5 rounded text-gray-300">
                                  {tool}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                        <div className="flex justify-between">
                          <span className="text-gray-500">ID</span>
                          <span className="text-gray-300 font-mono text-xs">{skill.id}</span>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>

      {filteredSkills.length === 0 && (
        <div className="bg-dark-800 border border-dark-600 rounded-2xl p-12 text-center">
          <Book size={48} className="text-gray-500 mx-auto mb-4" />
          <p className="text-gray-400 mb-2">No skills found</p>
          <p className="text-gray-500 text-sm">
            {searchQuery || selectedCategory ? 'Try adjusting your filters' : 'Install skills to extend your AI capabilities'}
          </p>
        </div>
      )}

      <AnimatePresence>
        {showInstallDialog && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => { setShowInstallDialog(false); setInstallResult(null); }}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-dark-800 border border-dark-600 rounded-2xl p-6 max-w-md w-full"
              onClick={e => e.stopPropagation()}
            >
              <h3 className="text-lg font-semibold text-white mb-4">Install Skill</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Skill Package Name</label>
                  <input
                    value={skillName}
                    onChange={(e) => setSkillName(e.target.value)}
                    className="input-base w-full"
                    placeholder="@scope/skill-name or skill-name"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Enter an npm package name or a GitHub URL
                  </p>
                </div>

                {installResult && (
                  <div className={clsx(
                    'p-3 rounded-lg',
                    installResult.success ? 'bg-green-500/10 border border-green-500/30' : 'bg-red-500/10 border border-red-500/30'
                  )}>
                    <div className="flex items-center gap-2">
                      {installResult.success ? (
                        <CheckCircle size={16} className="text-green-400" />
                      ) : (
                        <XCircle size={16} className="text-red-400" />
                      )}
                      <span className={installResult.success ? 'text-green-400' : 'text-red-400'}>
                        {installResult.message}
                      </span>
                    </div>
                  </div>
                )}
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={handleInstall}
                  disabled={installing || !skillName.trim()}
                  className="btn-primary flex items-center gap-2"
                >
                  {installing ? <Loader2 className="animate-spin" size={16} /> : <Download size={16} />}
                  Install
                </button>
                <button
                  onClick={() => { setShowInstallDialog(false); setInstallResult(null); }}
                  className="btn-secondary"
                >
                  Cancel
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showUninstallConfirm && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-dark-800 border border-dark-600 rounded-2xl p-6 max-w-sm w-full"
            >
              <h3 className="text-lg font-semibold text-white mb-2">Uninstall Skill?</h3>
              <p className="text-gray-400 text-sm mb-6">
                Are you sure you want to remove <span className="text-white font-mono">{showUninstallConfirm}</span>?
              </p>
              <div className="flex gap-3 justify-end">
                <button
                  onClick={() => setShowUninstallConfirm(null)}
                  className="btn-secondary"
                  disabled={installing}
                >
                  Cancel
                </button>
                <button
                  onClick={handleUninstall}
                  disabled={installing}
                  className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors text-sm flex items-center gap-2"
                >
                  {installing ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />}
                  Uninstall
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
