import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Shield,
  BookOpen,
  AlertCircle,
  CheckCircle2,
  AlertTriangle,
  Camera,
  Search,
  Check,
  XCircle,
  FileCheck,
  ChevronRight,
  Info,
  RefreshCw,
} from 'lucide-react';
import { listRulesApi } from '../../api/rules';
import { customerScanLabelApi } from '../../api/customer';
import ImageUpload from '../../components/ImageUpload';
import StatusBadge from '../../components/StatusBadge';

export default function CustomerPortal() {
  const [rules, setRules] = useState([]);
  const [loadingRules, setLoadingRules] = useState(true);

  // Scan state
  const [selectedFile, setSelectedFile] = useState(null);
  const [panelType, setPanelType] = useState('front');
  const [scanning, setScanning] = useState(false);
  const [scanError, setScanError] = useState(null);
  const [scanResult, setScanResult] = useState(null);

  useEffect(() => {
    listRulesApi()
      .then((data) => {
        const rulesList = Array.isArray(data) ? data : data?.rules || [];
        setRules(rulesList);
      })
      .catch((err) => {
        console.error('Failed to load rules for consumer portal:', err);
        setRules([]);
      })
      .finally(() => setLoadingRules(false));
  }, []);

  const handleImageSelected = (file) => {
    setSelectedFile(file);
    setScanError(null);
  };

  const handleStartScan = async () => {
    if (!selectedFile) {
      setScanError('Please select a product image.');
      return;
    }

    // Client-side file validations
    const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
    if (!validTypes.includes(selectedFile.type) && !selectedFile.name.match(/\.(jpe?g|png|webp)$/i)) {
      setScanError('Unsupported file format. Please upload a JPG, PNG, or WebP image.');
      return;
    }

    if (selectedFile.size > 15 * 1024 * 1024) {
      setScanError('Image file is too large. Maximum supported file size is 15MB.');
      return;
    }

    setScanning(true);
    setScanError(null);
    setScanResult(null);

    try {
      const result = await customerScanLabelApi(selectedFile, panelType);
      setScanResult(result);
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (detail) {
        setScanError(detail);
      } else if (err.code === 'ECONNABORTED' || !err.response) {
        setScanError('Backend verification service is currently unreachable. Please check your network connection or try again.');
      } else {
        setScanError('Failed to analyze product label. Please try again with a clearer image.');
      }
    } finally {
      setScanning(false);
    }
  };

  const handleResetScan = () => {
    setSelectedFile(null);
    setScanResult(null);
    setScanError(null);
  };

  return (
    <div className="space-y-8 max-w-4xl mx-auto pb-12">
      {/* Header Banner */}
      <div className="text-center py-4">
        <span className="inline-block p-3 rounded-2xl bg-indigo-500/10 text-indigo-400 mb-3">
          <Shield className="h-8 w-8" />
        </span>
        <h1 className="text-3xl font-bold text-white tracking-tight">
          Citizen Consumer Protection Portal
        </h1>
        <p className="text-sm text-slate-400 mt-2 max-w-lg mx-auto">
          Scan any packaged commodity label in real-time to extract declarations and verify Legal Metrology compliance.
        </p>
      </div>

      {/* Main Scan Section */}
      <div className="bg-slate-800/90 border border-slate-700/80 rounded-2xl p-6 shadow-xl space-y-6">
        <div className="flex items-center justify-between border-b border-slate-700/80 pb-4">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center space-x-2">
              <Camera className="text-indigo-400" size={22} />
              <span>Verify Packaged Commodity Label</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Select or take a photo of the product package display panel to run automated Legal Metrology audit
            </p>
          </div>
          {scanResult && (
            <button
              onClick={handleResetScan}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs font-semibold rounded-lg transition"
            >
              <RefreshCw size={13} />
              <span>Scan Another Item</span>
            </button>
          )}
        </div>

        {/* Error Alert */}
        {scanError && (
          <div className="p-4 bg-rose-950/60 border border-rose-800/80 rounded-xl text-rose-300 text-sm flex items-start space-x-2.5 shadow-md">
            <AlertCircle size={18} className="shrink-0 mt-0.5 text-rose-400" />
            <div className="flex-1 text-xs leading-relaxed font-medium">
              {scanError}
            </div>
          </div>
        )}

        {/* Upload and Panel Selector */}
        {!scanResult && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 items-center">
              <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Display Panel Type:
              </label>
              <div className="sm:col-span-2">
                <select
                  value={panelType}
                  onChange={(e) => setPanelType(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                >
                  <option value="front">Principal Display Panel (Front)</option>
                  <option value="back">Information / Back Panel</option>
                  <option value="side">Side Panel (Nutritional & Net Qty)</option>
                  <option value="top">Top / Bottom (MRP & Date)</option>
                  <option value="other">General Commodity Panel</option>
                </select>
              </div>
            </div>

            <ImageUpload
              onUpload={handleImageSelected}
              currentFile={selectedFile}
              error={scanError}
            />

            <div className="flex justify-end pt-2">
              <button
                type="button"
                onClick={handleStartScan}
                disabled={!selectedFile || scanning}
                className="w-full sm:w-auto px-8 py-3 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold rounded-xl shadow-lg transition text-sm flex items-center justify-center space-x-2"
              >
                {scanning ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    <span>Extracting Declarations & Running Compliance Checks...</span>
                  </>
                ) : (
                  <>
                    <span>Submit Image for Verification</span>
                    <ChevronRight size={16} />
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Results Screen */}
        {scanResult && (
          <div className="space-y-6 pt-2">
            {/* Status Banner */}
            <div
              className={`p-5 rounded-xl border flex items-start space-x-4 shadow-lg ${
                scanResult.compliance_status === 'compliant'
                  ? 'bg-emerald-950/40 border-emerald-800/80 text-emerald-300'
                  : scanResult.compliance_status === 'non_compliant'
                  ? 'bg-rose-950/40 border-rose-800/80 text-rose-300'
                  : 'bg-amber-950/40 border-amber-800/80 text-amber-300'
              }`}
            >
              {scanResult.compliance_status === 'compliant' ? (
                <CheckCircle2 size={32} className="text-emerald-400 shrink-0 mt-0.5" />
              ) : scanResult.compliance_status === 'non_compliant' ? (
                <XCircle size={32} className="text-rose-400 shrink-0 mt-0.5" />
              ) : (
                <AlertTriangle size={32} className="text-amber-400 shrink-0 mt-0.5" />
              )}
              <div className="flex-1">
                <div className="flex items-center space-x-3">
                  <span className="text-lg font-bold uppercase tracking-wider">
                    {scanResult.compliance_status === 'compliant'
                      ? 'Package Verified: Compliant'
                      : scanResult.compliance_status === 'non_compliant'
                      ? 'Statutory Violations Detected'
                      : 'Requires Further Review'}
                  </span>
                </div>
                <p className="text-xs mt-1 text-slate-300 leading-relaxed">
                  {scanResult.compliance_status === 'compliant'
                    ? 'All mandatory statutory declarations required under the Legal Metrology (Packaged Commodities) Rules, 2011 are verified present and compliant.'
                    : scanResult.compliance_status === 'non_compliant'
                    ? 'One or more mandatory Legal Metrology statutory requirements were found missing or non-compliant on the provided label.'
                    : 'Some declarations could not be fully confirmed from the single view. Further manual review is recommended.'}
                </p>
                <div className="mt-3 flex flex-wrap gap-4 text-xs font-mono">
                  <span>Evaluated Rules: <strong>{scanResult.summary?.total_rules_evaluated || 0}</strong></span>
                  <span className="text-emerald-400">Passed: <strong>{scanResult.summary?.passed_count || 0}</strong></span>
                  <span className="text-rose-400">Violations: <strong>{scanResult.summary?.violations_count || 0}</strong></span>
                  <span className="text-amber-400">Needs Review: <strong>{scanResult.summary?.review_count || 0}</strong></span>
                  <span className="text-slate-400">OCR Confidence: <strong>{Math.round((scanResult.ocr_confidence_overall || 0) * 100)}%</strong></span>
                </div>
              </div>
            </div>

            {/* Violations List */}
            {scanResult.violations?.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-sm font-bold text-rose-300 uppercase tracking-wider flex items-center space-x-1.5">
                  <AlertCircle size={16} />
                  <span>Identified Discrepancies & Violations ({scanResult.violations.length})</span>
                </h3>
                <div className="space-y-2">
                  {scanResult.violations.map((v, idx) => (
                    <div
                      key={idx}
                      className="p-4 bg-slate-900/90 border border-rose-900/60 rounded-xl space-y-2"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-white font-mono">{v.rule_code}</span>
                        <span
                          className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded ${
                            v.severity === 'critical'
                              ? 'bg-rose-900/60 text-rose-300 border border-rose-700'
                              : 'bg-amber-900/60 text-amber-300 border border-amber-700'
                          }`}
                        >
                          {v.severity}
                        </span>
                      </div>
                      <p className="text-xs text-slate-300 font-medium">{v.reason}</p>
                      <div className="text-[11px] text-slate-400 flex items-center space-x-2">
                        <span className="text-indigo-400 font-semibold">Statutory Reference:</span>
                        <span>{v.statutory_reference}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Extracted Facts Overview */}
            <div className="space-y-3">
              <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center space-x-1.5">
                <FileCheck size={16} className="text-indigo-400" />
                <span>Extracted Package Declarations</span>
              </h3>
              <div className="bg-slate-900/80 border border-slate-700/80 rounded-xl p-4">
                {Object.keys(scanResult.extracted_facts || {}).length === 0 ? (
                  <p className="text-xs text-slate-400">
                    No clear declarations could be recognized by OCR. Please ensure the label is well-lit, sharp, and unobstructed.
                  </p>
                ) : (
                  <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 text-xs">
                    {Object.entries(scanResult.extracted_facts).map(([key, val]) => {
                      if (val === null || val === undefined) return null;
                      const label = key.replace(/_/g, ' ').toUpperCase();
                      const displayVal = typeof val === 'boolean' ? (val ? 'Yes' : 'No') : String(val);
                      return (
                        <div key={key} className="border-b border-slate-800/80 pb-2">
                          <dt className="text-slate-400 font-semibold text-[10px]">{label}</dt>
                          <dd className="text-slate-200 font-medium mt-0.5 break-words">{displayVal}</dd>
                        </div>
                      );
                    })}
                  </dl>
                )}
              </div>
            </div>

            {/* Complete Evaluated Checks Collapsible / Details */}
            {scanResult.checks?.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-1.5">
                  <CheckCircle2 size={16} className="text-emerald-400" />
                  <span>All Evaluated Statutory Rules ({scanResult.checks.length})</span>
                </h3>
                <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                  {scanResult.checks.map((chk, idx) => (
                    <div
                      key={idx}
                      className="p-3 bg-slate-900/60 border border-slate-800 rounded-lg flex items-start justify-between space-x-3 text-xs"
                    >
                      <div className="space-y-1">
                        <div className="font-semibold text-white font-mono">{chk.rule_code}</div>
                        <div className="text-[11px] text-slate-400">{chk.statutory_reference}</div>
                        <div className="text-[11px] text-slate-300">{chk.reason}</div>
                      </div>
                      <span
                        className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded shrink-0 ${
                          chk.result === 'pass'
                            ? 'bg-emerald-900/60 text-emerald-300 border border-emerald-700'
                            : chk.result === 'fail'
                            ? 'bg-rose-900/60 text-rose-300 border border-rose-700'
                            : chk.result === 'needs_review'
                            ? 'bg-amber-900/60 text-amber-300 border border-amber-700'
                            : 'bg-slate-800 text-slate-400 border border-slate-700'
                        }`}
                      >
                        {chk.result === 'pass' ? 'Pass' : chk.result === 'fail' ? 'Violation' : chk.result}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Consumer Awareness Section */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-800/90 border border-slate-700/80 rounded-xl p-5 shadow-lg">
          <div className="text-indigo-400 font-bold text-base mb-1">MRP Protection</div>
          <p className="text-xs text-slate-300 leading-relaxed">
            No retail seller can charge above the Maximum Retail Price (MRP) printed on the package. MRP must be inclusive of all taxes.
          </p>
        </div>
        <div className="bg-slate-800/90 border border-slate-700/80 rounded-xl p-5 shadow-lg">
          <div className="text-emerald-400 font-bold text-base mb-1">Standard Net Quantity</div>
          <p className="text-xs text-slate-300 leading-relaxed">
            All commodities must clearly declare weight, measure, or numerical count in standard SI metric units (g, kg, ml, L).
          </p>
        </div>
        <div className="bg-slate-800/90 border border-slate-700/80 rounded-xl p-5 shadow-lg">
          <div className="text-purple-400 font-bold text-base mb-1">Consumer Care Grievance</div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Name, complete address, telephone number, and email of the grievance officer must be visibly legible on every retail container.
          </p>
        </div>
      </div>

      {/* Statutory Rules Standards Reference */}
      <div className="bg-slate-800/90 border border-slate-700/80 rounded-xl p-6 shadow-lg space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-white">Legal Metrology Declarations Standards</h2>
            <p className="text-xs text-slate-400">Statutory declarations enforced by the Department of Consumer Affairs</p>
          </div>
          <Link
            to="/customer/rules"
            className="text-xs font-semibold text-indigo-400 hover:text-indigo-300"
          >
            View Full Rule Book &rarr;
          </Link>
        </div>

        {loadingRules ? (
          <p className="text-xs text-slate-400">Fetching standards...</p>
        ) : rules.length === 0 ? (
          <p className="text-xs text-slate-400">No statutory rules currently listed.</p>
        ) : (
          <div className="space-y-2">
            {rules.slice(0, 5).map((r) => {
              const version = r.active_version || (r.versions && r.versions[0]) || {};
              return (
                <div key={r.id || r.rule_code} className="p-3 bg-slate-900/80 border border-slate-700/80 rounded-lg flex items-center justify-between">
                  <div>
                    <div className="text-xs font-medium text-white">{r.rule_code || r.name || 'Statutory Rule'}</div>
                    <div className="text-[11px] text-slate-400">
                      {r.category} | Section: {version.statutory_reference || r.rule_reference || 'LMPC Rules, 2011'}
                    </div>
                  </div>
                  <StatusBadge status={version.verification_status || r.verification_status || 'demo'} />
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
