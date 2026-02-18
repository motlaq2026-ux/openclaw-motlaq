import { useAppStore } from '../../stores/appStore';
import { api } from '../../lib/api';
import { useState } from 'react';
import { Download, Upload, Save, Loader2 } from 'lucide-react';

export function Settings() {
  const { loadAll } = useAppStore();
  const [saving, setSaving] = useState(false);
  const [exporting, setExporting] = useState(false);

  const handleExport = async () => {
    setExporting(true);
    try {
      const data = await api.getBackup();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `openclaw-backup-${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setExporting(false);
    }
  };

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const text = await file.text();
    const data = JSON.parse(text);
    setSaving(true);
    try {
      await api.restoreBackup(data);
      await loadAll();
      alert('Backup restored!');
    } catch (err) {
      alert('Failed to restore: ' + err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="h-full overflow-y-auto scroll-container p-6">
      <h2 className="text-2xl font-bold text-white mb-2">Settings</h2>
      <p className="text-gray-400 mb-8">System configuration</p>

      <div className="space-y-6 max-w-2xl">
        <div className="bg-dark-800 border border-dark-600 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Backup & Restore</h3>
          <p className="text-sm text-gray-400 mb-4">Export or import your configuration</p>
          <div className="flex gap-3">
            <button onClick={handleExport} disabled={exporting} className="btn-secondary flex items-center gap-2">
              {exporting ? <Loader2 className="animate-spin" size={16} /> : <Download size={16} />}
              Export Backup
            </button>
            <label className="btn-secondary flex items-center gap-2 cursor-pointer">
              <Upload size={16} />
              Import Backup
              <input type="file" accept=".json" onChange={handleImport} className="hidden" disabled={saving} />
            </label>
          </div>
        </div>

        <div className="bg-dark-800 border border-dark-600 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">About</h3>
          <div className="space-y-2 text-sm">
            <p className="text-gray-400">Version: <span className="text-white">2.0.0</span></p>
            <p className="text-gray-400">Build: <span className="text-white">Nuclear</span></p>
            <p className="text-gray-400">License: <span className="text-white">MIT</span></p>
          </div>
        </div>
      </div>
    </div>
  );
}
