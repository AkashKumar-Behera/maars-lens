import React, { useState, useEffect, useMemo } from 'react';
import { 
  BarChart, Bar, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend 
} from 'recharts';
import { 
  Download, RefreshCw, AlertTriangle, ShieldCheck, FileText, CheckCircle2, TrendingUp,
  BarChart3, Activity, Calendar, ShieldAlert, Sparkles, Database, Check, Layers, MapPin, Gavel, X
} from 'lucide-react';
import { getAnalyticsOverviewApi, getAnalyticsTrendsApi, downloadExportCsvBlobApi } from '../../api/admin';
import { getAdminGeoIntelligenceApi, executeAdminLegalActionApi } from '../../api/inquiries';
import IndiaMapView from '../../components/IndiaMapView';

// Custom sleek Glassmorphic Tooltip for Recharts
const CustomChartTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const formattedDate = (() => {
      try {
        const d = new Date(label);
        return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
      } catch {
        return label;
      }
    })();

    const audits = payload.find(p => p.dataKey === 'inspections')?.value ?? 0;
    const violations = payload.find(p => p.dataKey === 'violations')?.value ?? 0;
    const dailyPassRate = audits > 0 ? Math.round(((audits - violations) / audits) * 100) : 100;

    return (
      <div className="bg-slate-900/95 border border-slate-700/80 rounded-xl p-3.5 shadow-2xl backdrop-blur-md text-xs min-w-[190px]">
        <div className="text-[11px] font-semibold text-slate-400 border-b border-slate-800 pb-1.5 mb-2 flex items-center gap-1.5">
          <Calendar size={12} className="text-indigo-400" />
          {formattedDate}
        </div>
        
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-slate-300">
            <span className="flex items-center gap-1.5 text-[11px]">
              <span className="w-2 h-2 rounded-full bg-indigo-500" />
              Total Audits:
            </span>
            <span className="font-bold text-white text-xs">{audits}</span>
          </div>

          <div className="flex items-center justify-between text-slate-300">
            <span className="flex items-center gap-1.5 text-[11px]">
              <span className="w-2 h-2 rounded-full bg-rose-500" />
              Violations:
            </span>
            <span className="font-bold text-rose-400 text-xs">{violations}</span>
          </div>

          <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-[11px]">
            <span className="text-slate-400">Compliance:</span>
            <span className={`font-semibold ${dailyPassRate >= 80 ? 'text-emerald-400' : 'text-amber-400'}`}>
              {dailyPassRate}%
            </span>
          </div>
        </div>
      </div>
    );
  }
  return null;
};

