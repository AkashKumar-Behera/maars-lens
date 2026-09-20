import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  AlertTriangle, CheckCircle2, RefreshCw, Eye, ShieldAlert, FileText, Check, Clock 
} from 'lucide-react';
import { listScansApi } from '../../api/scans';
import { getViolationApi, updateViolationStatusApi } from '../../api/violations';
import StatusBadge from '../../components/StatusBadge';

export default function ViolationsList() {
  const [violations, setViolations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Transition modal state
  const [selectedViolation, setSelectedViolation] = useState(null);
  const [newStatus, setNewStatus] = useState('resolved');
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [transitionLoading, setTransitionLoading] = useState(false);
  const [modalError, setModalError] = useState(null);

  const fetchViolations = async () => {
    try {
      setLoading(true);
      setError(null);
      // Fetch inspections and find finalized non-compliant records that have violation files
      const scans = await listScansApi();
      const nonCompliantScans = scans.filter(s => s.is_finalized && (s.final_compliance === 'non_compliant' || s.automated_compliance === 'non_compliant'));
      
      // Fetch violation records for each non-compliant scan
      const violationPromises = nonCompliantScans.map(async (s) => {
        try {
          const v = await getViolationApi(s.id);
          return { ...v, scan: s };
        } catch {
          return null;
        }
      });

      const results = (await Promise.all(violationPromises)).filter(Boolean);
      setViolations(results);
    } catch (err) {
      console.error('Failed to load violations:', err);
      setError('Unable to load statutory violation docket.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchViolations();
  }, []);

  const handleOpenStatusModal = (v) => {
    setSelectedViolation(v);
    setNewStatus(v.status === 'open' ? 'resolved' : 'dismissed');
    setResolutionNotes('');
    setModalError(null);
  };

  const handleUpdateStatus = async (e) => {
    e.preventDefault();
    if (!resolutionNotes.trim()) {
      setModalError('Resolution rationale notes are strictly mandatory per statutory compliance requirements.');
      return;
    }

    try {
      setTransitionLoading(true);
      setModalError(null);
      const updated = await updateViolationStatusApi(selectedViolation.inspection_id, {
        status: newStatus,
        resolution_notes: resolutionNotes.trim()
      });

      // Update state
      setViolations(prev => prev.map(item => 
        item.inspection_id === selectedViolation.inspection_id 
          ? { ...item, ...updated } 
          : item
      ));

      setSelectedViolation(null);
    } catch (err) {
      console.error('Failed to update violation status:', err);
      setModalError(err.response?.data?.detail || 'Failed to update breach disposition.');
    } finally {
      setTransitionLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <ShieldAlert className="h-6 w-6 text-red-400" />
            Statutory Breach Docket
          </h1>
          <p className="text-sm text-brand-muted">
            Formal Legal Metrology breach proceedings, show-cause actions, and penalty adjudications.
          </p>
        </div>
        <button
          onClick={fetchViolations}
          disabled={loading}
          className="px-3 py-2 rounded-lg bg-surface-card border border-surface-border hover:bg-surface-border text-brand-muted hover:text-white transition flex items-center gap-2 text-sm w-fit"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh Docket
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm flex items-center gap-3">
          <AlertTriangle className="h-5 w-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Violations Table */}
      <div className="bg-surface-card border border-surface-border rounded-xl overflow-hidden shadow-sm">
        {loading ? (
          <div className="p-12 text-center text-brand-muted text-sm animate-pulse">
            Querying statutory violations repository...
          </div>
        ) : violations.length === 0 ? (
          <div className="p-12 text-center text-brand-muted text-sm flex flex-col items-center">
            <CheckCircle2 className="h-10 w-10 text-emerald-400 mb-2" />
            <span className="font-semibold text-white">No active statutory violations recorded.</span>
            <span className="text-xs text-brand-muted mt-1">All audited packaged commodities comply with prevailing declarations.</span>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="border-b border-surface-border bg-surface-dark/50 text-xs font-semibold text-brand-muted uppercase tracking-wider">
                  <th className="py-3 px-4">Breach ID & Commodity</th>
                  <th className="py-3 px-4">Severity / Fine</th>
                  <th className="py-3 px-4">Adjudication Status</th>
                  <th className="py-3 px-4">Issuance Date</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-border">
                {violations.map((v) => (
                  <tr key={v.id} className="hover:bg-surface-dark/30 transition">
                    <td className="py-3 px-4">
                      <div className="font-medium text-white">
                        {v.scan?.product_name || 'Packaged Commodity'}
                      </div>
                      <div className="text-xs font-mono text-brand-muted">
                        Inspection: {v.inspection_id.substring(0, 8)}...
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <span className={`inline-block px-2 py-0.5 rounded text-xs font-semibold uppercase ${
                          v.severity === 'critical' ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                          v.severity === 'major' ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30' :
                          'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                        }`}>
                          {v.severity}
                        </span>
                        {v.penalty_amount != null && (
                          <span className="text-xs font-medium text-white">
                            ₹{v.penalty_amount.toLocaleString()}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={v.status} />
                    </td>
                    <td className="py-3 px-4 text-xs text-brand-muted">
                      {v.created_at ? new Date(v.created_at).toLocaleDateString() : '—'}
                    </td>
                    <td className="py-3 px-4 text-right space-x-2">
                      <button
                        onClick={() => handleOpenStatusModal(v)}
                        className="px-2.5 py-1 rounded text-xs font-medium bg-surface-dark border border-surface-border text-brand-muted hover:text-white transition"
                      >
                        Update Status
                      </button>
                      <Link
                        to={`/officer/inspections/${v.inspection_id}`}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs font-medium bg-brand-blue/10 border border-brand-blue/30 text-brand-blue hover:bg-brand-blue/20 transition"
                      >
                        <Eye className="h-3 w-3" /> Audit
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Status Update Modal */}
      {selectedViolation && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-surface-card border border-surface-border rounded-xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-surface-border">
              <h3 className="font-semibold text-white flex items-center gap-2">
                <ShieldAlert className="h-5 w-5 text-red-400" />
                Update Breach Disposition
              </h3>
              <button 
                onClick={() => setSelectedViolation(null)}
                className="text-brand-muted hover:text-white text-lg font-bold"
              >
                &times;
              </button>
            </div>

            {modalError && (
              <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-xs">
                {modalError}
              </div>
            )}

            <form onSubmit={handleUpdateStatus} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-brand-muted mb-1">Target Disposition Status</label>
                <select
                  value={newStatus}
                  onChange={(e) => setNewStatus(e.target.value)}
                  className="w-full bg-surface-dark border border-surface-border rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-blue"
                >
                  <option value="resolved">Resolved (Penalty paid / rectified)</option>
                  <option value="dismissed">Dismissed (Legal challenge accepted / erroneous)</option>
                  <option value="appealed">Under Appellate Review</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-brand-muted mb-1">
                  Mandatory Statutory Rationale Notes <span className="text-red-400">*</span>
                </label>
                <textarea
                  rows="3"
                  required
                  placeholder="Record formal justification, challan reference, compounding fee receipt, or court order details..."
                  value={resolutionNotes}
                  onChange={(e) => setResolutionNotes(e.target.value)}
                  className="w-full bg-surface-dark border border-surface-border rounded-lg p-3 text-xs text-white placeholder-brand-muted focus:outline-none focus:border-brand-blue resize-none"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-surface-border">
                <button
                  type="button"
                  onClick={() => setSelectedViolation(null)}
                  className="px-4 py-2 rounded-lg text-xs font-medium text-brand-muted hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={transitionLoading}
                  className="px-4 py-2 rounded-lg text-xs font-semibold bg-brand-blue hover:bg-blue-600 text-white transition disabled:opacity-50"
                >
                  {transitionLoading ? 'Saving...' : 'Confirm Disposition'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
