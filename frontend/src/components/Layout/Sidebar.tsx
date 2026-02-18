import { useAppStore } from '../../stores/appStore';
import { LayoutDashboard, Bot, Plug, Book, MessageCircle, Brain, ScrollText, Settings, Zap } from 'lucide-react';
import clsx from 'clsx';

const navItems = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'ai-config', label: 'AI Config', icon: Bot },
  { id: 'mcp', label: 'MCP Servers', icon: Plug },
  { id: 'skills', label: 'Skills', icon: Book },
  { id: 'channels', label: 'Channels', icon: MessageCircle },
  { id: 'agents', label: 'Agents', icon: Brain },
  { id: 'logs', label: 'Logs', icon: ScrollText },
  { id: 'settings', label: 'Settings', icon: Settings },
] as const;

export function Sidebar() {
  const { currentPage, setCurrentPage, aiConfig } = useAppStore();
  
  return (
    <aside className="w-64 bg-dark-800 border-r border-dark-600 flex flex-col flex-shrink-0">
      <div className="p-4 border-b border-dark-600">
        <h1 className="text-2xl font-bold gradient-text flex items-center gap-2">
          <span className="text-3xl">🦞</span>
          OpenClaw
        </h1>
        <p className="text-xs text-gray-500">Fortress v2.0</p>
      </div>
      
      <nav className="flex-1 p-2 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentPage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setCurrentPage(item.id)}
              className={clsx(
                'w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all',
                isActive
                  ? 'bg-dark-700 text-white border-l-2 border-claw-500'
                  : 'text-gray-400 hover:bg-dark-700 hover:text-white'
              )}
            >
              <Icon size={20} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>
      
      <div className="p-4 border-t border-dark-600">
        <div className="bg-dark-700 rounded-xl p-3">
          <div className="flex items-center gap-2 mb-2">
            <Zap size={16} className="text-claw-500" />
            <span className="text-sm font-medium">Active Model</span>
          </div>
          <p className="text-xs text-gray-400 truncate">
            {aiConfig?.primary_model || 'Not configured'}
          </p>
        </div>
      </div>
    </aside>
  );
}
