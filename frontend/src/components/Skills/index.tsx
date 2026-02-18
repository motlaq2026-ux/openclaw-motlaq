import { useAppStore } from '../../stores/appStore';
import { useEffect } from 'react';
import { Loader2, ToggleLeft, ToggleRight } from 'lucide-react';

export function Skills() {
  const { skills, loadSkills, loading } = useAppStore();

  useEffect(() => {
    loadSkills();
  }, []);

  const handleToggle = async (id: string, enabled: boolean) => {
    await import('../../lib/api').then(({ api }) => api.toggleSkill(id, !enabled));
    await loadSkills();
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><Loader2 className="w-8 h-8 animate-spin text-claw-500" /></div>;
  }

  return (
    <div className="h-full overflow-y-auto scroll-container p-6">
      <h2 className="text-2xl font-bold text-white mb-2">Skills</h2>
      <p className="text-gray-400 mb-8">Manage available skills</p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {skills.map((skill) => (
          <div key={skill.id} className="bg-dark-800 border border-dark-600 rounded-2xl p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center text-xl">
                  {skill.icon || '🔧'}
                </div>
                <div>
                  <h3 className="font-medium text-white">{skill.name}</h3>
                  <p className="text-xs text-gray-400">{skill.category}</p>
                </div>
              </div>
              <button onClick={() => handleToggle(skill.id, skill.enabled)}>
                {skill.enabled ? <ToggleRight className="text-green-500" size={24} /> : <ToggleLeft className="text-gray-500" size={24} />}
              </button>
            </div>
            {skill.description && <p className="text-sm text-gray-400 mt-3">{skill.description}</p>}
          </div>
        ))}
      </div>
    </div>
  );
}
