import { useAppStore } from '../../stores/appStore';
import { LayoutDashboard, Bot, Plug, Book, MessageCircle, Brain, ScrollText, Settings, Zap, Keyboard } from 'lucide-react';
import clsx from 'clsx';

const navItems = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, shortcut: '1' },
  { id: 'ai-config', label: 'AI Config', icon: Bot, shortcut: '2' },
  { id: 'mcp', label: 'MCP Servers', icon: Plug, shortcut: '3' },
  { id: 'skills', label: 'Skills', icon: Book, shortcut: '4' },
  { id: 'channels', label: 'Channels', icon: MessageCircle, shortcut: '5' },
  { id: 'agents', label: 'Agents', icon: Brain, shortcut: '6' },
  { id: 'logs', label: 'Logs', icon: ScrollText, shortcut: '7' },
  { id: 'settings', label: 'Settings', icon: Settings, shortcut: '8' },
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
                'w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all group',
                isActive
                  ? 'bg-dark-700 text-white border-l-2 border-claw-500'
                  : 'text-gray-400 hover:bg-dark-700 hover:text-white'
              )}
            >
              <Icon size={20} />
              <span className="flex-1 text-left">{item.label}</span>
              <span className={clsx(
                'text-xs px-1.5 py-0.5 rounded font-mono',
                isActive ? 'bg-dark-600 text-gray-300' : 'bg-dark-700 text-gray-600 group-hover:bg-dark-600'
              )}>
                {item.shortcut}
              </span>
            </button>
          );
        })}
      </nav>
      
      <div className="p-4 border-t border-dark-600 space-y-3">
        <div className="bg-dark-700 rounded-xl p-3">
          <div className="flex items-center gap-2 mb-2">
            <Zap size={16} className="text-claw-500" />
            <span className="text-sm font-medium">Active Model</span>
          </div>
          <p className="text-xs text-gray-400 truncate">
            {aiConfig?.primary_model?.split('/')[1] || 'Not configured'}
          </p>
        </div>
        
        <button
          onClick={() => alert(`Keyboard Shortcuts:

1-8: Navigate pages
R: Refresh data
H: Go to Dashboard
?: Show this help
Esc: Close dialogs`)}
          className="w-full flex items-center gap-2 px-3 py-2 text-gray-500 hover:text-gray-300 hover:bg-dark-700 rounded-lg transition-colors text-sm"
        >
          <Keyboard size={14} />
          <span>Keyboard Shortcuts</span>
        </button>
      </div>
    </aside>
  );
}
