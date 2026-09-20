import { useState, useEffect } from 'react';
import { listScansApi } from '../../api/scans';
import { Link } from 'react-router-dom';
import StatusBadge from '../../components/StatusBadge';
import EmptyState from '../../components/EmptyState';
import {
  Camera,
  ClipboardList,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ArrowRight,
  ShieldCheck,
  Search,
} from 'lucide-react';

const OfficerDashboard = () => {
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchScans();
  }, []);

  const fetchScans = async () => {
    try {
      setLoading(true);
      const data = await listScansApi();
      setScans(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to fetch inspections');
    } finally {
      setLoading(false);
    }
  };

  // Real backend metrics calculation
  const total = scans.length;
  const compliant = scans.filter((s) => s.final_compliance === 'compliant').length;
  const nonCompliant = scans.filter((s) => s.final_compliance === 'non_compliant').length;
  const needsReview = scans.filter((s) => s.status === 'needs_review' || s.final_compliance === 'needs_review').length;
  const finalized = scans.filter((s) => s.is_finalized).length;

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-indigo-950/80 via-slate-900 to-slate-900 border border-indigo-800/40 p-6 rounded-xl shadow-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-indigo-400 text-xs font-bold uppercase tracking-wider mb-1">
            <ShieldCheck size={16} />
            <span>Field Enforcement Unit</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Legal Metrology Inspection Console</h1>
          <p className="text-sm text-slate-400 mt-1">
            Standard Operating Procedures for Packaged Commodities Act inspections and verification.
          </p>
        </div>
        <div>
          <Link
            to="/officer/new-inspection"
            className="inline-flex items-center space-x-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold rounded-lg shadow-md shadow-indigo-600/30 transition"
          >
            <Camera size={18} />
            <span>New Package Inspection</span>
          </Link>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-800/90 border border-slate-700/80 p-4 rounded-xl">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
            <span>Total Inspections</span>
            <ClipboardList size={18} className="text-indigo-400" />
          </div>
          <p className="text-3xl font-extrabold text-white mt-2">{loading ? '...' : total}</p>
          <p className="text-xs text-slate-400 mt-1">{finalized} officially finalized</p>
        </div>

        <div className="bg-slate-800/90 border border-slate-700/80 p-4 rounded-xl">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
            <span>Compliant Packages</span>
            <CheckCircle2 size={18} className="text-emerald-400" />
          </div>
          <p className="text-3xl font-extrabold text-emerald-400 mt-2">{loading ? '...' : compliant}</p>
          <p className="text-xs text-slate-400 mt-1">Met all mandatory declarations</p>
        </div>

        <div className="bg-slate-800/90 border border-slate-700/80 p-4 rounded-xl">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
            <span>Non-Compliant</span>
            <AlertTriangle size={18} className="text-rose-400" />
          </div>
          <p className="text-3xl font-extrabold text-rose-400 mt-2">{loading ? '...' : nonCompliant}</p>
          <p className="text-xs text-slate-400 mt-1">Eligible for statutory notice</p>
        </div>

        <div className="bg-slate-800/90 border border-slate-700/80 p-4 rounded-xl">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
            <span>Pending Review</span>
            <Clock size={18} className="text-amber-400" />
          </div>
          <p className="text-3xl font-extrabold text-amber-400 mt-2">{loading ? '...' : needsReview}</p>
          <p className="text-xs text-slate-400 mt-1">Requires manual officer check</p>
        </div>
      </div>

      {/* Recent Inspections Table */}
      <div className="bg-slate-800/90 border border-slate-700/80 rounded-xl overflow-hidden shadow-lg">
        <div className="px-6 py-4 border-b border-slate-700 flex items-center justify-between">
          <h2 className="text-base font-bold text-white">Recent Field Inspections</h2>
          <Link
            to="/officer/inspections"
            className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold inline-flex items-center space-x-1"
          >
            <span>View All Records</span>
            <ArrowRight size={14} />
          </Link>
        </div>

        {loading ? (
          <div className="p-12 text-center text-slate-400 text-sm">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500 mb-3"></div>
            <p>Loading real-time inspection telemetry from database...</p>
          </div>
        ) : error ? (
          <div className="p-8 text-center text-rose-400 text-sm bg-rose-950/20 border-b border-rose-900">
            <AlertTriangle size={24} className="mx-auto mb-2 text-rose-400" />
            <p className="font-semibold">Failed to load inspections</p>
            <p className="text-xs text-slate-400 mt-1">{error}</p>
          </div>
        ) : scans.length === 0 ? (
          <div className="p-6">
            <EmptyState
              title="No inspection records found"
              message="You haven't conducted any product inspections yet. Click 'New Package Inspection' to begin."
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-900/80 text-xs uppercase font-semibold text-slate-400 border-b border-slate-700">
                <tr>
                  <th className="px-6 py-3">Product Name</th>
                  <th className="px-6 py-3">Brand</th>
                  <th className="px-6 py-3">Inspection ID</th>
                  <th className="px-6 py-3">Date</th>
                  <th className="px-6 py-3">Status</th>
                  <th className="px-6 py-3">Compliance</th>
                  <th className="px-6 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/60">
                {scans.slice(0, 10).map((scan) => (
                  <tr key={scan.id} className="hover:bg-slate-750/50 transition">
                    <td className="px-6 py-3.5 font-medium text-white">
                      {scan.product_name || 'Unspecified Commodity'}
                    </td>
                    <td className="px-6 py-3.5 text-slate-300">{scan.brand_name || '—'}</td>
                    <td className="px-6 py-3.5 font-mono text-xs text-slate-400">
                      {scan.id?.substring(0, 8)}...
                    </td>
                    <td className="px-6 py-3.5 text-xs text-slate-400">
                      {scan.created_at ? new Date(scan.created_at).toLocaleString() : '—'}
                    </td>
                    <td className="px-6 py-3.5">
                      <StatusBadge status={scan.status} />
                    </td>
                    <td className="px-6 py-3.5">
                      <StatusBadge status={scan.final_compliance || scan.automated_compliance || 'needs_review'} />
                    </td>
                    <td className="px-6 py-3.5 text-right">
                      <Link
                        to={`/officer/inspections/${scan.id}`}
                        className="inline-flex items-center space-x-1 text-xs text-indigo-400 hover:text-indigo-300 font-semibold"
                      >
                        <span>Audit Result</span>
                        <ArrowRight size={13} />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default OfficerDashboard;
