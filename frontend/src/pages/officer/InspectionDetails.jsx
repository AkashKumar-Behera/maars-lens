import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { getScanResultApi, submitManualReviewApi, finalizeScanApi, listInspectionImagesApi } from '../../api/scans';
import { getProductHistoryApi } from '../../api/products';
import { createViolationApi } from '../../api/violations';
import { downloadReportPdfBlobApi, downloadReportDocxBlobApi, downloadReportXlsxBlobApi } from '../../api/reports';
import StatusBadge from '../../components/StatusBadge';
import {
  Shield,
  FileCheck2,
  AlertTriangle,
  FileText,
  Lock,
  Download,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Send,
  ArrowLeft,
  Stamp,
  History,
} from 'lucide-react';

const InspectionDetails = () => {
  const { id } = useParams();
  const { user } = useAuth();
  const role = user?.role || 'officer';
  const backPath = role === 'admin' ? '/admin/inspections' : role === 'retailer' ? '/retailer/inspections' : '/officer/inspections';

  const [inspection, setInspection] = useState(null);
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Manual review modal state
  const [selectedRule, setSelectedRule] = useState(null);
  const [reviewResult, setReviewResult] = useState('pass');
  const [reviewReason, setReviewReason] = useState('');
  const [submittingReview, setSubmittingReview] = useState(false);

  // Finalization state
  const [officerNotes, setOfficerNotes] = useState('');
  const [finalizing, setFinalizing] = useState(false);

  // Violation creation state
  const [showViolationModal, setShowViolationModal] = useState(false);
  const [violationSummary, setViolationSummary] = useState('');
  const [submittingViolation, setSubmittingViolation] = useState(false);

  // Product repeat scan history state
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [productHistory, setProductHistory] = useState(null);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const fetchProductHistory = async (productId) => {
    if (!productId) return;
    try {
      setLoadingHistory(true);
      setShowHistoryModal(true);
      const data = await getProductHistoryApi(productId);
      setProductHistory(data);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to fetch product history');
    } finally {
      setLoadingHistory(false);
    }
  };

  useEffect(() => {
    fetchInspection();
  }, [id]);

  const fetchInspection = async () => {
    try {
      setLoading(true);
      const data = await getScanResultApi(id);
      setInspection(data);
      try {
        const imgList = await listInspectionImagesApi(id);
        setImages(imgList || []);
      } catch (e) {
        // Soft fail on image listing if none exist
        setImages([]);
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load inspection details');
    } finally {
      setLoading(false);
    }
  };

  const handleReviewSubmit = async (e) => {
    e.preventDefault();
    if (!reviewReason.trim()) {
      alert('A justified reason is mandatory for manual review assessment.');
      return;
    }

    try {
      setSubmittingReview(true);
      await submitManualReviewApi(id, {
        rule_code: selectedRule.rule_code,
        manual_review_result: reviewResult,
        manual_review_reason: reviewReason.trim(),
      });
      setSelectedRule(null);
      setReviewReason('');
      await fetchInspection();
    } catch (err) {
      alert(err.response?.data?.detail || err.message || 'Failed to record manual review');
    } finally {
      setSubmittingReview(false);
    }
  };

  const handleFinalize = async () => {
    if (!confirm('Are you sure you want to finalize this inspection? Once finalized, it will be cryptographically locked with a SHA-256 seal and cannot be altered.')) {
      return;
    }

    try {
      setFinalizing(true);
      await finalizeScanApi(id, {
        officer_notes: officerNotes.trim() || undefined,
      });
      await fetchInspection();
    } catch (err) {
      alert(err.response?.data?.detail || err.message || 'Finalization failed');
    } finally {
      setFinalizing(false);
    }
  };

  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [downloadingDocx, setDownloadingDocx] = useState(false);
  const [downloadingXlsx, setDownloadingXlsx] = useState(false);

  const handleDownloadPdf = async () => {
    try {
      setDownloadingPdf(true);
      const blob = await downloadReportPdfBlobApi(id);
      const url = window.URL.createObjectURL(new Blob([blob], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `MAARS_Inspection_${id.substring(0, 8)}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert(err.response?.data?.detail || err.message || 'Failed to download official signed PDF');
    } finally {
      setDownloadingPdf(false);
    }
  };

  const handleDownloadDocx = async () => {
    try {
      setDownloadingDocx(true);
      const blob = await downloadReportDocxBlobApi(id);
      const url = window.URL.createObjectURL(new Blob([blob], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `MAARS_Inspection_${id.substring(0, 8)}.docx`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert(err.response?.data?.detail || err.message || 'Failed to download DOCX notice');
    } finally {
      setDownloadingDocx(false);
    }
  };

  const handleDownloadXlsx = async () => {
    try {
      setDownloadingXlsx(true);
      const blob = await downloadReportXlsxBlobApi(id);
      const url = window.URL.createObjectURL(new Blob([blob], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `MAARS_Inspection_${id.substring(0, 8)}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert(err.response?.data?.detail || err.message || 'Failed to download XLSX report');
    } finally {
      setDownloadingXlsx(false);
    }
  };

  const handleCreateViolation = async (e) => {
    e.preventDefault();
    if (!violationSummary.trim()) {
      alert('Please provide a statutory violation summary.');
      return;
    }

    const failedRules = (inspection.audit_results || [])
      .filter((ar) => ar.effective_result === 'fail')
      .map((ar) => ar.rule_code);

    if (failedRules.length === 0) {
      alert('No failing rules found for this inspection.');
      return;
    }

    try {
      setSubmittingViolation(true);
      await createViolationApi(id, {
        failing_rule_codes: failedRules,
        summary: violationSummary.trim(),
      });
      setShowViolationModal(false);
      alert('Statutory violation notice generated successfully.');
    } catch (err) {
      alert(err.response?.data?.detail || err.message || 'Failed to generate violation');
    } finally {
      setSubmittingViolation(false);
    }
  };

  if (loading) {
    return (
      <div className="p-12 text-center text-slate-400">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500 mb-3"></div>
        <p>Loading inspection telemetry & compliance audit...</p>
      </div>
    );
  }

  if (error || !inspection) {
    return (
      <div className="p-8 bg-rose-950/20 border border-rose-800 rounded-xl text-center text-rose-300">
        <AlertTriangle size={32} className="mx-auto mb-2 text-rose-400" />
        <p className="font-bold">{error || 'Inspection record not found'}</p>
        <Link to={backPath} className="mt-4 inline-block text-xs text-indigo-400 hover:underline">
          Return to inspection history
        </Link>
      </div>
    );
  }

  const auditResults = inspection.audit_results || [];
  const failingRules = auditResults.filter((ar) => ar.effective_result === 'fail');

  return (
    <div className="space-y-6">
      {/* Navigation & Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <Link
            to={backPath}
            className="inline-flex items-center space-x-1 text-xs text-slate-400 hover:text-white mb-2"
          >
            <ArrowLeft size={14} />
            <span>Back to Inspection Records</span>
          </Link>
          <div className="flex items-center space-x-3">
            <h1 className="text-2xl font-bold text-white tracking-tight">
              {inspection.product_name || 'Packaged Commodity'}
            </h1>
            <StatusBadge status={inspection.final_compliance || inspection.automated_compliance || 'needs_review'} />
            {inspection.is_finalized && (
              <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 bg-indigo-950 text-indigo-300 border border-indigo-700 text-xs font-semibold rounded-full">
                <Lock size={12} />
                <span>Finalized & Sealed</span>
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400 mt-1 font-mono">
            Inspection ID: {inspection.inspection_id}
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-2">
          {inspection.is_finalized && (
            <>
              <button
                onClick={handleDownloadPdf}
                disabled={downloadingPdf}
                className="inline-flex items-center space-x-2 px-3 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-600 text-slate-200 text-xs font-semibold rounded-lg shadow transition disabled:opacity-50"
              >
                <Download size={14} className={downloadingPdf ? 'animate-bounce' : ''} />
                <span>{downloadingPdf ? 'PDF...' : 'PDF'}</span>
              </button>
              <button
                onClick={handleDownloadDocx}
                disabled={downloadingDocx}
                className="inline-flex items-center space-x-2 px-3 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-600 text-slate-200 text-xs font-semibold rounded-lg shadow transition disabled:opacity-50"
              >
                <Download size={14} className={downloadingDocx ? 'animate-bounce' : ''} />
                <span>{downloadingDocx ? 'DOCX...' : 'DOCX'}</span>
              </button>
              <button
                onClick={handleDownloadXlsx}
                disabled={downloadingXlsx}
                className="inline-flex items-center space-x-2 px-3 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-600 text-slate-200 text-xs font-semibold rounded-lg shadow transition disabled:opacity-50"
              >
                <Download size={14} className={downloadingXlsx ? 'animate-bounce' : ''} />
                <span>{downloadingXlsx ? 'XLSX...' : 'XLSX'}</span>
              </button>
            </>
          )}

          {role !== 'retailer' && inspection.is_finalized && inspection.final_compliance === 'non_compliant' && (
            <button
              onClick={() => setShowViolationModal(true)}
              className="inline-flex items-center space-x-2 px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold rounded-lg shadow-md transition"
            >
              <AlertTriangle size={14} />
              <span>Issue Statutory Violation Notice</span>
            </button>
          )}

          {inspection.product_id && (
            <button
              onClick={() => fetchProductHistory(inspection.product_id)}
              className="inline-flex items-center space-x-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-600 text-indigo-300 text-xs font-semibold rounded-lg shadow transition"
            >
              <History size={14} />
              <span>Product History</span>
            </button>
          )}

          {!inspection.is_finalized && (
            <button
              onClick={handleFinalize}
              disabled={finalizing}
              className="inline-flex items-center space-x-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg shadow-md shadow-emerald-600/20 disabled:opacity-50 transition"
            >
              <Stamp size={14} />
              <span>{finalizing ? 'Sealing...' : 'Finalize & Sign Inspection'}</span>
            </button>
          )}
        </div>
      </div>

      {/* Tamper-evident Seal Card */}
      {inspection.report_hash && (
        <div className="bg-slate-950/80 border border-emerald-900/60 p-4 rounded-xl flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-emerald-950 rounded-lg text-emerald-400">
              <Shield size={20} />
            </div>
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-emerald-400">
                Cryptographic Integrity Verified
              </p>
              <p className="font-mono text-xs text-slate-300 break-all">{inspection.report_hash}</p>
            </div>
          </div>
          <span className="text-[10px] text-slate-500 hidden sm:inline">SHA-256 Tamper-Proof</span>
        </div>
      )}

      {/* Multi-Panel Evidence Images & Annotations */}
      {images && images.length > 0 && (
        <div className="bg-slate-800/90 border border-slate-700/80 rounded-xl p-6 shadow-lg space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-white flex items-center space-x-2">
              <FileCheck2 size={20} className="text-indigo-400" />
              <span>Inspection Evidence Images ({images.length} Panels)</span>
            </h2>
            <span className="text-xs text-slate-400">PaddleOCR polygon extraction & SHA-256 verified</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {images.map((img) => (
              <div key={img.id} className="bg-slate-900 border border-slate-700/80 rounded-lg overflow-hidden p-3 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-indigo-300 uppercase tracking-wider">{img.panel_type} Panel</span>
                  <span className="text-[10px] text-slate-400 font-mono">{(img.size / 1024).toFixed(1)} KB</span>
                </div>
                <div className="h-44 bg-slate-950 rounded flex items-center justify-center overflow-hidden border border-slate-800">
                  <img
                    src={`/uploads/${img.storage_path}`}
                    alt={`${img.panel_type} panel evidence`}
                    className="w-full h-full object-contain"
                    onError={(e) => {
                      e.target.onerror = null;
                      e.target.src = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 24 24" fill="none" stroke="%2364748b" stroke-width="2"><rect width="18" height="18" x="3" y="3" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg>';
                    }}
                  />
                </div>
                <p className="text-[10px] text-slate-500 font-mono truncate" title={img.sha256}>
                  SHA256: {img.sha256.substring(0, 16)}...
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Merged Package Facts & OCR Summary */}
      {inspection.extracted_facts && Object.keys(inspection.extracted_facts).length > 0 && (
        <div className="bg-slate-800/90 border border-slate-700/80 rounded-xl p-6 shadow-lg space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-white flex items-center space-x-2">
              <FileText size={20} className="text-indigo-400" />
              <span>Extracted Package Declarations (Unified Facts)</span>
            </h2>
            {inspection.ocr_confidence_overall && (
              <span className="text-xs px-2.5 py-1 bg-indigo-950 text-indigo-300 border border-indigo-700 rounded-full font-semibold">
                Confidence: {(inspection.ocr_confidence_overall * 100).toFixed(1)}%
              </span>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 text-xs">
            {Object.entries(inspection.extracted_facts).filter(([k]) => !k.startsWith('_')).map(([key, val]) => (
              <div key={key} className="p-3 bg-slate-900/80 border border-slate-700/60 rounded-lg">
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-0.5">
                  {key.replace(/_/g, ' ')}
                </span>
                <span className="font-semibold text-slate-200 break-words">
                  {typeof val === 'object' ? JSON.stringify(val) : String(val)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Rules Evaluation Table */}
      <div className="bg-slate-800/90 border border-slate-700/80 rounded-xl overflow-hidden shadow-lg">
        <div className="px-6 py-4 border-b border-slate-700">
          <h2 className="text-base font-bold text-white">Statutory Rule Evaluations</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Evaluated by the Legal Metrology compliance engine against Packaged Commodities Rules.
          </p>
        </div>

        {auditResults.length === 0 ? (
          <div className="p-8 text-center text-slate-400 text-sm">
            No compliance rules evaluated for this scan yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-900/80 text-xs uppercase font-semibold text-slate-400 border-b border-slate-700">
                <tr>
                  <th className="px-6 py-3">Rule Code</th>
                  <th className="px-6 py-3">Statutory Citation</th>
                  <th className="px-6 py-3">Automated Verdict</th>
                  <th className="px-6 py-3">Officer Review</th>
                  <th className="px-6 py-3">Effective Result</th>
                  <th className="px-6 py-3 text-right">Review Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/60">
                {auditResults.map((ar) => (
                  <tr key={ar.id} className="hover:bg-slate-750/50 transition">
                    <td className="px-6 py-4 font-mono font-bold text-xs text-white">
                      {ar.rule_code}
                      <span className="block text-[10px] font-normal text-slate-400">v{ar.rule_version}</span>
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-300 max-w-xs">
                      {ar.statutory_reference}
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={ar.automated_result} />
                    </td>
                    <td className="px-6 py-4">
                      {ar.manual_review_result ? (
                        <div>
                          <StatusBadge status={ar.manual_review_result} />
                          {ar.manual_review_reason && (
                            <p className="text-[11px] text-slate-400 italic mt-1 max-w-xs">
                              "{ar.manual_review_reason}"
                            </p>
                          )}
                        </div>
                      ) : (
                        <span className="text-xs text-slate-500">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={ar.effective_result} />
                    </td>
                    <td className="px-6 py-4 text-right">
                      {role === 'retailer' ? (
                        <span className="text-xs text-slate-500">Audited Record</span>
                      ) : !inspection.is_finalized ? (
                        <button
                          onClick={() => {
                            setSelectedRule(ar);
                            setReviewResult(ar.effective_result === 'pass' ? 'fail' : 'pass');
                          }}
                          className="px-3 py-1.5 bg-indigo-600/80 hover:bg-indigo-600 text-white text-xs font-semibold rounded-lg transition"
                        >
                          Manual Assessment
                        </button>
                      ) : (
                        <span className="text-xs text-slate-500">Locked</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Manual Review Modal */}
      {selectedRule && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-800 border border-slate-700 rounded-xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <h3 className="text-lg font-bold text-white">
              Manual Officer Review: {selectedRule.rule_code}
            </h3>
            <p className="text-xs text-slate-300">
              {selectedRule.statutory_reference}
            </p>

            <form onSubmit={handleReviewSubmit} className="space-y-4 pt-2">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
                  Officer Verdict
                </label>
                <div className="flex space-x-4">
                  <label className="flex items-center space-x-2 text-sm text-slate-200 cursor-pointer">
                    <input
                      type="radio"
                      name="verdict"
                      value="pass"
                      checked={reviewResult === 'pass'}
                      onChange={(e) => setReviewResult(e.target.value)}
                      className="text-indigo-600"
                    />
                    <span>Pass (Compliant)</span>
                  </label>
                  <label className="flex items-center space-x-2 text-sm text-slate-200 cursor-pointer">
                    <input
                      type="radio"
                      name="verdict"
                      value="fail"
                      checked={reviewResult === 'fail'}
                      onChange={(e) => setReviewResult(e.target.value)}
                      className="text-indigo-600"
                    />
                    <span>Fail (Non-Compliant)</span>
                  </label>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
                  Mandatory Statutory Justification Note
                </label>
                <textarea
                  value={reviewReason}
                  onChange={(e) => setReviewReason(e.target.value)}
                  placeholder="State factual examination evidence (e.g. physical packaging inspection confirmed absence of MRP declaration)..."
                  rows={4}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  required
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setSelectedRule(null)}
                  className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 text-xs font-semibold rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingReview}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg disabled:opacity-50"
                >
                  {submittingReview ? 'Submitting...' : 'Save Assessment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Violation Creation Modal */}
      {showViolationModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-800 border border-slate-700 rounded-xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <h3 className="text-lg font-bold text-white flex items-center space-x-2 text-rose-400">
              <AlertTriangle size={20} />
              <span>Issue Legal Metrology Violation Notice</span>
            </h3>

            <p className="text-xs text-slate-300">
              Generates a formal legal infraction under Section 36 of the Legal Metrology Act, 2009.
            </p>

            <form onSubmit={handleCreateViolation} className="space-y-4 pt-2">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
                  Failing Rule Codes
                </label>
                <div className="p-2 bg-slate-900 border border-slate-700 rounded-lg text-xs font-mono text-rose-300">
                  {failingRules.map((r) => r.rule_code).join(', ')}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
                  Violation Summary & Allegation Text
                </label>
                <textarea
                  value={violationSummary}
                  onChange={(e) => setViolationSummary(e.target.value)}
                  placeholder="Specify violation summary (e.g. Absence of mandatory Maximum Retail Price declaration on principal display panel)..."
                  rows={4}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-rose-500"
                  required
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowViolationModal(false)}
                  className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 text-xs font-semibold rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingViolation}
                  className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold rounded-lg disabled:opacity-50"
                >
                  {submittingViolation ? 'Issuing Notice...' : 'Issue Statutory Notice'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Product Repeat Scan History Modal */}
      {showHistoryModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-800 border border-slate-700 rounded-xl max-w-2xl w-full p-6 shadow-2xl space-y-4 max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between border-b border-slate-700 pb-3">
              <h3 className="text-base font-bold text-white flex items-center space-x-2">
                <History size={18} className="text-indigo-400" />
                <span>Product Compliance History</span>
              </h3>
              <button
                onClick={() => setShowHistoryModal(false)}
                className="text-slate-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            {loadingHistory ? (
              <div className="py-12 text-center text-slate-400 text-sm">
                Loading repeat inspection history...
              </div>
            ) : productHistory ? (
              <div className="space-y-4 overflow-y-auto pr-1">
                <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-700/60 text-xs grid grid-cols-2 gap-2">
                  <div>
                    <span className="text-slate-400">Brand:</span>{' '}
                    <span className="font-semibold text-white">{productHistory.brand_name || 'N/A'}</span>
                  </div>
                  <div>
                    <span className="text-slate-400">Product:</span>{' '}
                    <span className="font-semibold text-white">{productHistory.product_name || 'N/A'}</span>
                  </div>
                  <div>
                    <span className="text-slate-400">Barcode:</span>{' '}
                    <span className="font-mono text-indigo-300">{productHistory.barcode || 'N/A'}</span>
                  </div>
                  <div>
                    <span className="text-slate-400">Total Scans:</span>{' '}
                    <span className="font-bold text-white">{productHistory.total_inspections}</span>
                  </div>
                </div>

                <div className="space-y-2">
                  <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                    Past Inspection Records & Verdicts
                  </h4>
                  {productHistory.inspections?.length === 0 ? (
                    <p className="text-xs text-slate-400">No prior inspections found.</p>
                  ) : (
                    <div className="space-y-2">
                      {productHistory.inspections.map((item) => (
                        <div
                          key={item.inspection_id}
                          className="bg-slate-900 border border-slate-700/70 rounded-lg p-3 flex items-center justify-between text-xs"
                        >
                          <div className="space-y-1">
                            <div className="flex items-center space-x-2">
                              <span className="font-mono text-slate-300">
                                {item.inspection_id.substring(0, 8)}...
                              </span>
                              <span className="text-[10px] text-slate-500">
                                {new Date(item.created_at).toLocaleDateString()}
                              </span>
                            </div>
                            <div className="text-[10px] text-slate-400">
                              Status: <span className="text-slate-300">{item.status}</span>
                            </div>
                          </div>
                          <div className="flex items-center space-x-2">
                            <StatusBadge
                              status={item.final_compliance || item.automated_compliance || 'needs_review'}
                            />
                            {item.is_finalized && (
                              <span className="px-1.5 py-0.5 bg-indigo-950 text-indigo-300 border border-indigo-700 rounded text-[10px]">
                                Sealed
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <p className="text-xs text-slate-400">No record available.</p>
            )}

            <div className="flex justify-end pt-2 border-t border-slate-700">
              <button
                type="button"
                onClick={() => setShowHistoryModal(false)}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs font-semibold rounded-lg"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default InspectionDetails;
