import React, { useState, useEffect } from 'react';
import { listScansApi } from '../../api/scans';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import StatusBadge from '../../components/StatusBadge';
import EmptyState from '../../components/EmptyState';
import {
  Search,
  Filter,
  ArrowRight,
  Camera,
  FileText,
  ShieldCheck,
  AlertTriangle,
  Clock,
  CheckCircle2,
  XCircle,
  Layers,
  RefreshCw,
  Eye,
  FileSpreadsheet,
} from 'lucide-react';

const InspectionHistory = () => {
  const { user } = useAuth();
  const role = user?.role || 'officer';
  const basePath = role === 'admin' ? '/admin' : role === 'retailer' ? '/retailer' : '/officer';

  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [complianceFilter, setComplianceFilter] = useState('all');

  useEffect(() => {
    fetchScans();
  }, []);

  const fetchScans = async () => {
    try {
      setLoading(true);
      const data = await listScansApi();
      setScans(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Failed to load inspections:', err);
    } finally {
      setLoading(false);
    }
  };

  const totalCount = scans.length;
  const compliantCount = scans.filter(
    (s) => s.final_compliance === 'compliant' || (!s.final_compliance && s.automated_compliance === 'compliant')
  ).length;
  const nonCompliantCount = scans.filter(
    (s) => s.final_compliance === 'non_compliant' || (!s.final_compliance && s.automated_compliance === 'non_compliant')
  ).length;
  const needsReviewCount = scans.filter(
    (s) => (s.final_compliance || s.automated_compliance) === 'needs_review' || (!s.final_compliance && !s.automated_compliance)
  ).length;

  const filteredScans = scans.filter((scan) => {
    const matchesSearch =
      (scan.product_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (scan.brand_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (scan.officer_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (scan.id || '').toLowerCase().includes(searchTerm.toLowerCase());

    const compStatus = scan.final_compliance || scan.automated_compliance || 'needs_review';
    const matchesCompliance =
      complianceFilter === 'all' || compStatus === complianceFilter;

    return matchesSearch && matchesCompliance;
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2.5">
              <span className="p-2 rounded-xl bg-indigo-500/15 border border-indigo-500/30 text-indigo-400">
                <FileText size={22} />
              </span>
              {role === 'admin'
                ? 'National Inspections & Citizen Reports Audit'
                : role === 'retailer'
                ? 'Compliance Inquiries & Premises Audits'
                : 'Inspection Records Archive'}
            </h1>
            <span className="text-[10px] font-bold uppercase px-2.5 py-0.5 rounded-full bg-indigo-500/15 text-indigo-400 border border-indigo-500/30">
              Audit Registry
            </span>
          </div>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            {role === 'admin'
              ? 'Centralized audit log of all officer inspections, citizen reports, automated OCR checks, and statutory verdicts.'
              : role === 'retailer'
              ? 'Review compliance audit logs, statutory verdicts, and certification records for your retail premises.'
              : 'Historical package inspections, cryptographic hashes, and statutory compliance verdicts.'}
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={fetchScans}
            disabled={loading}
            className="px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-700 hover:bg-slate-800 text-slate-300 hover:text-white transition flex items-center gap-2 text-xs font-semibold shadow-sm cursor-pointer"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin text-indigo-400' : ''} />
            <span>Refresh</span>
          </button>

          {/* Only Officer gets New Inspection button. Admin and Retailer do NOT have this button! */}
          {role === 'officer' && (
            <Link
              to="/officer/new-inspection"
              className="inline-flex items-center space-x-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-xl shadow-lg shadow-indigo-600/25 transition cursor-pointer"
            >
              <Camera size={15} />
              <span>New Inspection</span>
            </Link>
          )}
        </div>
      </div>

      {/* 4 Summary KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div
          onClick={() => setComplianceFilter('all')}
          className={`p-4 rounded-xl border transition cursor-pointer ${
            complianceFilter === 'all'
              ? 'bg-slate-800/90 border-indigo-500 ring-1 ring-indigo-500/30 shadow-lg'
              : 'bg-slate-900/80 border-slate-800 hover:border-slate-700'
          }`}
        >
          <div className="flex items-center justify-between text-xs text-slate-400 uppercase font-bold">
            <span>Total Audited</span>
            <Layers size={16} className="text-indigo-400" />
          </div>
          <p className="text-2xl font-extrabold text-white mt-1.5">{loading ? '...' : totalCount}</p>
          <p className="text-[11px] text-slate-400 mt-1">Logged inspection records</p>
        </div>

        <div
          onClick={() => setComplianceFilter('compliant')}
          className={`p-4 rounded-xl border transition cursor-pointer ${
            complianceFilter === 'compliant'
              ? 'bg-slate-800/90 border-emerald-500 ring-1 ring-emerald-500/30 shadow-lg'
              : 'bg-slate-900/80 border-slate-800 hover:border-slate-700'
          }`}
        >
          <div className="flex items-center justify-between text-xs text-emerald-400 uppercase font-bold">
            <span>Fully Compliant</span>
            <CheckCircle2 size={16} className="text-emerald-400" />
          </div>
          <p className="text-2xl font-extrabold text-emerald-400 mt-1.5">{loading ? '...' : compliantCount}</p>
          <p className="text-[11px] text-emerald-400/80 mt-1">10/10 rules verified</p>
        </div>

        <div
          onClick={() => setComplianceFilter('non_compliant')}
          className={`p-4 rounded-xl border transition cursor-pointer ${
            complianceFilter === 'non_compliant'
              ? 'bg-slate-800/90 border-rose-500 ring-1 ring-rose-500/30 shadow-lg'
              : 'bg-slate-900/80 border-slate-800 hover:border-slate-700'
          }`}
        >
          <div className="flex items-center justify-between text-xs text-rose-400 uppercase font-bold">
            <span>Violations / Missing</span>
            <XCircle size={16} className="text-rose-400" />
          </div>
          <p className="text-2xl font-extrabold text-rose-400 mt-1.5">{loading ? '...' : nonCompliantCount}</p>
          <p className="text-[11px] text-rose-400/80 mt-1">Statutory breaches detected</p>
        </div>

        <div
          onClick={() => setComplianceFilter('needs_review')}
          className={`p-4 rounded-xl border transition cursor-pointer ${
            complianceFilter === 'needs_review'
              ? 'bg-slate-800/90 border-amber-500 ring-1 ring-amber-500/30 shadow-lg'
              : 'bg-slate-900/80 border-slate-800 hover:border-slate-700'
          }`}
        >
          <div className="flex items-center justify-between text-xs text-amber-400 uppercase font-bold">
            <span>Needs Review</span>
            <AlertTriangle size={16} className="text-amber-400" />
          </div>
          <p className="text-2xl font-extrabold text-amber-400 mt-1.5">{loading ? '...' : needsReviewCount}</p>
          <p className="text-[11px] text-amber-400/80 mt-1">Advisory / Incomplete</p>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-2xl flex flex-col md:flex-row gap-3 items-center justify-between shadow-lg">
        <div className="relative flex-1 w-full md:max-w-md">
          <Search size={16} className="absolute left-3.5 top-3 text-slate-400" />
          <input
            type="text"
            placeholder="Search by commodity, brand, inspector, or ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-950 border border-slate-700/80 rounded-xl text-xs sm:text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition"
          />
        </div>

        {/* Tab Filters */}
        <div className="flex items-center gap-1.5 w-full md:w-auto overflow-x-auto pb-1 md:pb-0">
          {[
            { id: 'all', label: 'All Audits' },
            { id: 'compliant', label: 'Compliant' },
            { id: 'non_compliant', label: 'Violations' },
            { id: 'needs_review', label: 'Under Review' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setComplianceFilter(tab.id)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition cursor-pointer ${
                complianceFilter === tab.id
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/20'
                  : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-800'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Table Container */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        {loading ? (
          <div className="p-14 text-center text-slate-400 text-xs">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500 mb-3" />
            <p>Retrieving statutory inspection audit logs...</p>
          </div>
        ) : filteredScans.length === 0 ? (
          <div className="p-8">
            <EmptyState
              title="No Inspection Records Found"
              message={
                searchTerm || complianceFilter !== 'all'
                  ? 'No inspections matched your filter criteria. Try clearing search or status filters.'
                  : 'No inspection records or user reports have been logged in the audit registry yet.'
              }
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs sm:text-sm text-slate-300">
              <thead className="bg-slate-950 text-[11px] uppercase font-bold text-slate-400 border-b border-slate-800 tracking-wider">
                <tr>
                  <th className="px-5 py-3.5">Commodity & Brand</th>
                  <th className="px-5 py-3.5">Inspection ID / Date</th>
                  <th className="px-5 py-3.5">Auditor / Submitter</th>
                  <th className="px-5 py-3.5">Compliance Verdict</th>
                  <th className="px-5 py-3.5">Security Seal</th>
                  <th className="px-5 py-3.5 text-right">Audit Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {filteredScans.map((scan) => {
                  const compStatus = scan.final_compliance || scan.automated_compliance || 'needs_review';
                  const dateStr = scan.created_at
                    ? new Date(scan.created_at).toLocaleDateString('en-IN', {
                        day: 'numeric',
                        month: 'short',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })
                    : '—';

                  return (
                    <tr key={scan.id} className="hover:bg-slate-800/40 transition">
                      <td className="px-5 py-4">
                        <div className="font-bold text-white text-xs sm:text-sm">
                          {scan.product_name || 'Packaged Commodity'}
                        </div>
                        <div className="text-[11px] text-slate-400 mt-0.5 flex items-center gap-1.5">
                          <span>Brand: <strong className="text-slate-300">{scan.brand_name || 'Generic / Unbranded'}</strong></span>
                        </div>
                      </td>

                      <td className="px-5 py-4">
                        <div className="font-mono text-[11px] text-indigo-300">
                          {scan.id ? `${scan.id.substring(0, 12)}...` : 'ID-SCAN'}
                        </div>
                        <div className="text-[10px] text-slate-500 mt-0.5 flex items-center gap-1">
                          <Clock size={11} />
                          <span>{dateStr}</span>
                        </div>
                      </td>

                      <td className="px-5 py-4">
                        <div className="text-xs font-medium text-slate-200">
                          {scan.officer_name || scan.user_email || 'Enforcement Inspector'}
                        </div>
                        <div className="text-[10px] text-slate-500 uppercase font-mono">
                          {scan.area_name || 'Jurisdiction LMPC'}
                        </div>
                      </td>

                      <td className="px-5 py-4">
                        <StatusBadge status={compStatus} />
                      </td>

                      <td className="px-5 py-4">
                        {scan.report_hash ? (
                          <div className="flex items-center gap-1.5 text-emerald-400 text-[11px] font-mono">
                            <ShieldCheck size={14} />
                            <span>SHA-256 Sealed</span>
                          </div>
                        ) : (
                          <span className="text-[11px] text-slate-500 font-mono">Unsealed Draft</span>
                        )}
                      </td>

                      <td className="px-5 py-4 text-right">
                        <Link
                          to={`${basePath}/inspections/${scan.id}`}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600/20 hover:bg-indigo-600 text-indigo-300 hover:text-white border border-indigo-500/30 rounded-lg text-xs font-bold transition shadow-sm cursor-pointer"
                        >
                          <Eye size={13} />
                          <span>Inspect Report</span>
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default InspectionHistory;
