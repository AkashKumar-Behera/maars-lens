import { useState, useEffect } from 'react';
import { listScansApi } from '../../api/scans';
import { Link } from 'react-router-dom';
import StatusBadge from '../../components/StatusBadge';
import EmptyState from '../../components/EmptyState';
import { Search, Filter, ArrowRight, Camera, FileText } from 'lucide-react';

const InspectionHistory = () => {
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [complianceFilter, setComplianceFilter] = useState('');

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

  const filteredScans = scans.filter((scan) => {
    const matchesSearch =
      (scan.product_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (scan.brand_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (scan.id || '').toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCompliance =
      !complianceFilter || scan.final_compliance === complianceFilter || scan.automated_compliance === complianceFilter;
    return matchesSearch && matchesCompliance;
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Inspection Records Archive</h1>
          <p className="text-sm text-slate-400 mt-1">
            Historical package inspections, cryptographic hashes, and compliance verdicts.
          </p>
        </div>
        <Link
          to="/officer/new-inspection"
          className="inline-flex items-center space-x-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg shadow-md transition"
        >
          <Camera size={16} />
          <span>New Inspection</span>
        </Link>
      </div>

      {/* Filter Bar */}
      <div className="bg-slate-800/90 border border-slate-700/80 p-4 rounded-xl flex flex-col md:flex-row gap-4 justify-between">
        <div className="relative flex-1 max-w-md">
          <Search size={16} className="absolute left-3 top-3 text-slate-400" />
          <input
            type="text"
            placeholder="Search by commodity, brand, or ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div className="flex items-center space-x-2">
          <Filter size={16} className="text-slate-400" />
          <select
            value={complianceFilter}
            onChange={(e) => setComplianceFilter(e.target.value)}
            className="px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All Compliance Statuses</option>
            <option value="compliant">Compliant</option>
            <option value="non_compliant">Non-Compliant</option>
            <option value="needs_review">Needs Review</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="bg-slate-800/90 border border-slate-700/80 rounded-xl overflow-hidden shadow-lg">
        {loading ? (
          <div className="p-12 text-center text-slate-400 text-sm">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500 mb-3"></div>
            <p>Retrieving inspection logs from database...</p>
          </div>
        ) : filteredScans.length === 0 ? (
          <div className="p-6">
            <EmptyState
              title="No records matching filter"
              message="No inspections found matching the current search parameters."
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-900/80 text-xs uppercase font-semibold text-slate-400 border-b border-slate-700">
                <tr>
                  <th className="px-6 py-3.5">Commodity Details</th>
                  <th className="px-6 py-3.5">Inspection ID</th>
                  <th className="px-6 py-3.5">Timestamp</th>
                  <th className="px-6 py-3.5">Process Status</th>
                  <th className="px-6 py-3.5">Compliance Result</th>
                  <th className="px-6 py-3.5">Tamper Proof</th>
                  <th className="px-6 py-3.5 text-right">View</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/60">
                {filteredScans.map((scan) => (
                  <tr key={scan.id} className="hover:bg-slate-750/50 transition">
                    <td className="px-6 py-4">
                      <div className="font-bold text-white text-sm">
                        {scan.product_name || 'Unspecified Commodity'}
                      </div>
                      <div className="text-xs text-slate-400">{scan.brand_name || 'Generic'}</div>
                    </td>
                    <td className="px-6 py-4 font-mono text-xs text-slate-400">
                      {scan.id?.substring(0, 13)}...
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-400">
                      {scan.created_at ? new Date(scan.created_at).toLocaleString() : '—'}
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={scan.status} />
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={scan.final_compliance || scan.automated_compliance || 'needs_review'} />
                    </td>
                    <td className="px-6 py-4">
                      {scan.report_hash ? (
                        <span className="text-[11px] font-mono text-emerald-400">SHA-256 Sealed</span>
                      ) : (
                        <span className="text-xs text-slate-500">Unfinalized</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link
                        to={`/officer/inspections/${scan.id}`}
                        className="inline-flex items-center space-x-1 px-3 py-1.5 bg-slate-700/60 hover:bg-slate-700 text-indigo-300 hover:text-white rounded-lg text-xs font-semibold transition"
                      >
                        <span>Details</span>
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

export default InspectionHistory;
