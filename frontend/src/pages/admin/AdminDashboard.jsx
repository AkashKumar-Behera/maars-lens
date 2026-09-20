import React, { useState, useEffect } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend 
} from 'recharts';
import { 
  Download, RefreshCw, AlertTriangle, ShieldCheck, FileText, CheckCircle2, TrendingUp 
} from 'lucide-react';
import { getAnalyticsOverviewApi, getAnalyticsTrendsApi, downloadExportCsvBlobApi } from '../../api/admin';

export default function AdminDashboard() {
  const [overview, setOverview] = useState(null);
  const [trends, setTrends] = useState([]);
  const [days, setDays] = useState(14);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState(null);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);
      const [overviewData, trendsData] = await Promise.all([
        getAnalyticsOverviewApi(),
        getAnalyticsTrendsApi(days)
      ]);
      setOverview(overviewData);
      setTrends(trendsData);
    } catch (err) {
      console.error('Failed to load admin analytics:', err);
      setError('Unable to load analytics metrics from backend. Ensure admin privileges.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, [days]);

  const handleExportCsv = async () => {
    try {
      setExporting(true);
      const blob = await downloadExportCsvBlobApi();
      const url = window.URL.createObjectURL(new Blob([blob], { type: 'text/csv' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `MAARS_Compliance_Export_${new Date().toISOString().slice(0, 10)}.csv`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to export CSV:', err);
      alert(err.response?.data?.detail || 'Failed to export compliance audit CSV.');
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <TrendingUp className="h-6 w-6 text-brand-blue" />
            Executive Oversight & Analytics
          </h1>
          <p className="text-sm text-brand-muted">
            National legal metrology audit telemetry, trend indicators, and compliance distribution.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchAnalytics}
            disabled={loading}
            className="px-3 py-2 rounded-lg bg-surface-card border border-surface-border hover:bg-surface-border text-brand-muted hover:text-white transition flex items-center gap-2 text-sm"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={handleExportCsv}
            disabled={exporting}
            className="px-3 py-2 rounded-lg bg-surface-card border border-surface-border hover:bg-surface-border text-brand-muted hover:text-white transition flex items-center gap-2 text-sm disabled:opacity-50"
          >
            <Download className={`h-4 w-4 ${exporting ? 'animate-bounce' : ''}`} />
            {exporting ? 'Exporting...' : 'Export CSV'}
          </button>
          <button
            onClick={async () => {
              try {
                const token = localStorage.getItem('token');
                const response = await fetch('/api/v1/reports/summary/export?format=xlsx', {
                  headers: token ? { Authorization: `Bearer ${token}` } : {},
                });
                if (!response.ok) throw new Error('Failed to download summary report');
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `MAARS_Summary_Report_${new Date().toISOString().slice(0, 10)}.xlsx`;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
              } catch (err) {
                alert(err.message || 'Failed to export summary spreadsheet');
              }
            }}
            className="px-4 py-2 rounded-lg bg-brand-blue hover:bg-blue-600 text-white font-medium shadow-md shadow-brand-blue/20 transition flex items-center gap-2 text-sm"
          >
            <Download className="h-4 w-4" />
            Export Summary (XLSX)
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm flex items-center gap-3">
          <AlertTriangle className="h-5 w-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-surface-card border border-surface-border rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-brand-muted uppercase tracking-wider">Total Audits</span>
            <span className="p-2 rounded-lg bg-brand-blue/10 text-brand-blue"><FileText className="h-5 w-5" /></span>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-white">{overview?.inspections?.total ?? '—'}</span>
            <span className="text-xs text-brand-muted">Recorded Inspections</span>
          </div>
          <div className="mt-3 flex items-center gap-3 text-xs text-brand-muted border-t border-surface-border/50 pt-3">
            <span>Finalized: <strong className="text-white">{overview?.inspections?.finalized ?? 0}</strong></span>
            <span>Pending: <strong className="text-amber-400">{overview?.inspections?.pending_review ?? 0}</strong></span>
          </div>
        </div>

        <div className="bg-surface-card border border-surface-border rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-brand-muted uppercase tracking-wider">Compliance Rate</span>
            <span className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400"><ShieldCheck className="h-5 w-5" /></span>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-emerald-400">
              {overview?.inspections?.total ? (
                `${Math.round(((overview.inspections.compliant || 0) / overview.inspections.total) * 100)}%`
              ) : '—'}
            </span>
            <span className="text-xs text-brand-muted">Automated Passing</span>
          </div>
          <div className="mt-3 flex items-center gap-3 text-xs text-brand-muted border-t border-surface-border/50 pt-3">
            <span className="text-emerald-400">Compliant: <strong>{overview?.inspections?.compliant ?? 0}</strong></span>
            <span className="text-red-400">Non-Compliant: <strong>{overview?.inspections?.non_compliant ?? 0}</strong></span>
          </div>
        </div>

        <div className="bg-surface-card border border-surface-border rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-brand-muted uppercase tracking-wider">Statutory Violations</span>
            <span className="p-2 rounded-lg bg-red-500/10 text-red-400"><AlertTriangle className="h-5 w-5" /></span>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-red-400">{overview?.violations?.total ?? '—'}</span>
            <span className="text-xs text-brand-muted">Total Breaches</span>
          </div>
          <div className="mt-3 flex items-center gap-3 text-xs text-brand-muted border-t border-surface-border/50 pt-3">
            <span className="text-amber-400">Open: <strong>{overview?.violations?.open ?? 0}</strong></span>
            <span className="text-emerald-400">Resolved: <strong>{overview?.violations?.resolved ?? 0}</strong></span>
          </div>
        </div>

        <div className="bg-surface-card border border-surface-border rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-brand-muted uppercase tracking-wider">Rule Engine Inventory</span>
            <span className="p-2 rounded-lg bg-purple-500/10 text-purple-400"><CheckCircle2 className="h-5 w-5" /></span>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-white">{overview?.rules?.total ?? '—'}</span>
            <span className="text-xs text-brand-muted">Registered Rules</span>
          </div>
          <div className="mt-3 flex items-center gap-3 text-xs text-brand-muted border-t border-surface-border/50 pt-3">
            <span className="text-amber-400">Demo Rules: <strong>{overview?.rules?.demo_rules ?? 0}</strong></span>
            <span className="text-purple-400">Statutory: <strong>{overview?.rules?.verified_rules ?? 0}</strong></span>
          </div>
        </div>
      </div>

      {/* Analytics Trend Chart */}
      <div className="bg-surface-card border border-surface-border rounded-xl p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-6 border-b border-surface-border gap-4">
          <div>
            <h2 className="text-base font-semibold text-white">Daily Inspection & Breach Activity</h2>
            <p className="text-xs text-brand-muted mt-1">Aggregated inspection volumes and recorded statutory violations over time</p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-brand-muted">Timeframe:</span>
            {[7, 14, 30].map(d => (
              <button
                key={d}
                onClick={() => setDays(d)}
                className={`px-3 py-1 rounded text-xs font-medium transition ${
                  days === d 
                    ? 'bg-brand-blue text-white' 
                    : 'bg-surface-dark border border-surface-border text-brand-muted hover:text-white'
                }`}
              >
                {d} Days
              </button>
            ))}
          </div>
        </div>

        <div className="mt-6 h-72 w-full">
          {trends.length === 0 ? (
            <div className="h-full flex items-center justify-center text-brand-muted text-sm">
              No trend records available for the selected timeframe.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2D3748" vertical={false} />
                <XAxis dataKey="date" stroke="#718096" fontSize={11} tickLine={false} />
                <YAxis stroke="#718096" fontSize={11} tickLine={false} allowDecimals={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1A202C', borderColor: '#2D3748', borderRadius: '0.5rem', color: '#fff' }}
                  itemStyle={{ fontSize: '12px' }}
                />
                <Legend wrapperStyle={{ paddingTop: '10px', fontSize: '12px' }} />
                <Bar dataKey="inspections" name="Total Audits" fill="#3182CE" radius={[4, 4, 0, 0]} />
                <Bar dataKey="violations" name="Violations" fill="#E53E3E" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  );
}