export default function AdminDashboard() {
  const [overview, setOverview] = useState(null);
  const [trends, setTrends] = useState([]);
  const [geoIntel, setGeoIntel] = useState({ geo_json: { features: [] }, stats: {} });
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [legalModalOpen, setLegalModalOpen] = useState(false);
  const [legalActionType, setLegalActionType] = useState('Compounding Penalty Notice (Section 36)');
  const [legalActionNotes, setLegalActionNotes] = useState('');
  const [submittingLegalAction, setSubmittingLegalAction] = useState(false);
  const [days, setDays] = useState(14);
  const [chartType, setChartType] = useState('bar'); // 'bar' | 'area'
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState(null);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);
      const [overviewData, trendsData, geoData] = await Promise.all([
        getAnalyticsOverviewApi(),
        getAnalyticsTrendsApi(days),
        getAdminGeoIntelligenceApi().catch(() => ({ geo_json: { features: [] }, stats: {} }))
      ]);
      setOverview(overviewData);
      setGeoIntel(geoData);
      
      // Robust array extraction (handles { trends: [...] } and direct arrays)
      const rawTrends = trendsData?.trends || (Array.isArray(trendsData) ? trendsData : []);
      setTrends(rawTrends);
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

  // Format date tick like "19 Sep"
  const formatXAxis = (tickItem) => {
    try {
      const parts = tickItem.split('-');
      if (parts.length === 3) {
        const d = new Date(tickItem);
        return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
      }
      return tickItem;
    } catch {
      return tickItem;
    }
  };

  // Aggregated stats over selected window
  const windowStats = useMemo(() => {
    if (!trends || !trends.length) return { totalAudits: 0, totalViolations: 0, peakDaily: 0 };
    let totalAudits = 0;
    let totalViolations = 0;
    let peakDaily = 0;
    trends.forEach(t => {
      totalAudits += (t.inspections || 0);
      totalViolations += (t.violations || 0);
      if ((t.inspections || 0) > peakDaily) peakDaily = t.inspections;
    });
    return { totalAudits, totalViolations, peakDaily };
  }, [trends]);

  return (
    <div className="space-y-6">
      {/* Top Header & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2.5">
              <span className="p-2 rounded-xl bg-indigo-500/15 border border-indigo-500/30 text-indigo-400">
                <TrendingUp size={22} />
              </span>
              Executive Oversight & Analytics
            </h1>
            <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
              Live Feed
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            National Legal Metrology compliance telemetry, statutory breach audits & daily time-series.
          </p>
        </div>

        <div className="flex items-center gap-2.5 flex-wrap">
          <button
            onClick={fetchAnalytics}
            disabled={loading}
            className="px-3.5 py-2 rounded-xl bg-slate-900/80 border border-slate-700/80 hover:bg-slate-800 text-slate-300 hover:text-white transition flex items-center gap-2 text-xs font-semibold shadow-sm cursor-pointer"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin text-indigo-400' : ''} />
            Refresh
          </button>
          
          <button
            onClick={handleExportCsv}
            disabled={exporting}
            className="px-3.5 py-2 rounded-xl bg-slate-900/80 border border-slate-700/80 hover:bg-slate-800 text-slate-300 hover:text-white transition flex items-center gap-2 text-xs font-semibold shadow-sm disabled:opacity-50 cursor-pointer"
          >
            <Download size={14} className={exporting ? 'animate-bounce text-indigo-400' : ''} />
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
            className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold shadow-md shadow-indigo-600/25 transition flex items-center gap-2 text-xs cursor-pointer"
          >
            <Download size={14} />
            Summary (XLSX)
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3.5 rounded-xl bg-rose-950/60 border border-rose-800/80 text-rose-300 text-xs flex items-center gap-2.5 shadow-md">
          <AlertTriangle size={17} className="text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* 4 KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Audits */}
        <div className="bg-slate-900/80 border border-slate-800/90 rounded-2xl p-5 shadow-lg relative overflow-hidden backdrop-blur">
          <div className="absolute top-0 right-0 w-24 h-24 bg-indigo-500/10 rounded-full blur-xl pointer-events-none" />
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Total Audits</span>
            <div className="p-2 rounded-xl bg-indigo-500/15 border border-indigo-500/30 text-indigo-400">
              <FileText size={18} />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-white">{overview?.inspections?.total ?? '—'}</span>
            <span className="text-xs text-slate-400">Recorded Inspections</span>
          </div>
          <div className="mt-3.5 flex items-center justify-between text-xs text-slate-400 border-t border-slate-800/80 pt-3">
            <span>Finalized: <strong className="text-white">{overview?.inspections?.finalized ?? 0}</strong></span>
            <span>Pending: <strong className="text-amber-400">{overview?.inspections?.pending_review ?? 0}</strong></span>
          </div>
        </div>

        {/* Compliance Rate */}
        <div className="bg-slate-900/80 border border-slate-800/90 rounded-2xl p-5 shadow-lg relative overflow-hidden backdrop-blur">
          <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/10 rounded-full blur-xl pointer-events-none" />
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Compliance Rate</span>
            <div className="p-2 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-400">
              <ShieldCheck size={18} />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-emerald-400">
              {overview?.inspections?.total ? (
                `${Math.round(((overview.inspections.compliant || 0) / overview.inspections.total) * 100)}%`
              ) : '—'}
            </span>
            <span className="text-xs text-slate-400">Automated Passing</span>
          </div>
          <div className="mt-3.5 flex items-center justify-between text-xs text-slate-400 border-t border-slate-800/80 pt-3">
            <span className="text-emerald-400">Compliant: <strong>{overview?.inspections?.compliant ?? 0}</strong></span>
            <span className="text-rose-400">Non-Compliant: <strong>{overview?.inspections?.non_compliant ?? 0}</strong></span>
          </div>
        </div>

        {/* Statutory Violations */}
        <div className="bg-slate-900/80 border border-slate-800/90 rounded-2xl p-5 shadow-lg relative overflow-hidden backdrop-blur">
          <div className="absolute top-0 right-0 w-24 h-24 bg-rose-500/10 rounded-full blur-xl pointer-events-none" />
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Statutory Violations</span>
            <div className="p-2 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-400">
              <AlertTriangle size={18} />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-rose-400">{overview?.violations?.total ?? '0'}</span>
            <span className="text-xs text-slate-400">Total Breaches</span>
          </div>
          <div className="mt-3.5 flex items-center justify-between text-xs text-slate-400 border-t border-slate-800/80 pt-3">
            <span className="text-amber-400">Open: <strong>{overview?.violations?.open ?? 0}</strong></span>
            <span className="text-emerald-400">Resolved: <strong>{overview?.violations?.resolved ?? 0}</strong></span>
          </div>
        </div>

        {/* Rule Engine Inventory */}
        <div className="bg-slate-900/80 border border-slate-800/90 rounded-2xl p-5 shadow-lg relative overflow-hidden backdrop-blur">
          <div className="absolute top-0 right-0 w-24 h-24 bg-purple-500/10 rounded-full blur-xl pointer-events-none" />
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Rule Engine Inventory</span>
            <div className="p-2 rounded-xl bg-purple-500/15 border border-purple-500/30 text-purple-400">
              <Layers size={18} />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-white">{overview?.rules?.total_rules ?? '—'}</span>
            <span className="text-xs text-slate-400">Registered Rules</span>
          </div>
          <div className="mt-3.5 flex items-center justify-between text-xs text-slate-400 border-t border-slate-800/80 pt-3">
            <span className="text-amber-400">Demo Rules: <strong>{overview?.rules?.demo_versions ?? 0}</strong></span>
            <span className="text-purple-400">Statutory: <strong>{overview?.rules?.verified_versions ?? 0}</strong></span>
          </div>
        </div>
      </div>

      {/* Analytics Trend Graph Container */}
      <div className="bg-slate-900/80 border border-slate-800/90 rounded-2xl p-5 sm:p-6 shadow-xl backdrop-blur relative overflow-hidden">
        
        {/* Header with Title, Summary Chips & Controls */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between pb-5 border-b border-slate-800 gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <BarChart3 size={18} className="text-indigo-400" />
                Daily Inspection & Breach Activity
              </h2>
              <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                Aggregated Trends
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Time-series tracking of total label verification volumes and logged non-compliance breaches
            </p>
          </div>

          <div className="flex items-center gap-3 flex-wrap">
            {/* Quick summary metrics chips */}
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-slate-950/60 border border-slate-800 rounded-xl text-xs">
              <span className="text-slate-400">Window Audits: <strong className="text-indigo-400">{windowStats.totalAudits}</strong></span>
              <span className="text-slate-600">|</span>
              <span className="text-slate-400">Breaches: <strong className="text-rose-400">{windowStats.totalViolations}</strong></span>
              <span className="text-slate-600">|</span>
              <span className="text-slate-400">Peak Daily: <strong className="text-white">{windowStats.peakDaily}</strong></span>
            </div>

            {/* Chart Type Toggle */}
            <div className="flex items-center bg-slate-950/80 border border-slate-800 p-1 rounded-xl">
              <button
                onClick={() => setChartType('bar')}
                className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition flex items-center gap-1.5 cursor-pointer ${
                  chartType === 'bar'
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
                title="Bar Chart View"
              >
                <BarChart3 size={13} />
                Bar View
              </button>
              <button
                onClick={() => setChartType('area')}
                className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition flex items-center gap-1.5 cursor-pointer ${
                  chartType === 'area'
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
                title="Trend Area View"
              >
                <Activity size={13} />
                Trend View
              </button>
            </div>

            {/* Timeframe Selector */}
            <div className="flex items-center gap-1 bg-slate-950/80 border border-slate-800 p-1 rounded-xl">
              {[7, 14, 30].map(d => (
                <button
                  key={d}
                  onClick={() => setDays(d)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition cursor-pointer ${
                    days === d 
                      ? 'bg-indigo-600 text-white shadow-sm' 
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {d}D
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Main Chart Canvas */}
        <div className="mt-6 h-80 w-full min-w-0">
          {trends.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-slate-400 text-xs space-y-2">
              <Activity size={28} className="text-slate-600 animate-pulse" />
              <p>No trend telemetry recorded for the past {days} days.</p>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              {chartType === 'bar' ? (
                <BarChart data={trends} margin={{ top: 15, right: 15, left: -20, bottom: 5 }}>
                  <defs>
                    <linearGradient id="barAuditGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#818cf8" stopOpacity={1} />
                      <stop offset="100%" stopColor="#4f46e5" stopOpacity={0.85} />
                    </linearGradient>
                    <linearGradient id="barViolGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#f43f5e" stopOpacity={1} />
                      <stop offset="100%" stopColor="#e11d48" stopOpacity={0.85} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.4} vertical={false} />
                  <XAxis 
                    dataKey="date" 
                    tickFormatter={formatXAxis}
                    stroke="#64748b" 
                    fontSize={11} 
                    tickLine={false}
                    dy={5}
                  />
                  <YAxis 
                    stroke="#64748b" 
                    fontSize={11} 
                    tickLine={false} 
                    allowDecimals={false}
                  />
                  <Tooltip content={<CustomChartTooltip />} />
                  <Legend 
                    wrapperStyle={{ paddingTop: '16px', fontSize: '12px' }} 
                    formatter={(value) => <span className="text-slate-300 font-medium">{value}</span>}
                  />
                  <Bar 
                    dataKey="inspections" 
                    name="Total Audits" 
                    fill="url(#barAuditGrad)" 
                    radius={[6, 6, 0, 0]} 
                    maxBarSize={45}
                  />
                  <Bar 
                    dataKey="violations" 
                    name="Violations" 
                    fill="url(#barViolGrad)" 
                    radius={[6, 6, 0, 0]} 
                    maxBarSize={45}
                  />
                </BarChart>
              ) : (
                <AreaChart data={trends} margin={{ top: 15, right: 15, left: -20, bottom: 5 }}>
                  <defs>
                    <linearGradient id="areaAuditGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366f1" stopOpacity={0.45} />
                      <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
                    </linearGradient>
                    <linearGradient id="areaViolGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.45} />
                      <stop offset="95%" stopColor="#f43f5e" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.4} vertical={false} />
                  <XAxis 
                    dataKey="date" 
                    tickFormatter={formatXAxis}
                    stroke="#64748b" 
                    fontSize={11} 
                    tickLine={false}
                    dy={5}
                  />
                  <YAxis 
                    stroke="#64748b" 
                    fontSize={11} 
                    tickLine={false} 
                    allowDecimals={false}
                  />
                  <Tooltip content={<CustomChartTooltip />} />
                  <Legend 
                    wrapperStyle={{ paddingTop: '16px', fontSize: '12px' }} 
                    formatter={(value) => <span className="text-slate-300 font-medium">{value}</span>}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="inspections" 
                    name="Total Audits" 
                    stroke="#818cf8" 
                    strokeWidth={2.5}
                    fillOpacity={1} 
                    fill="url(#areaAuditGrad)" 
                  />
                  <Area 
                    type="monotone" 
                    dataKey="violations" 
                    name="Violations" 
                    stroke="#f43f5e" 
                    strokeWidth={2.5}
                    fillOpacity={1} 
                    fill="url(#areaViolGrad)" 
                  />
                </AreaChart>
              )}
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* MapTiler National Geospatial Radar */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <MapPin size={18} className="text-rose-400" />
              Pan-India Legal Metrology Geospatial Radar (MapTiler)
            </h2>
            <p className="text-xs text-slate-400">
              Real-time visualization of citizen incident reports, hot spot districts, and supply-chain breaches.
            </p>
          </div>
          <div className="flex items-center gap-3 text-xs text-slate-400 font-mono">
            <span>Total Hotspots: <strong className="text-white">{geoIntel.geo_json?.features?.length || 0}</strong></span>
            <span>Escalations: <strong className="text-amber-400">{geoIntel.stats?.escalated_count || 0}</strong></span>
          </div>
        </div>

        <IndiaMapView
          incidents={geoIntel.geo_json?.features || []}
          height="450px"
          onSelectIncident={(inc) => {
            setSelectedIncident(inc);
            setLegalActionNotes(`Formal compounding penalty under Section 36 for non-compliant packaged commodity [${inc.properties?.product_name || 'Item'}].`);
            setLegalModalOpen(true);
          }}
        />
      </div>

      {/* National Legal Escalations & Sanctions Center */}
      <div className="bg-slate-900/80 border border-slate-800/90 rounded-2xl p-5 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Gavel size={18} className="text-amber-400" />
              Statutory Enforcement & Legal Sanctions Docket
            </h2>
            <p className="text-xs text-slate-400">
              Escalated incidents requiring formal administrative sanctions, compounding penalties, or seizure warrants.
            </p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-950 text-xs uppercase font-semibold text-slate-400 border-b border-slate-800">
              <tr>
                <th className="px-5 py-3">Product Name</th>
                <th className="px-5 py-3">Failing Rules</th>
                <th className="px-5 py-3">Reported Store / Origin</th>
                <th className="px-5 py-3">Wholesale Distributor</th>
                <th className="px-5 py-3">Status</th>
                <th className="px-5 py-3 text-right">Legal Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {(geoIntel.geo_json?.features || []).map((feat) => {
                const p = feat.properties || {};
                const isResolved = p.status === 'resolved';

                return (
                  <tr key={feat.id} className="hover:bg-slate-800/30 transition">
                    <td className="px-5 py-3.5 font-medium text-white">
                      {p.product_name}
                    </td>
                    <td className="px-5 py-3.5">
                      <div className="flex flex-wrap gap-1">
                        {(p.failing_rules || []).map((r) => (
                          <span key={r} className="px-1.5 py-0.5 rounded bg-rose-950/80 border border-rose-800/80 text-rose-300 text-[10px] font-mono">
                            {r}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-5 py-3.5 text-xs text-slate-300 font-mono">
                      {p.date}
                    </td>
                    <td className="px-5 py-3.5 text-xs text-slate-300">
                      {p.supplier}
                    </td>
                    <td className="px-5 py-3.5">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                        isResolved
                          ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                          : 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                      }`}>
                        {p.status}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      {!isResolved ? (
                        <button
                          onClick={() => {
                            setSelectedIncident(feat);
                            setLegalActionNotes(`Compounding fine issued under Section 36 of Legal Metrology Act for package non-compliance.`);
                            setLegalModalOpen(true);
                          }}
                          className="px-3 py-1.5 bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold rounded-lg transition shadow flex items-center gap-1.5 ml-auto"
                        >
                          <Gavel size={13} />
                          <span>Sanction Order</span>
                        </button>
                      ) : (
                        <span className="text-xs text-emerald-400 font-mono font-semibold">
                          {p.action_taken}
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Admin Legal Sanction Modal */}
      {legalModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-[#0f172a] border border-slate-700 rounded-2xl w-full max-w-lg p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2 text-amber-400">
                <Gavel size={20} />
                <h3 className="text-base font-bold text-white">Execute Statutory Sanction Order</h3>
              </div>
              <button
                onClick={() => setLegalModalOpen(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg"
              >
                <X size={18} />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <p className="text-slate-300">
                Issue a binding statutory order for commodity: <strong>{selectedIncident?.properties?.product_name || 'Packaged Commodity'}</strong>.
              </p>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Sanction Action Type:</label>
                <select
                  value={legalActionType}
                  onChange={(e) => setLegalActionType(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-amber-500"
                >
                  <option value="Compounding Penalty Notice (Section 36)">Compounding Penalty Notice (Section 36 - First Offense: Up to ₹25,000)</option>
                  <option value="Batch Seizure & Forfeiture Warrant">Batch Seizure & Forfeiture Warrant</option>
                  <option value="Court Prosecution & Summons (Section 48)">Court Prosecution & Summons (Section 48)</option>
                  <option value="Show-Cause Revocation of Packer Registration">Show-Cause Revocation of Packer Registration</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Sanction Directive Notes / Order Reference:</label>
                <textarea
                  rows={4}
                  value={legalActionNotes}
                  onChange={(e) => setLegalActionNotes(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-slate-200 focus:outline-none focus:border-amber-500"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-slate-800">
              <button
                onClick={() => setLegalModalOpen(false)}
                className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={async () => {
                  if (!selectedIncident) return;
                  setSubmittingLegalAction(true);
                  try {
                    await executeAdminLegalActionApi({
                      report_id: selectedIncident.id,
                      action_type: legalActionType,
                      action_notes: legalActionNotes,
                    });
                    alert(`Statutory Sanction Order [${legalActionType}] issued and recorded successfully.`);
                    setLegalModalOpen(false);
                    fetchAnalytics();
                  } catch (err) {
                    alert('Failed to execute legal sanction: ' + (err.response?.data?.detail || err.message));
                  } finally {
                    setSubmittingLegalAction(false);
                  }
                }}
                disabled={submittingLegalAction}
                className="px-5 py-2 rounded-xl bg-amber-600 hover:bg-amber-500 text-white text-xs font-bold transition shadow-lg shadow-amber-600/30 flex items-center gap-1.5 disabled:opacity-50"
              >
                {submittingLegalAction ? <RefreshCw size={14} className="animate-spin" /> : <Gavel size={14} />}
                <span>{submittingLegalAction ? 'Sealing Order...' : 'Execute Sanction'}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
