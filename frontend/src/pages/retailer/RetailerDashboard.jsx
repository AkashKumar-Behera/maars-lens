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
  Scan,
  UploadCloud,
  Trash2,
  Check,
  Sparkles,
  ChevronRight,
  IndianRupee,
  Layers,
  Tag,
  Scale,
  Calendar,
  PhoneCall,
  Globe,
  AlertCircle,
  XCircle,
  Copy,
  CheckCheck,
} from 'lucide-react';
import { listRetailerInquiriesApi, submitSupplierProofApi } from '../../api/inquiries';
import { listRulesApi } from '../../api/rules';
import { customerScanLabelApi } from '../../api/customer';
import StatusBadge from '../../components/StatusBadge';
import EmptyState from '../../components/EmptyState';

// 10 Statutory Rules Metadata for Consumer/Retailer Packaging Verification
const STATUTORY_RULES_METADATA = [
  {
    code: 'LMPC-R6-MRP-TAX-INCLUSIVE',
    fallbackCodes: ['PCR-2011-RULE-6-1-MRP'],
    title: 'MRP Tax-Inclusive Declaration',
    reference: 'Legal Metrology (Packaged Commodities) Rules, 2011 - Rule 6(1)(e)',
    targetField: 'mrp_tax_inclusive',
    keywords: ['inclusive of all taxes', 'incl. of all taxes', 'incl of taxes', 'सभी कर सहित', 'कर सहित'],
    icon: IndianRupee,
    description: 'MRP declaration must explicitly mention inclusive of all taxes or similar statutory phrasing.',
  },
  {
    code: 'LMPC-R6-MRP',
    fallbackCodes: ['PCR-2011-RULE-6-1-MRP'],
    title: 'Maximum Retail Price (MRP)',
    reference: 'Legal Metrology (Packaged Commodities) Rules, 2011 - Rule 6(1)(e)',
    targetField: 'mrp',
    keywords: ['mrp', 'm.r.p', 'max retail price', 'maximum retail price', 'अधिकतम खुदरा मूल्य', 'rs.', '₹'],
    icon: IndianRupee,
    description: 'Maximum retail price in Indian Rupees must be clearly declared on package.',
  },
  {
    code: 'LMPC-R6-NAME-ADDRESS',
    fallbackCodes: [],
    title: 'Manufacturer / Packer / Importer Address',
    reference: 'Legal Metrology (Packaged Commodities) Rules, 2011 - Rule 6(1)(a)',
    targetField: 'manufacturer',
    keywords: ['manufactured by', 'marketed by', 'packed by', 'imported by', 'mfg by', 'निर्माता', 'द्वारा निर्मित'],
    icon: Layers,
    description: 'Name and complete physical address of the manufacturer, packer or importer must be declared.',
  },
  {
    code: 'LMPC-R6-GENERIC-NAME',
    fallbackCodes: [],
    title: 'Common or Generic Name of Commodity',
    reference: 'Legal Metrology (Packaged Commodities) Rules, 2011 - Rule 6(1)(b)',
    targetField: 'generic_name',
    keywords: ['generic name', 'common name', 'product name', 'commodity name', 'वस्तु का नाम', 'सामान्य नाम'],
    icon: Tag,
    description: 'Common or generic name of the commodity must be declared on every package.',
  },
  {
    code: 'LMPC-R6-NET-QTY',
    fallbackCodes: [],
    title: 'Net Quantity in Standard Units',
    reference: 'Legal Metrology (Packaged Commodities) Rules, 2011 - Rule 6(1)(d)',
    targetField: 'net_quantity',
    keywords: ['net qty', 'net quantity', 'net wt', 'net weight', 'g', 'kg', 'ml', 'l', 'शुद्ध मात्रा'],
    icon: Scale,
    description: 'Net quantity in standard units of weight, measure or number must be declared.',
  },
  {
    code: 'LMPC-R6-MFG-MONTH-YEAR',
    fallbackCodes: [],
    title: 'Month & Year of Manufacture / Packing',
    reference: 'Legal Metrology (Packaged Commodities) Rules, 2011 - Rule 6(1)(b)',
    targetField: 'mfg_date',
    keywords: ['mfg date', 'mfd date', 'mfg.', 'mfd.', 'pkd date', 'packed date', 'date of packing', 'निर्माण तिथि'],
    icon: Calendar,
    description: 'Month and year in which commodity is manufactured, packed, or imported must be stated.',
  },
  {
    code: 'LMPC-R6-CONSUMER-CARE',
    fallbackCodes: [],
    title: 'Consumer Grievance / Care Contact',
    reference: 'Legal Metrology (Packaged Commodities) Rules, 2011 - Rule 6(1)(da)',
    targetField: 'customer_care',
    keywords: ['consumer care', 'customer care', 'helpline', 'toll free', 'care@', 'grievance officer', 'ग्राहक सेवा'],
    icon: PhoneCall,
    description: 'Name, address, telephone number and email address for consumer complaint resolution.',
  },
  {
    code: 'LMPC-R6-COUNTRY-OF-ORIGIN',
    fallbackCodes: [],
    title: 'Country of Origin / Manufacture',
    reference: 'Legal Metrology (Packaged Commodities) Rules, 2011 - Rule 6(10)',
    targetField: 'country_of_origin',
    keywords: ['country of origin', 'origin:', 'made in', 'मूल देश', 'उत्पत्ति देश'],
    icon: Globe,
    description: 'Name of country of origin or manufacture must be clearly declared.',
  },
  {
    code: 'LMPC-R6-UNIT-SALE-PRICE',
    fallbackCodes: [],
    title: 'Unit Sale Price (USP)',
    reference: 'Legal Metrology (Packaged Commodities) Amendment Rules - Rule 6(11)',
    targetField: 'unit_sale_price',
    keywords: ['unit sale price', 'usp', 'per unit', '₹ / 100g', '₹ / 100ml', 'प्रति इकाई मूल्य'],
    icon: IndianRupee,
    description: 'Unit sale price declared on packages where net quantity is more than one unit or specified threshold.',
  },
  {
    code: 'FSSAI-SEC-31-LIC',
    fallbackCodes: ['LMPC-R7-FONT-SIZE'],
    title: 'FSSAI License / Registration Declaration',
    reference: 'FSSAI (Labelling & Display) Regulations, 2020 & LMPC General Declarations',
    targetField: 'fssai',
    keywords: ['fssai', 'lic. no', 'lic no', 'license', 'एफएसएसएआई'],
    icon: FileCheck,
    description: 'FSSAI logo and 14-digit Food Safety License/Registration Number must be displayed on packaged food commodities.',
  },
];

