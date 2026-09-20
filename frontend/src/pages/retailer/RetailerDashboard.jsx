import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Store,
  ShieldCheck,
  AlertTriangle,
  BookOpen,
  Camera,
  FileCheck,
  Send,
  Upload,
  RefreshCw,
  Clock,
  CheckCircle2,
  X,
  FileText,
} from 'lucide-react';
import { listRetailerInquiriesApi, submitSupplierProofApi } from '../../api/inquiries';
import { listRulesApi } from '../../api/rules';
import StatusBadge from '../../components/StatusBadge';
import EmptyState from '../../components/EmptyState';

export default function RetailerDashboard() {
  const [inquiries, setInquiries] = useState([]);
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);

  // Supplier Response Modal
  const [responseModalOpen, setResponseModalOpen] = useState(false);
  const [selectedInquiry, setSelectedInquiry] = useState(null);
  const [supplierName, setSupplierName] = useState('');
  const [supplierContact, setSupplierContact] = useState('');
  const [invoiceNo, setInvoiceNo] = useState('');
  const [explanation, setExplanation] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [inqData, rulesData] = await Promise.all([
        listRetailerInquiriesApi().catch(() => []),
        listRulesApi().catch(() => []),
      ]);
      setInquiries(Array.isArray(inqData) ? inqData : []);
      setRules(Array.isArray(rulesData) ? rulesData : rulesData?.rules || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenResponseModal = (inq) => {
    setSelectedInquiry(inq);
    setSupplierName(inq.supplier_name || '');
    setSupplierContact(inq.supplier_contact || '');
    setInvoiceNo(inq.supplier_invoice_no || '');
    setExplanation(inq.retailer_explanation || '');
    setResponseModalOpen(true);
  };

  const handleSubmitProof = async () => {
    if (!selectedInquiry) return;
    if (!supplierName || !invoiceNo) {
      alert('Please fill in Supplier/Distributor Name and Invoice Number.');
      return;
    }

    setSubmitting(true);
    try {
      await submitSupplierProofApi({
        report_id: selectedInquiry.id,
        supplier_name: supplierName,
        supplier_contact: supplierContact || 'Contact on file',
        supplier_invoice_no: invoiceNo,
        supplier_invoice_file: 'uploads/sample_distributor_bill.pdf',
        retailer_explanation: explanation || 'Commodity received in pre-sealed condition directly from wholesale distributor.',
      });
      alert('Wholesale supplier traceability proof submitted successfully to Legal Metrology Department.');
      setResponseModalOpen(false);
      loadData();
    } catch (err) {
      alert('Failed to submit proof: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSubmitting(false);
    }
  };

  const pendingNotices = inquiries.filter((i) => i.status === 'inquiry_sent').length;
  const respondedCount = inquiries.filter((i) => i.status === 'retailer_responded').length;

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-gradient-to-r from-slate-900 via-slate-900 to-indigo-950/40 p-6 rounded-2xl border border-slate-800 shadow-xl">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Store className="h-6 w-6 text-indigo-400" />
            <span>Retailer & Merchant Compliance Portal</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Store packaging verification, statutory show-cause notices, and wholesale distributor traceability.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            to="/retailer/rules"
            className="px-4 py-2 rounded-xl bg-slate-800 border border-slate-700 hover:bg-slate-700 text-white text-xs font-semibold flex items-center gap-2 transition"
          >
            <BookOpen className="h-4 w-4" />
            <span>LMPC 2011 Standards</span>
          </Link>
          <button
            onClick={loadData}
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition border border-slate-700"
          >
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      {/* Advisory Bar */}
      <div className="p-4 rounded-xl bg-indigo-950/30 border border-indigo-800/40 text-indigo-200 text-xs leading-relaxed space-y-1">
        <strong className="text-white block font-semibold">
          Section 39 / Rule 6 Supply Chain Traceability Protection
        </strong>
        <span>
          As a retailer, if an item on your shelf is flagged for missing or non-compliant manufacturer declarations,
          you can submit your registered distributor/wholesaler purchase invoice. This protects your establishment
          and enables inspectors to pursue the manufacturer upstream.
        </span>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 shadow">
          <div className="flex items-center justify-between text-xs text-slate-400 uppercase font-semibold">
            <span>Pending Show-Cause Notices</span>
            <AlertTriangle className="h-4 w-4 text-rose-400" />
          </div>
          <p className="text-2xl font-extrabold text-white mt-2">{loading ? '...' : pendingNotices}</p>
          <p className="text-xs text-rose-400 mt-1">Requires wholesale proof response</p>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 shadow">
          <div className="flex items-center justify-between text-xs text-slate-400 uppercase font-semibold">
            <span>Supplier Proofs Submitted</span>
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
          </div>
          <p className="text-2xl font-extrabold text-white mt-2">{loading ? '...' : respondedCount}</p>
          <p className="text-xs text-emerald-400 mt-1">Upstream traceability logged</p>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 shadow">
          <div className="flex items-center justify-between text-xs text-slate-400 uppercase font-semibold">
            <span>Statutory Rules in Force</span>
            <FileCheck className="h-4 w-4 text-indigo-400" />
          </div>
          <p className="text-2xl font-extrabold text-white mt-2">{rules.length || 13}</p>
          <p className="text-xs text-slate-400 mt-1">Verified LMPC 2011 standards</p>
        </div>
      </div>

      {/* Show-Cause Inquiries Section */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
        <div className="border-b border-slate-800/80 pb-3 flex items-center justify-between">
          <div>
            <h2 className="text-sm sm:text-base font-bold text-white">Active Inspector Inquiries & Product Notices</h2>
            <p className="text-xs text-slate-400">
              Notices issued by Legal Metrology Officers regarding products surveyed at your store premises.
            </p>
          </div>
        </div>

        {inquiries.length === 0 ? (
          <EmptyState
            title="Clean Compliance Record"
            description="No active product show-cause inquiries or statutory notices recorded for your store."
          />
        ) : (
          <div className="space-y-3">
            {inquiries.map((inq) => {
              const isPending = inq.status === 'inquiry_sent' || inq.status === 'submitted';
              const isResponded = inq.status === 'retailer_responded';

              return (
                <div
                  key={inq.id}
                  className="p-4 rounded-xl bg-slate-950 border border-slate-800/90 hover:border-slate-700 transition space-y-3"
                >
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-bold text-white">
                          {inq.product_name || 'Packaged Commodity Under Inquiry'}
                        </span>
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold uppercase ${
                            isResponded
                              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                              : 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                          }`}
                        >
                          {inq.status}
                        </span>
                      </div>
                      <p className="text-xs text-slate-300">{inq.description}</p>
                    </div>

                    <button
                      onClick={() => handleOpenResponseModal(inq)}
                      className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-1.5 shrink-0 ${
                        isResponded
                          ? 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                          : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/30'
                      }`}
                    >
                      <Upload size={14} />
                      <span>{isResponded ? 'Update Supplier Proof' : 'Submit Supplier & Invoice Proof'}</span>
                    </button>
                  </div>

                  {/* Inspector Notice Text */}
                  {inq.inquiry_notice_text && (
                    <div className="p-3 rounded-lg bg-rose-950/30 border border-rose-900/50 text-xs text-rose-200 space-y-1">
                      <strong className="block text-[11px] uppercase tracking-wider text-rose-300">
                        Official Officer Notice Directive:
                      </strong>
                      <p>{inq.inquiry_notice_text}</p>
                    </div>
                  )}

                  {/* Existing Submitted Proof Display */}
                  {isResponded && (
                    <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300 space-y-1">
                      <strong className="block text-emerald-400 text-[11px] uppercase tracking-wider">
                        ✓ Submitted Wholesale Origin Credentials:
                      </strong>
                      <div className="flex flex-wrap gap-4 text-slate-300">
                        <span><strong>Distributor:</strong> {inq.supplier_name}</span>
                        <span><strong>Invoice No:</strong> {inq.supplier_invoice_no}</span>
                        <span><strong>Contact:</strong> {inq.supplier_contact}</span>
                      </div>
                      {inq.retailer_explanation && (
                        <p className="text-slate-400 italic mt-1">"{inq.retailer_explanation}"</p>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Supplier Traceability Response Modal */}
      {responseModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-[#0f172a] border border-slate-700 rounded-2xl w-full max-w-lg p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2 text-indigo-400">
                <FileText size={20} />
                <h3 className="text-base font-bold text-white">Submit Wholesale Supplier Invoice</h3>
              </div>
              <button
                onClick={() => setResponseModalOpen(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg"
              >
                <X size={18} />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <p className="text-slate-300">
                Provide details of the distributor, wholesaler, or manufacturer from whom this batch was purchased.
              </p>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">
                  Wholesaler / Distributor Business Name:
                </label>
                <input
                  type="text"
                  value={supplierName}
                  onChange={(e) => setSupplierName(e.target.value)}
                  placeholder="e.g. Apex FMCG Wholesalers Pvt Ltd"
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Invoice / Bill Number:</label>
                  <input
                    type="text"
                    value={invoiceNo}
                    onChange={(e) => setInvoiceNo(e.target.value)}
                    placeholder="e.g. INV-2026-9921"
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Distributor Phone / Contact:</label>
                  <input
                    type="text"
                    value={supplierContact}
                    onChange={(e) => setSupplierContact(e.target.value)}
                    placeholder="e.g. +91 98110 22334"
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">
                  Merchant Statement / Explanation:
                </label>
                <textarea
                  rows={3}
                  value={explanation}
                  onChange={(e) => setExplanation(e.target.value)}
                  placeholder="State how and when the commodity was delivered and whether packages were pre-sealed."
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-slate-800">
              <button
                onClick={() => setResponseModalOpen(false)}
                className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmitProof}
                disabled={submitting}
                className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition shadow-lg shadow-indigo-600/30 flex items-center gap-1.5 disabled:opacity-50"
              >
                {submitting ? <RefreshCw size={14} className="animate-spin" /> : <Send size={14} />}
                <span>{submitting ? 'Submitting Proof...' : 'Submit to Legal Metrology'}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
