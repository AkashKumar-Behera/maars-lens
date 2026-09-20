import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import StatusBadge from '../../components/StatusBadge';
import EmptyState from '../../components/EmptyState';
import {
  listOfficerIncidentsApi,
  sendOfficerInquiryApi,
  escalateIncidentToAdminApi,
} from '../../api/inquiries';
import { listScansApi } from '../../api/scans';
import {
  Camera,
  ClipboardList,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ArrowRight,
  ShieldCheck,
  Search,
  MapPin,
  Send,
  AlertCircle,
  FileCheck2,
  ChevronRight,
  RefreshCw,
  X,
} from 'lucide-react';

const OfficerDashboard = () => {
  const [activeTab, setActiveTab] = useState('incidents'); // 'incidents' | 'scans'
  const [incidents, setIncidents] = useState([]);
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedIncident, setSelectedIncident] = useState(null);

  // Notice Dispatch Modal State
  const [noticeModalOpen, setNoticeModalOpen] = useState(false);
  const [noticeText, setNoticeText] = useState('');
  const [dispatchingNotice, setDispatchingNotice] = useState(false);

  // Escalation Modal State
  const [escalateModalOpen, setEscalateModalOpen] = useState(false);
  const [escalateReason, setEscalateReason] = useState('');
  const [escalating, setEscalating] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [incData, scanData] = await Promise.all([
        listOfficerIncidentsApi(),
        listScansApi(),
      ]);
      setIncidents(Array.isArray(incData) ? incData : []);
      setScans(Array.isArray(scanData) ? scanData : []);
    } catch (err) {
      console.error('Failed to load officer dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenNoticeModal = (inc) => {
    setSelectedIncident(inc);
    setNoticeText(
      `SHOW-CAUSE STATUTORY NOTICE: Non-compliant commodity [${inc.product_name || 'Packaged Commodity'}] reported at your store premises. Missing/Failing rules: ${(inc.failing_rule_codes || []).join(', ')}. Please provide genuine supplier/wholesaler invoice and origin details within 48 hours.`
    );
    setNoticeModalOpen(true);
  };

  const handleSendNotice = async () => {
    if (!selectedIncident) return;
    setDispatchingNotice(true);
    try {
      await sendOfficerInquiryApi({
        report_id: selectedIncident.id,
        inquiry_notice_text: noticeText,
      });
      alert('Show-cause inquiry notice successfully pushed to retailer.');
      setNoticeModalOpen(false);
      loadData();
    } catch (err) {
      alert('Failed to send notice: ' + (err.response?.data?.detail || err.message));
    } finally {
      setDispatchingNotice(false);
    }
  };

  const handleOpenEscalateModal = (inc) => {
    setSelectedIncident(inc);
    setEscalateReason(
      `Retailer failed to submit genuine wholesaler credentials or commodity contains counterfeit statutory declarations. Escalating for National Metrology seizure and Section 36 proceedings.`
    );
    setEscalateModalOpen(true);
  };

  const handleEscalateToAdmin = async () => {
    if (!selectedIncident) return;
    setEscalating(true);
    try {
      await escalateIncidentToAdminApi(selectedIncident.id, escalateReason);
      alert('Incident escalated to National Administrator for statutory legal enforcement.');
      setEscalateModalOpen(false);
      loadData();
    } catch (err) {
      alert('Failed to escalate: ' + (err.response?.data?.detail || err.message));
    } finally {
      setEscalating(false);
    }
  };

  const totalIncidents = incidents.length;
  const pendingInquiries = incidents.filter((i) => i.status === 'submitted').length;
  const retailerResponses = incidents.filter((i) => i.status === 'retailer_responded').length;
  const escalatedCount = incidents.filter((i) => i.escalated_to_admin).length;

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-indigo-950/90 via-slate-900 to-slate-900 border border-indigo-800/40 p-6 rounded-2xl shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-indigo-400 text-xs font-bold uppercase tracking-wider mb-1">
            <ShieldCheck size={16} />
            <span>Legal Metrology Field Enforcement & Radar Console</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Officer Enforcement Dashboard</h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Geospatial surveillance, citizen incident dispatch, retailer show-cause inquiries, and statutory inspections.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={loadData}
            className="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition border border-slate-700 shadow"
            title="Refresh Feed"
          >
            <RefreshCw size={16} />
          </button>
          <Link
            to="/officer/new-inspection"
            className="inline-flex items-center space-x-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs sm:text-sm font-semibold rounded-xl shadow-lg shadow-indigo-600/30 transition"
          >
            <Camera size={18} />
            <span>Spot Package Inspection</span>
          </Link>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-xl shadow">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
            <span>Live Geo Incidents</span>
            <AlertTriangle size={18} className="text-rose-400" />
          </div>
          <p className="text-2xl sm:text-3xl font-extrabold text-white mt-2">{loading ? '...' : totalIncidents}</p>
          <p className="text-xs text-rose-400 mt-1">{pendingInquiries} awaiting officer action</p>
        </div>

        <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-xl shadow">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
            <span>Retailer Explanations</span>
            <FileCheck2 size={18} className="text-amber-400" />
          </div>
          <p className="text-2xl sm:text-3xl font-extrabold text-white mt-2">{loading ? '...' : retailerResponses}</p>
          <p className="text-xs text-amber-400 mt-1">Supplier proofs submitted</p>
        </div>

        <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-xl shadow">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
            <span>Admin Escalations</span>
            <ShieldCheck size={18} className="text-indigo-400" />
          </div>
          <p className="text-2xl sm:text-3xl font-extrabold text-white mt-2">{loading ? '...' : escalatedCount}</p>
          <p className="text-xs text-slate-400 mt-1">Legal sanction requested</p>
        </div>

        <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-xl shadow">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
            <span>Total Official Scans</span>
            <ClipboardList size={18} className="text-emerald-400" />
          </div>
          <p className="text-2xl sm:text-3xl font-extrabold text-white mt-2">{loading ? '...' : scans.length}</p>
          <p className="text-xs text-emerald-400 mt-1">Audit certificates generated</p>
        </div>
      </div>

      {/* Main Tabs Navigation */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab('incidents')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 ${
            activeTab === 'incidents'
              ? 'bg-indigo-600 text-white shadow-md'
              : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
          }`}
        >
          <AlertCircle size={15} />
          <span>Citizen Geo-Incidents & Notice Dispatch ({incidents.length})</span>
        </button>
        <button
          onClick={() => setActiveTab('scans')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 ${
            activeTab === 'scans'
              ? 'bg-indigo-600 text-white shadow-md'
              : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
          }`}
        >
          <ClipboardList size={15} />
          <span>Official Inspection Archive ({scans.length})</span>
        </button>
      </div>

      {/* Tab 1: Citizen Incidents Queue */}
      {activeTab === 'incidents' && (
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <div>
              <h3 className="text-sm sm:text-base font-bold text-white">Live Incident Feed (Citizen Reports)</h3>
              <p className="text-xs text-slate-400">
                Products flagged for LMPC 2011 statutory non-compliance with tagged GPS coordinates & retail establishments.
              </p>
            </div>
          </div>

          {incidents.length === 0 ? (
            <EmptyState
              title="No active citizen incidents reported"
              description="New product non-compliance reports from citizens will appear here in real-time."
            />
          ) : (
            <div className="space-y-3">
              {incidents.map((inc) => {
                const hasRetailerResponse = inc.status === 'retailer_responded';
                const isNoticeSent = inc.status === 'inquiry_sent';
                const isEscalated = inc.escalated_to_admin;

                return (
                  <div
                    key={inc.id}
                    className="p-4 rounded-xl bg-slate-950 border border-slate-800/90 hover:border-slate-700 transition space-y-3"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-bold text-white">
                            {inc.product_name || 'Packaged Commodity'}
                          </span>
                          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold uppercase bg-slate-800 text-slate-300 border border-slate-700">
                            {inc.status}
                          </span>
                          {isEscalated && (
                            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold uppercase bg-amber-500/20 text-amber-300 border border-amber-500/40">
                              Escalated to Admin
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-slate-400 leading-snug">{inc.description}</p>
                        <div className="flex flex-wrap items-center gap-3 pt-1 text-[11px] text-slate-400 font-mono">
                          <span className="flex items-center gap-1 text-slate-300">
                            <MapPin size={12} className="text-rose-400" />
                            <span>Store: {inc.retailer_name} ({inc.retailer_address})</span>
                          </span>
                          <span>GPS: {inc.gps_lat?.toFixed(4)}, {inc.gps_lng?.toFixed(4)}</span>
                          <span>Reported: {inc.created_at ? new Date(inc.created_at).toLocaleString() : 'Recent'}</span>
                        </div>
                      </div>

                      {/* Action Buttons */}
                      <div className="flex items-center gap-2 shrink-0">
                        {inc.status === 'submitted' && (
                          <button
                            onClick={() => handleOpenNoticeModal(inc)}
                            className="px-3 py-1.5 bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold rounded-lg transition shadow flex items-center gap-1.5"
                          >
                            <Send size={13} />
                            <span>Push Notice to Retailer</span>
                          </button>
                        )}

                        {(hasRetailerResponse || isNoticeSent) && !isEscalated && (
                          <button
                            onClick={() => handleOpenEscalateModal(inc)}
                            className="px-3 py-1.5 bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold rounded-lg transition shadow flex items-center gap-1.5"
                          >
                            <AlertTriangle size={13} />
                            <span>Escalate to Admin</span>
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Failing Rules Badges */}
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {(inc.failing_rule_codes || []).map((code) => (
                        <span
                          key={code}
                          className="px-2 py-0.5 rounded bg-rose-950/60 border border-rose-900/60 text-rose-300 text-[10px] font-mono"
                        >
                          Violation: {code}
                        </span>
                      ))}
                    </div>

                    {/* Retailer Supplier Explanation & Traceability Details */}
                    {hasRetailerResponse && (
                      <div className="p-3 rounded-lg bg-indigo-950/30 border border-indigo-900/50 space-y-1.5 text-xs">
                        <div className="flex items-center justify-between text-indigo-300 font-semibold text-[11px] uppercase tracking-wider">
                          <span>✓ Retailer Supplier Traceability Submission</span>
                          <span>Invoice: {inc.supplier_invoice_no || 'Attached'}</span>
                        </div>
                        <p className="text-slate-200">
                          <strong className="text-slate-400">Supplier/Distributor:</strong> {inc.supplier_name} ({inc.supplier_contact})
                        </p>
                        <p className="text-slate-300 italic">
                          "{inc.retailer_explanation}"
                        </p>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Scans Table */}
      {activeTab === 'scans' && (
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-xl">
          <h3 className="text-sm sm:text-base font-bold text-white mb-3">Official Inspection Archive</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-950 text-xs uppercase font-semibold text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="px-5 py-3">Product Name</th>
                  <th className="px-5 py-3">Brand</th>
                  <th className="px-5 py-3">Inspection ID</th>
                  <th className="px-5 py-3">Date</th>
                  <th className="px-5 py-3">Compliance</th>
                  <th className="px-5 py-3 text-right">Certificate</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {scans.slice(0, 10).map((scan) => (
                  <tr key={scan.id} className="hover:bg-slate-800/40 transition">
                    <td className="px-5 py-3.5 font-medium text-white">
                      {scan.product_name || 'Packaged Commodity'}
                    </td>
                    <td className="px-5 py-3.5 text-slate-300">{scan.brand_name || '—'}</td>
                    <td className="px-5 py-3.5 font-mono text-xs text-slate-400">
                      {scan.id?.substring(0, 8)}...
                    </td>
                    <td className="px-5 py-3.5 text-xs text-slate-400">
                      {scan.created_at ? new Date(scan.created_at).toLocaleString() : '—'}
                    </td>
                    <td className="px-5 py-3.5">
                      <StatusBadge status={scan.final_compliance || scan.automated_compliance || 'needs_review'} />
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <Link
                        to={`/officer/inspections/${scan.id}`}
                        className="inline-flex items-center space-x-1 text-xs text-indigo-400 hover:text-indigo-300 font-semibold"
                      >
                        <span>View Certificate</span>
                        <ArrowRight size={13} />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Notice Dispatch Modal */}
      {noticeModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-[#0f172a] border border-slate-700 rounded-2xl w-full max-w-lg p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2 text-rose-400">
                <Send size={18} />
                <h3 className="text-base font-bold text-white">Push Statutory Show-Cause Notice</h3>
              </div>
              <button
                onClick={() => setNoticeModalOpen(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg"
              >
                <X size={18} />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <p className="text-slate-300">
                This notice will be immediately dispatched to <strong>{selectedIncident?.retailer_name}</strong>. The retailer will be required to submit wholesale distributor credentials and purchase invoice.
              </p>
              <div>
                <label className="block text-slate-300 font-semibold mb-1">Notice Order Text:</label>
                <textarea
                  rows={4}
                  value={noticeText}
                  onChange={(e) => setNoticeText(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-slate-800">
              <button
                onClick={() => setNoticeModalOpen(false)}
                className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={handleSendNotice}
                disabled={dispatchingNotice}
                className="px-5 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold flex items-center gap-1.5 disabled:opacity-50"
              >
                {dispatchingNotice ? <RefreshCw size={14} className="animate-spin" /> : <Send size={14} />}
                <span>{dispatchingNotice ? 'Dispatching...' : 'Dispatch Notice'}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Escalation to Admin Modal */}
      {escalateModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-[#0f172a] border border-slate-700 rounded-2xl w-full max-w-lg p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2 text-amber-400">
                <AlertTriangle size={18} />
                <h3 className="text-base font-bold text-white">Escalate Incident to National Admin</h3>
              </div>
              <button
                onClick={() => setEscalateModalOpen(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg"
              >
                <X size={18} />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <p className="text-slate-300">
                Escalates this matter to the National Legal Metrology Directorate for formal sanction under Section 36 (Penalties for non-standard packages) or court prosecution.
              </p>
              <div>
                <label className="block text-slate-300 font-semibold mb-1">Reason for Escalation:</label>
                <textarea
                  rows={4}
                  value={escalateReason}
                  onChange={(e) => setEscalateReason(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-slate-200 focus:outline-none focus:border-amber-500"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-slate-800">
              <button
                onClick={() => setEscalateModalOpen(false)}
                className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={handleEscalateToAdmin}
                disabled={escalating}
                className="px-5 py-2 rounded-xl bg-amber-600 hover:bg-amber-500 text-white text-xs font-bold flex items-center gap-1.5 disabled:opacity-50"
              >
                {escalating ? <RefreshCw size={14} className="animate-spin" /> : <AlertTriangle size={14} />}
                <span>{escalating ? 'Escalating...' : 'Confirm Escalation'}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default OfficerDashboard;