export default function RetailerDashboard() {
  const [activeTab, setActiveTab] = useState('scanner'); // 'scanner' | 'inquiries'
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

  // 5 Multi-panel upload state
  const PANEL_DEFAULTS = [
    { id: 'p1', label: '1. Front / Principal Panel', required: true, defaultType: 'front', hint: 'Mandatory - Brand, Product Name' },
    { id: 'p2', label: '2. Back Panel (Optional)', required: false, defaultType: 'back', hint: 'MRP, Date, Manufacturer' },
    { id: 'p3', label: '3. Side Panel (Optional)', required: false, defaultType: 'side', hint: 'Nutritional / Ingredients' },
    { id: 'p4', label: '4. Consumer Care Panel (Optional)', required: false, defaultType: 'side', hint: 'Toll-free / Customer Email' },
    { id: 'p5', label: '5. Top / Bottom / Outer (Optional)', required: false, defaultType: 'top', hint: 'Batch, Barcode, Additional Info' },
  ];

  const [panelSlots, setPanelSlots] = useState([
    { file: null, preview: null, type: 'front' },
    { file: null, preview: null, type: 'back' },
    { file: null, preview: null, type: 'side' },
    { file: null, preview: null, type: 'side' },
    { file: null, preview: null, type: 'top' },
  ]);

  const [scanning, setScanning] = useState(false);
  const [scanError, setScanError] = useState(null);
  const [scanResult, setScanResult] = useState(null);
  const [copiedRawText, setCopiedRawText] = useState(false);
  const [filterMode, setFilterMode] = useState('all');

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

  const handleMultiSelectFiles = (files) => {
    if (!files || files.length === 0) return;
    setScanError(null);
    const selectedFiles = Array.from(files).slice(0, 5);

    setPanelSlots((prev) => {
      const next = [...prev];
      selectedFiles.forEach((file, idx) => {
        if (idx < next.length) {
          if (next[idx].preview) {
            URL.revokeObjectURL(next[idx].preview);
          }
          next[idx] = {
            ...next[idx],
            file,
            preview: URL.createObjectURL(file),
          };
        }
      });
      return next;
    });
  };

  const handleSlotFileChange = (index, file) => {
    setScanError(null);
    setPanelSlots((prev) => {
      const next = [...prev];
      if (next[index].preview) {
        URL.revokeObjectURL(next[index].preview);
      }
      next[index] = {
        ...next[index],
        file: file || null,
        preview: file ? URL.createObjectURL(file) : null,
      };
      return next;
    });
  };

  const handleSlotTypeChange = (index, newType) => {
    setPanelSlots((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], type: newType };
      return next;
    });
  };

  const handleClearSlot = (index) => {
    setPanelSlots((prev) => {
      const next = [...prev];
      if (next[index].preview) {
        URL.revokeObjectURL(next[index].preview);
      }
      next[index] = { ...next[index], file: null, preview: null };
      return next;
    });
  };

  const handleResetScan = () => {
    panelSlots.forEach((slot) => {
      if (slot.preview) URL.revokeObjectURL(slot.preview);
    });
    setPanelSlots([
      { file: null, preview: null, type: 'front' },
      { file: null, preview: null, type: 'back' },
      { file: null, preview: null, type: 'side' },
      { file: null, preview: null, type: 'side' },
      { file: null, preview: null, type: 'top' },
    ]);
    setScanResult(null);
    setScanError(null);
  };

  const handleStartScan = async () => {
    if (!panelSlots[0].file) {
      setScanError('Panel 1 (Front / Principal Display Panel) photo is mandatory. Please upload at least 1 image.');
      return;
    }

    const validPanels = panelSlots.filter((s) => s.file !== null);
    const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
    for (let i = 0; i < validPanels.length; i++) {
      const f = validPanels[i].file;
      if (!validTypes.includes(f.type) && !f.name.match(/\.(jpe?g|png|webp)$/i)) {
        setScanError(`File ${f.name} is not a valid format. Please upload JPG, PNG, or WebP.`);
        return;
      }
      if (f.size > 15 * 1024 * 1024) {
        setScanError(`File ${f.name} exceeds maximum allowed size of 15MB.`);
        return;
      }
    }

    setScanning(true);
    setScanError(null);
    setScanResult(null);

    try {
      const filesToUpload = validPanels.map((s) => s.file);
      const typesToUpload = validPanels.map((s) => s.type);
      const result = await customerScanLabelApi(filesToUpload, typesToUpload);
      setScanResult(result);
    } catch (err) {
      const detail = err.response?.data?.detail;
      let errorMsg = 'Failed to analyze product label images. Please ensure labels are clear and legible.';
      if (typeof detail === 'string') {
        errorMsg = detail;
      } else if (Array.isArray(detail)) {
        errorMsg = detail.map((d) => d.msg || (typeof d === 'string' ? d : JSON.stringify(d))).join('; ');
      } else if (detail && typeof detail === 'object') {
        errorMsg = detail.msg || detail.message || JSON.stringify(detail);
      } else if (err.message) {
        errorMsg = err.message;
      }
      setScanError(errorMsg);
    } finally {
      setScanning(false);
    }
  };

  const handleCopyRawText = () => {
    if (!scanResult?.raw_text) return;
    navigator.clipboard.writeText(scanResult.raw_text);
    setCopiedRawText(true);
    setTimeout(() => setCopiedRawText(false), 2500);
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

  const getRuleEvaluation = (meta) => {
    if (!scanResult) return null;
    const checks = scanResult.checks || [];
    const extractedFacts = scanResult.extracted_facts || {};

    let match = checks.find((c) => c.rule_code === meta.code);
    if (!match && meta.fallbackCodes?.length > 0) {
      match = checks.find((c) => meta.fallbackCodes.includes(c.rule_code));
    }

    const factVal = extractedFacts[meta.targetField];
    const isPresentInFacts = factVal !== undefined && factVal !== null && factVal !== false && String(factVal).trim().length > 0;
    const isPass = meta.targetField === 'fssai' ? isPresentInFacts : (match ? match.result === 'pass' : isPresentInFacts);
    const isFail = !isPass;

    let detectedText = null;
    if (isPresentInFacts) {
      detectedText = typeof factVal === 'boolean' ? (factVal ? 'Statutory phrasing present' : 'Missing') : String(factVal);
    } else if (match?.actual_value && match.actual_value !== 'None') {
      detectedText = String(match.actual_value);
    }

    return {
      status: isPass ? 'present' : (isFail ? 'missing' : 'review'),
      isPass,
      reason: isPass
        ? (detectedText ? `Detected on package: ${detectedText}` : 'Declaration verified and compliant.')
        : (match?.reason || 'Mandatory statutory declaration missing on package label.'),
      detectedText,
      severity: match?.severity || 'major',
    };
  };

  const evaluatedRules = STATUTORY_RULES_METADATA.map((meta) => {
    const evalData = getRuleEvaluation(meta);
    return { ...meta, evalData };
  });

  const presentCount = evaluatedRules.filter((r) => r.evalData?.isPass).length;
  const missingCount = evaluatedRules.filter((r) => r.evalData && !r.evalData.isPass).length;

  const displayRules = evaluatedRules.filter((r) => {
    if (filterMode === 'present') return r.evalData?.isPass;
    if (filterMode === 'missing') return r.evalData && !r.evalData.isPass;
    return true;
  });

  const pendingNotices = inquiries.filter((i) => i.status === 'inquiry_sent').length;
  const respondedCount = inquiries.filter((i) => i.status === 'retailer_responded').length;

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-16">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-gradient-to-r from-slate-900 via-slate-900 to-indigo-950/40 p-6 rounded-2xl border border-slate-800 shadow-xl">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Store className="h-6 w-6 text-indigo-400" />
            <span>Retailer & Merchant Compliance Portal</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Pre-shelf inventory verification, 10 Statutory Rules multi-panel OCR audit, and wholesale distributor traceability.
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
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition border border-slate-700 cursor-pointer"
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
          Use the <strong>Pre-Shelf Multi-Panel Scanner</strong> to verify commodity packaging before displaying items in your store.
          If any supplier goods are non-compliant, upload distributor invoices to protect your establishment from legal liability.
        </span>
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-3 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab('scanner')}
          className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition flex items-center gap-2 cursor-pointer ${
            activeTab === 'scanner'
              ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/25'
              : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
          }`}
        >
          <Camera size={16} />
          <span>Pre-Shelf Multi-Panel Scanner</span>
        </button>

        <button
          onClick={() => setActiveTab('inquiries')}
          className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition flex items-center gap-2 cursor-pointer relative ${
            activeTab === 'inquiries'
              ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/25'
              : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
          }`}
        >
          <FileText size={16} />
          <span>Inspector Notices & Supplier Proofs</span>
          {pendingNotices > 0 && (
            <span className="px-1.5 py-0.5 rounded-full bg-rose-500 text-white text-[10px] font-bold">
              {pendingNotices}
            </span>
          )}
        </button>
      </div>

      {/* TAB 1: PRE-SHELF MULTI-PANEL SCANNER */}
      {activeTab === 'scanner' && (
        <div className="space-y-6">
          {/* Main Image Upload Card */}
          <div className="bg-[#0c1220] border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-6">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
              <div>
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  <Camera className="text-indigo-400" size={20} />
                  <span>Pre-Shelf Commodity Label Inspection</span>
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  Upload package photos (up to 5 panels) to extract OCR text and verify mandatory 10 Statutory Declarations
                </p>
              </div>
              {panelSlots.some((s) => s.file !== null) && (
                <button
                  onClick={handleResetScan}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-lg transition border border-slate-700 cursor-pointer"
                >
                  <RefreshCw size={13} />
                  <span>Reset Panels</span>
                </button>
              )}
            </div>

            {/* Error Alert */}
            {scanError && (
              <div className="p-4 bg-rose-950/60 border border-rose-800/80 rounded-xl text-rose-300 text-xs flex items-start gap-2.5 shadow-md">
                <AlertCircle size={18} className="shrink-0 mt-0.5 text-rose-400" />
                <div className="flex-1 leading-relaxed font-medium">{scanError}</div>
              </div>
            )}

            {/* Quick Multi-Image Picker Dropzone / Button */}
            <div className="p-4 rounded-xl bg-gradient-to-r from-indigo-950/40 via-[#0a101f] to-slate-900/50 border border-indigo-500/30 flex flex-col sm:flex-row items-center justify-between gap-4 shadow-inner">
              <div className="flex items-center gap-3 text-left">
                <div className="p-2.5 rounded-xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 shrink-0">
                  <UploadCloud size={24} />
                </div>
                <div>
                  <div className="text-xs sm:text-sm font-bold text-white flex items-center gap-1.5">
                    <span>Multi-Image Select (Max 5 Images)</span>
                    <span className="text-[10px] font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 px-1.5 py-0.2 rounded">
                      Quick Batch
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    Select up to 5 photos from your folder/device at once. They will automatically populate Panel 1 (Mandatory) through Panel 5.
                  </p>
                </div>
              </div>

              <label className="inline-flex items-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-xl cursor-pointer shadow-lg shadow-indigo-600/25 transition whitespace-nowrap active:scale-95 shrink-0">
                <UploadCloud size={16} />
                <span>Choose Up to 5 Photos</span>
                <input
                  type="file"
                  multiple
                  accept="image/jpeg,image/png,image/webp"
                  className="hidden"
                  onChange={(e) => {
                    if (e.target.files && e.target.files.length > 0) {
                      handleMultiSelectFiles(e.target.files);
                      e.target.value = '';
                    }
                  }}
                />
              </label>
            </div>

            {/* 5-Panel Package Multi-Image Upload Grid */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="text-xs text-slate-400">
                  <span className="font-semibold text-white">Capture / Upload Package Faces</span> &bull;
                  <span className="text-amber-400 font-medium ml-1">Panel 1 is mandatory</span>, rest 4 are optional for full 360° compliance audit.
                </div>
                <span className="text-[11px] font-mono text-indigo-400 bg-indigo-950/80 px-2 py-0.5 rounded border border-indigo-800/60">
                  {panelSlots.filter((s) => s.file !== null).length} of 5 Panels Added
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {PANEL_DEFAULTS.map((def, idx) => {
                  const slot = panelSlots[idx];
                  const isFilled = slot && slot.file !== null;

                  return (
                    <div
                      key={def.id}
                      className={`rounded-xl border p-4 transition relative flex flex-col justify-between ${
                        isFilled
                          ? 'bg-slate-900/90 border-indigo-500/60 shadow-lg shadow-indigo-950/30'
                          : def.required
                          ? 'bg-[#080d18] border-amber-500/50 hover:border-amber-400/80 ring-1 ring-amber-500/20'
                          : 'bg-[#080d18]/70 border-slate-800 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2 mb-2.5">
                        <div>
                          <div className="flex items-center gap-1.5">
                            <span className="text-xs font-bold text-white tracking-tight">{def.label}</span>
                            {def.required ? (
                              <span className="px-1.5 py-0.2 text-[9px] font-bold uppercase rounded bg-amber-500/20 text-amber-300 border border-amber-500/40">
                                Required
                              </span>
                            ) : (
                              <span className="px-1.5 py-0.2 text-[9px] font-medium rounded bg-slate-800 text-slate-400 border border-slate-700">
                                Optional
                              </span>
                            )}
                          </div>
                          <p className="text-[11px] text-slate-400 mt-0.5 leading-tight">{def.hint}</p>
                        </div>

                        {isFilled && (
                          <button
                            type="button"
                            onClick={() => handleClearSlot(idx)}
                            className="text-slate-400 hover:text-rose-400 p-1 rounded hover:bg-slate-800 transition cursor-pointer"
                            title="Remove image"
                          >
                            <Trash2 size={14} />
                          </button>
                        )}
                      </div>

                      {isFilled ? (
                        <div className="space-y-2">
                          <div className="relative w-full h-36 rounded-lg overflow-hidden bg-black/60 border border-slate-700 flex items-center justify-center">
                            <img src={slot.preview} alt={`Panel ${idx + 1}`} className="w-full h-full object-contain" />
                            <div className="absolute top-1.5 right-1.5">
                              <span className="px-1.5 py-0.5 rounded bg-black/70 text-emerald-300 text-[10px] font-mono border border-emerald-500/40 flex items-center gap-1">
                                <Check size={10} /> Loaded
                              </span>
                            </div>
                          </div>

                          <div className="flex items-center justify-between gap-2 pt-1">
                            <span className="text-[10px] text-slate-400 font-medium">Panel Tag:</span>
                            <select
                              value={slot.type}
                              onChange={(e) => handleSlotTypeChange(idx, e.target.value)}
                              className="px-2 py-1 bg-[#060a12] border border-slate-700 rounded text-[11px] text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                            >
                              <option value="front">Principal Front</option>
                              <option value="back">Back / Declarations</option>
                              <option value="side">Side / Nutritional</option>
                              <option value="top">Top / Bottom (MRP)</option>
                              <option value="other">Outer / Box</option>
                            </select>
                          </div>
                        </div>
                      ) : (
                        <label className="border-2 border-dashed border-slate-700/80 hover:border-indigo-500/70 hover:bg-indigo-950/10 rounded-lg p-5 flex flex-col items-center justify-center cursor-pointer transition text-center group min-h-[144px]">
                          <div className="p-2 rounded-lg bg-slate-800 group-hover:bg-indigo-600/20 text-slate-400 group-hover:text-indigo-400 transition mb-2">
                            <Camera size={20} />
                          </div>
                          <span className="text-xs font-semibold text-slate-200 group-hover:text-white">
                            {def.required ? 'Take Photo or Choose File' : '+ Add Optional Face'}
                          </span>
                          <span className="text-[10px] text-slate-500 mt-1">JPEG, PNG, WebP (Max 15MB)</span>
                          <input
                            type="file"
                            accept="image/jpeg,image/png,image/webp"
                            className="hidden"
                            onChange={(e) => {
                              const file = e.target.files?.[0];
                              if (file) handleSlotFileChange(idx, file);
                            }}
                          />
                        </label>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Action Bar */}
              <div className="pt-4 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-3">
                <div className="text-xs text-slate-400">
                  {panelSlots[0].file ? (
                    <span className="text-emerald-400 font-semibold flex items-center gap-1.5">
                      <Check size={14} /> Ready to verify {panelSlots.filter((s) => s.file !== null).length} package panel(s).
                    </span>
                  ) : (
                    <span className="text-amber-400 flex items-center gap-1.5">
                      <AlertCircle size={14} /> Please upload Panel 1 (Front photo) to proceed.
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-2.5">
                  {panelSlots.some((s) => s.file !== null) && (
                    <button
                      type="button"
                      onClick={handleResetScan}
                      disabled={scanning}
                      className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-xl transition border border-slate-700 cursor-pointer"
                    >
                      Clear All
                    </button>
                  )}

                  <button
                    type="button"
                    onClick={handleStartScan}
                    disabled={scanning || !panelSlots[0].file}
                    className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold rounded-xl shadow-lg transition text-xs flex items-center gap-2 cursor-pointer"
                  >
                    {scanning ? (
                      <>
                        <RefreshCw size={14} className="animate-spin" />
                        <span>Analyzing OCR & Verifying {panelSlots.filter((s) => s.file !== null).length} Panel(s)...</span>
                      </>
                    ) : (
                      <>
                        <Sparkles size={14} />
                        <span>{scanResult ? 'Re-verify Panels' : 'Verify Statutory Rules'}</span>
                        <ChevronRight size={14} />
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Loading Indicator when scanning */}
          {scanning && (
            <div className="bg-[#0c1220] border border-indigo-900/50 rounded-2xl p-8 text-center shadow-2xl space-y-4">
              <div className="inline-flex p-4 rounded-full bg-indigo-500/10 text-indigo-400 animate-pulse border border-indigo-500/20">
                <RefreshCw size={32} className="animate-spin text-indigo-400" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">Extracting Package Declarations</h3>
                <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
                  Extracting verbatim OCR lines, normalizing numerals, and scanning targeted statutory keywords for 10 Legal Metrology Rules...
                </p>
              </div>
            </div>
          )}

          {/* RESULTS SECTION: DIRECTLY UNDER THE IMAGE */}
          {scanResult && !scanning && (
            <div className="space-y-6">
              {/* Overall Compliance Verdict Banner */}
              <div
                className={`p-5 rounded-2xl border flex flex-col sm:flex-row items-start gap-4 shadow-xl backdrop-blur ${
                  scanResult.compliance_status === 'compliant'
                    ? 'bg-emerald-950/40 border-emerald-800/80 text-emerald-300'
                    : scanResult.compliance_status === 'non_compliant'
                    ? 'bg-rose-950/40 border-rose-800/80 text-rose-300'
                    : 'bg-amber-950/40 border-amber-800/80 text-amber-300'
                }`}
              >
                <div className="p-2.5 rounded-xl bg-black/30 border border-current shrink-0">
                  {scanResult.compliance_status === 'compliant' ? (
                    <CheckCircle2 size={32} className="text-emerald-400" />
                  ) : scanResult.compliance_status === 'non_compliant' ? (
                    <XCircle size={32} className="text-rose-400" />
                  ) : (
                    <AlertTriangle size={32} className="text-amber-400" />
                  )}
                </div>

                <div className="flex-1 space-y-2">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="text-base sm:text-lg font-bold uppercase tracking-wider">
                      {scanResult.compliance_status === 'compliant'
                        ? '10 / 10 Statutory Rules Verified: Fully Compliant'
                        : scanResult.compliance_status === 'non_compliant'
                        ? 'Statutory Violations Detected (Missing Declarations)'
                        : 'Pre-Audit Complete: Advisory & Review Items'}
                    </span>
                    <span className="px-3 py-1 rounded-full text-xs font-bold font-mono uppercase bg-black/40 border border-current">
                      {scanResult.compliance_status}
                    </span>
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed">
                    {scanResult.compliance_status === 'compliant'
                      ? 'All mandatory Legal Metrology declarations under Rule 6 and Rule 7 were detected on the package label. This batch is safe to place on retail shelves.'
                      : 'The package is missing one or more mandatory statutory declarations. If this was received from a wholesale supplier, you should request compliant stock or log supplier invoice proof.'}
                  </p>

                  <div className="flex flex-wrap gap-4 pt-1 text-xs font-mono">
                    <span className="text-slate-300">
                      Total Rules: <strong>{STATUTORY_RULES_METADATA.length}</strong>
                    </span>
                    <span className="text-emerald-400 flex items-center gap-1">
                      <Check size={14} className="stroke-[3]" />
                      <span>Present (Compliant): <strong>{presentCount}</strong></span>
                    </span>
                    <span className="text-rose-400 flex items-center gap-1">
                      <X size={14} className="stroke-[3]" />
                      <span>Missing (Non-Compliant): <strong>{missingCount}</strong></span>
                    </span>
                    <span className="text-indigo-400">
                      OCR Confidence: <strong>{Math.round((scanResult.ocr_confidence_overall || 0.95) * 100)}%</strong>
                    </span>
                  </div>
                </div>
              </div>

              {/* Raw OCR Text Box */}
              <div className="bg-[#0c1220] border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                  <div className="flex items-center gap-2">
                    <FileText size={18} className="text-indigo-400" />
                    <h3 className="text-sm font-bold text-white">Extracted Package OCR Text (Raw)</h3>
                  </div>
                  <button
                    onClick={handleCopyRawText}
                    className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold flex items-center gap-1.5 transition border border-slate-700 cursor-pointer"
                  >
                    {copiedRawText ? <CheckCheck size={14} className="text-emerald-400" /> : <Copy size={14} />}
                    <span>{copiedRawText ? 'Copied' : 'Copy Text'}</span>
                  </button>
                </div>
                <pre className="bg-[#060a12] p-4 rounded-xl text-xs text-slate-300 font-mono overflow-x-auto max-h-48 border border-slate-800/80 leading-relaxed whitespace-pre-wrap">
                  {scanResult.raw_text || 'No legible text extracted from image.'}
                </pre>
              </div>

              {/* 10 Statutory Rules Compliance Breakdown */}
              <div className="bg-[#0c1220] border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-4 border-b border-slate-800 gap-3">
                  <div>
                    <h3 className="text-base font-bold text-white flex items-center gap-2">
                      <ShieldCheck className="text-emerald-400" size={20} />
                      <span>10 Statutory Declarations Checklist</span>
                    </h3>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Verifies compliance against Rule 6 & 7 of Legal Metrology (Packaged Commodities) Rules, 2011
                    </p>
                  </div>

                  {/* Filter chips */}
                  <div className="flex items-center gap-1 bg-[#060a12] p-1 rounded-xl border border-slate-800 self-start">
                    <button
                      onClick={() => setFilterMode('all')}
                      className={`px-3 py-1 rounded-lg text-xs font-semibold transition cursor-pointer ${
                        filterMode === 'all' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
                      }`}
                    >
                      All (10)
                    </button>
                    <button
                      onClick={() => setFilterMode('present')}
                      className={`px-3 py-1 rounded-lg text-xs font-semibold transition cursor-pointer ${
                        filterMode === 'present' ? 'bg-emerald-600 text-white' : 'text-slate-400 hover:text-white'
                      }`}
                    >
                      Compliant ({presentCount})
                    </button>
                    <button
                      onClick={() => setFilterMode('missing')}
                      className={`px-3 py-1 rounded-lg text-xs font-semibold transition cursor-pointer ${
                        filterMode === 'missing' ? 'bg-rose-600 text-white' : 'text-slate-400 hover:text-white'
                      }`}
                    >
                      Missing ({missingCount})
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {displayRules.map((rule, idx) => {
                    const Icon = rule.icon || FileCheck;
                    const isPass = rule.evalData?.isPass;

                    return (
                      <div
                        key={rule.code}
                        className={`p-4 rounded-xl border transition space-y-2.5 ${
                          isPass
                            ? 'bg-[#08121f] border-emerald-800/40 hover:border-emerald-700/60'
                            : 'bg-[#150a12] border-rose-900/50 hover:border-rose-800/80'
                        }`}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex items-center gap-2">
                            <div
                              className={`p-2 rounded-lg ${
                                isPass
                                  ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                                  : 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                              }`}
                            >
                              <Icon size={16} />
                            </div>
                            <div>
                              <span className="text-xs font-bold text-white block">{rule.title}</span>
                              <span className="text-[10px] text-slate-400 font-mono">{rule.code}</span>
                            </div>
                          </div>

                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase font-mono ${
                              isPass
                                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                                : 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                            }`}
                          >
                            {isPass ? 'COMPLIANT' : 'NON-COMPLIANT'}
                          </span>
                        </div>

                        <p className="text-[11px] text-slate-300 leading-snug">{rule.description}</p>

                        {rule.evalData?.detectedText && (
                          <div className="p-2 rounded-lg bg-black/40 border border-slate-800 text-[11px] text-slate-300 font-mono">
                            <strong className="text-slate-400">Detected: </strong>
                            <span>{rule.evalData.detectedText}</span>
                          </div>
                        )}

                        <div className="text-[10px] text-slate-500 pt-1 border-t border-slate-800/60 flex items-center justify-between">
                          <span>{rule.reference}</span>
                          <span className={isPass ? 'text-emerald-400 font-semibold' : 'text-rose-400 font-semibold'}>
                            {isPass ? '✓ Verified' : '✗ Declaration Missing'}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: SHOW-CAUSE INQUIRIES & SUPPLIER INVOICES */}
      {activeTab === 'inquiries' && (
        <div className="space-y-6">
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
              <p className="text-2xl font-extrabold text-white mt-2">{rules.length || 10}</p>
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
                          className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-1.5 shrink-0 cursor-pointer ${
                            isResponded
                              ? 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                              : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/30'
                          }`}
                        >
                          <Upload size={14} />
                          <span>{isResponded ? 'Update Supplier Proof' : 'Submit Supplier & Invoice Proof'}</span>
                        </button>
                      </div>

                      {inq.inquiry_notice_text && (
                        <div className="p-3 rounded-lg bg-rose-950/30 border border-rose-900/50 text-xs text-rose-200 space-y-1">
                          <strong className="block text-[11px] uppercase tracking-wider text-rose-300">
                            Official Officer Notice Directive:
                          </strong>
                          <p>{inq.inquiry_notice_text}</p>
                        </div>
                      )}

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
        </div>
      )}

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
                className="text-slate-400 hover:text-white p-1 rounded-lg cursor-pointer"
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
                className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-semibold cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmitProof}
                disabled={submitting}
                className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition shadow-lg shadow-indigo-600/30 flex items-center gap-1.5 disabled:opacity-50 cursor-pointer"
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
