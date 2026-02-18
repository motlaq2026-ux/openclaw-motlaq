import { useState, useEffect } from 'react';
import { Check } from 'lucide-react';
import clsx from 'clsx';

export const THEMES = [
  { id: 'claw', name: 'Claw', color: '#f97316', tailwind: 'orange' },
  { id: 'blue', name: 'Ocean', color: '#3b82f6', tailwind: 'blue' },
  { id: 'purple', name: 'Violet', color: '#8b5cf6', tailwind: 'violet' },
  { id: 'green', name: 'Forest', color: '#22c55e', tailwind: 'green' },
  { id: 'pink', name: 'Rose', color: '#ec4899', tailwind: 'pink' },
  { id: 'cyan', name: 'Cyan', color: '#06b6d4', tailwind: 'cyan' },
] as const;

export type ThemeId = typeof THEMES[number]['id'];

const THEME_KEY = 'openclaw-theme';

export function useTheme() {
  const [theme, setTheme] = useState<ThemeId>(() => {
    if (typeof window !== 'undefined') {
      return (localStorage.getItem(THEME_KEY) as ThemeId) || 'claw';
    }
    return 'claw';
  });

  useEffect(() => {
    const root = document.documentElement;
    const themeData = THEMES.find(t => t.id === theme) || THEMES[0];
    
    root.style.setProperty('--color-claw-50', `color-mix(in srgb, ${themeData.color} 5%, white)`);
    root.style.setProperty('--color-claw-100', `color-mix(in srgb, ${themeData.color} 10%, white)`);
    root.style.setProperty('--color-claw-200', `color-mix(in srgb, ${themeData.color} 20%, white)`);
    root.style.setProperty('--color-claw-300', `color-mix(in srgb, ${themeData.color} 30%, white)`);
    root.style.setProperty('--color-claw-400', `color-mix(in srgb, ${themeData.color} 50%, white)`);
    root.style.setProperty('--color-claw-500', themeData.color);
    root.style.setProperty('--color-claw-600', `color-mix(in srgb, ${themeData.color} 20%, black)`);
    root.style.setProperty('--color-claw-700', `color-mix(in srgb, ${themeData.color} 35%, black)`);
    root.style.setProperty('--color-claw-800', `color-mix(in srgb, ${themeData.color} 50%, black)`);
    root.style.setProperty('--color-claw-900', `color-mix(in srgb, ${themeData.color} 65%, black)`);
    root.style.setProperty('--color-claw-950', `color-mix(in srgb, ${themeData.color} 80%, black)`);

    localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  return { theme, setTheme, themes: THEMES };
}

interface ThemePickerProps {
  currentTheme: ThemeId;
  onThemeChange: (theme: ThemeId) => void;
}

export function ThemePicker({ currentTheme, onThemeChange }: ThemePickerProps) {
  return (
    <div className="flex items-center gap-2">
      {THEMES.map((t) => (
        <button
          key={t.id}
          onClick={() => onThemeChange(t.id)}
          className={clsx(
            'w-8 h-8 rounded-lg transition-all flex items-center justify-center',
            currentTheme === t.id
              ? 'ring-2 ring-white ring-offset-2 ring-offset-dark-800'
              : 'hover:scale-110'
          )}
          style={{ backgroundColor: t.color }}
          title={t.name}
        >
          {currentTheme === t.id && <Check size={16} className="text-white" />}
        </button>
      ))}
    </div>
  );
}
