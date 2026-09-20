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
  Copy,
  CheckCheck,
  FileText,
  Tag,
  Scale,
  Calendar,
  IndianRupee,
  PhoneCall,
  Globe,
  Layers,
  Sparkles,
  X,
  Trash2,
  UploadCloud,
} from 'lucide-react';
import { listRulesApi } from '../../api/rules';
import { customerScanLabelApi } from '../../api/customer';
import { submitCustomerGeoReportApi, listStoresApi } from '../../api/inquiries';
import ImageUpload from '../../components/ImageUpload';
import StatusBadge from '../../components/StatusBadge';

// 10 Statutory Rules Metadata for Consumer Packaging Verification
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

export default function CustomerPortal() {
  const [rules, setRules] = useState([]);
  const [loadingRules, setLoadingRules] = useState(true);

  // 5 Multi-panel upload state: 1 Mandatory (Front/MRP) + 4 Optional (Back, Side 1, Side 2, Top/Bottom)
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
  const [filterMode, setFilterMode] = useState('all'); // 'all' | 'present' | 'missing'

  // Geo-Reporting state
  const [stores, setStores] = useState([]);
  const [selectedStoreId, setSelectedStoreId] = useState('');
  const [reportNotes, setReportNotes] = useState('');
  const [reporting, setReporting] = useState(false);
  const [reportSuccessMsg, setReportSuccessMsg] = useState(null);
  const [showReportModal, setShowReportModal] = useState(false);

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

    listStoresApi()
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setStores(data);
          setSelectedStoreId(data[0].id);
        }
      })
      .catch((err) => console.error('Failed to load stores:', err));
  }, []);

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
    // 1st slot is mandatory
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
      } else if (err.code === 'ECONNABORTED' || !err.response) {
        errorMsg = 'Backend verification service is currently unreachable. Please verify server connection.';
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

  const handleSubmitGeoReport = async () => {
    if (!scanResult) return;
    setReporting(true);
    setReportSuccessMsg(null);

    // Get current GPS location or default
    let lat = 28.6139;
    let lng = 77.2090;

    if (navigator.geolocation) {
      try {
        const pos = await new Promise((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 5000 });
        });
        lat = pos.coords.latitude;
        lng = pos.coords.longitude;
      } catch (e) {
        console.warn('Geolocation denied or timed out, using fallback coordinates', e);
      }
    }

    const failingCodes = (scanResult.violations || []).map(v => v.rule_code);
    const prodName = scanResult.extracted_facts?.generic_name || scanResult.extracted_facts?.product_name || 'Packaged Commodity';

    try {
      const resp = await submitCustomerGeoReportApi({
        product_name: prodName,
        retailer_id: selectedStoreId || null,
        description: reportNotes || `Statutory non-compliance detected at retail store. Missing declarations: ${failingCodes.join(', ')}`,
        gps_lat: lat,
        gps_lng: lng,
        failing_rule_codes: failingCodes,
        image_storage_path: 'uploads/consumer_report.jpg',
      });
      setReportSuccessMsg(resp.message || 'Violation reported successfully. Nearby enforcement officer has been alerted.');
      setShowReportModal(false);
    } catch (err) {
      alert('Failed to submit geo-report: ' + (err.response?.data?.detail || err.message));
    } finally {
      setReporting(false);
    }
  };

  // Helper to resolve rule status from backend scan checks
  const getRuleEvaluation = (meta) => {
    if (!scanResult) return null;
    const checks = scanResult.checks || [];
    const extractedFacts = scanResult.extracted_facts || {};

    // 1. Direct match by rule code
    let match = checks.find((c) => c.rule_code === meta.code);

    // 2. Fallback codes
    if (!match && meta.fallbackCodes?.length > 0) {
      match = checks.find((c) => meta.fallbackCodes.includes(c.rule_code));
    }

    // 3. Match by target field existence in extracted facts
    const factVal = extractedFacts[meta.targetField];
    const isPresentInFacts = factVal !== undefined && factVal !== null && factVal !== false && String(factVal).trim().length > 0;

    // If targetField is directly in facts (like fssai or customer_care), it passes
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

  // Filtered 10 rules list
  const evaluatedRules = STATUTORY_RULES_METADATA.map((meta) => {
    const evalData = getRuleEvaluation(meta);
    return {
      ...meta,
      evalData,
    };
  });

  const presentCount = evaluatedRules.filter((r) => r.evalData?.isPass).length;
  const missingCount = evaluatedRules.filter((r) => r.evalData && !r.evalData.isPass).length;

  const displayRules = evaluatedRules.filter((r) => {
    if (filterMode === 'present') return r.evalData?.isPass;
    if (filterMode === 'missing') return r.evalData && !r.evalData.isPass;
    return true;
  });

  return (
    <div className="space-y-8 max-w-5xl mx-auto pb-16">
      {/* Portal Header */}
      <div className="text-center py-2">
        <div className="inline-flex p-3 rounded-2xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 mb-3 shadow-lg shadow-indigo-500/5">
          <Shield className="h-7 w-7" />
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
          National Legal Metrology Digital Verification System
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 mt-1.5 max-w-xl mx-auto">
          Upload any packaged commodity image to run automated OCR text extraction and 10 Statutory Rules compliance verification.
        </p>
      </div>

      {/* Main Image Upload Card */}
      <div className="bg-[#0c1220] border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-6">
        <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Camera className="text-indigo-400" size={20} />
              <span>Upload Commodity Label Photo</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Select or take a photo of the product package panel to extract text and audit statutory requirements
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
            <div className="flex-1 leading-relaxed font-medium">
              {scanError}
            </div>
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
                Select up to 5 photos from your gallery or folder at once. They will automatically fill Panel 1 (Mandatory) through Panel 5.
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
                  e.target.value = ''; // reset so user can re-pick same files if desired
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
              {panelSlots.filter(s => s.file !== null).length} of 5 Panels Added
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
                  {/* Card Header */}
                  <div className="flex items-start justify-between gap-2 mb-2.5">
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs font-bold text-white tracking-tight">
                          {def.label}
                        </span>
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
                      <p className="text-[11px] text-slate-400 mt-0.5 leading-tight">
                        {def.hint}
                      </p>
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

                  {/* Preview or Upload Drop Area */}
                  {isFilled ? (
                    <div className="space-y-2">
                      <div className="relative w-full h-36 rounded-lg overflow-hidden bg-black/60 border border-slate-700 flex items-center justify-center">
                        <img
                          src={slot.preview}
                          alt={`Panel ${idx + 1}`}
                          className="w-full h-full object-contain"
                        />
                        <div className="absolute top-1.5 right-1.5">
                          <span className="px-1.5 py-0.5 rounded bg-black/70 text-emerald-300 text-[10px] font-mono border border-emerald-500/40 flex items-center gap-1">
                            <Check size={10} /> Loaded
                          </span>
                        </div>
                      </div>

                      {/* Panel Type Selector */}
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
                      <span className="text-[10px] text-slate-500 mt-1">
                        JPEG, PNG, WebP (Max 15MB)
                      </span>
                      <input
                        type="file"
                        accept="image/jpeg,image/png,image/webp"
                        capture="environment"
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
                  <Check size={14} /> Ready to verify {panelSlots.filter(s => s.file !== null).length} package panel(s).
                </span>
              ) : (
                <span className="text-amber-400 flex items-center gap-1.5">
                  <AlertCircle size={14} /> Please upload Panel 1 (Front photo) to proceed.
                </span>
              )}
            </div>

            <div className="flex items-center gap-2.5">
              {panelSlots.some(s => s.file !== null) && (
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
                    <span>Analyzing OCR & Verifying {panelSlots.filter(s => s.file !== null).length} Panel(s)...</span>
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
          {/* 1. Overall Compliance Verdict Banner */}
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
                    : 'Inspection Complete: Advisory & Review Items'}
                </span>
                <span className="px-3 py-1 rounded-full text-xs font-bold font-mono uppercase bg-black/40 border border-current">
                  {scanResult.compliance_status}
                </span>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed">
                {scanResult.compliance_status === 'compliant'
                  ? 'All mandatory Legal Metrology declarations under Rule 6 and Rule 7 were detected on the package label.'
                  : 'The package is missing one or more mandatory statutory declarations or contains non-compliant phrasing under the Legal Metrology (Packaged Commodities) Rules, 2011.'}
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

              {/* Citizen Reporting Trigger Button */}
              {scanResult.compliance_status !== 'compliant' && (
                <div className="pt-3 flex items-center gap-3">
                  <button
                    onClick={() => setShowReportModal(true)}
                    className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold rounded-xl shadow-lg shadow-rose-900/40 transition flex items-center gap-2"
                  >
                    <AlertCircle size={15} />
                    <span>Report This Store & Product to Nearby Inspector</span>
                  </button>
                  <span className="text-[11px] text-rose-300/80">
                    Auto-captures your current GPS location & alerts Legal Metrology Officer.
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Success Banner when Report Submitted */}
          {reportSuccessMsg && (
            <div className="p-4 rounded-xl bg-emerald-950/60 border border-emerald-700/80 text-emerald-200 text-xs flex items-center justify-between shadow-lg">
              <div className="flex items-center gap-2">
                <CheckCircle2 size={18} className="text-emerald-400" />
                <span>{reportSuccessMsg}</span>
              </div>
              <button
                onClick={() => setReportSuccessMsg(null)}
                className="text-emerald-400 hover:text-white"
              >
                <X size={16} />
              </button>
            </div>
          )}

          {/* 2. Raw OCR Text Box */}
          <div className="bg-[#0c1220] border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  <FileText size={16} />
                </div>
                <div>
                  <h3 className="text-xs sm:text-sm font-bold text-white">
                    Raw Extracted OCR Text (All Detected Lines)
                  </h3>
                  <p className="text-[11px] text-slate-400">
                    Exact character strings extracted verbatim from the uploaded commodity package
                  </p>
                </div>
              </div>

              <button
                onClick={handleCopyRawText}
                className="inline-flex items-center gap-1 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg transition border border-slate-700"
              >
                {copiedRawText ? (
                  <>
                    <CheckCheck size={13} className="text-emerald-400" />
                    <span className="text-emerald-300 font-semibold">Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy size={13} />
                    <span>Copy Raw Text</span>
                  </>
                )}
              </button>
            </div>

            <div className="bg-[#060a12] border border-slate-800/90 rounded-xl p-4 font-mono text-xs text-slate-300 max-h-48 overflow-y-auto leading-relaxed whitespace-pre-wrap selection:bg-indigo-500/40">
              {scanResult.raw_text ? (
                scanResult.raw_text
              ) : (
                <span className="text-slate-500 italic">No text extracted from package.</span>
              )}
            </div>
          </div>

          {/* 2b. Prominent Detected Statutory Declarations (FSSAI, MRP, Batch, Dates) */}
          {scanResult.extracted_facts && (
            <div className="bg-[#0c1220] border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
              <div className="flex items-center gap-2 border-b border-slate-800/80 pb-3">
                <div className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  <Sparkles size={16} />
                </div>
                <div>
                  <h3 className="text-xs sm:text-sm font-bold text-white">
                    Key Extracted Declarations & Identifiers
                  </h3>
                  <p className="text-[11px] text-slate-400">
                    High-priority statutory values identified from package OCR
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {/* FSSAI Card */}
                <div className={`p-3 rounded-xl border ${
                  scanResult.extracted_facts.fssai 
                    ? 'bg-emerald-950/20 border-emerald-500/40 text-emerald-200' 
                    : 'bg-slate-900/40 border-slate-800 text-slate-400'
                }`}>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono uppercase tracking-wider font-semibold">
                      FSSAI Food Safety Lic.
                    </span>
                    {scanResult.extracted_facts.fssai ? (
                      <span className="px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-300 text-[10px] font-mono border border-emerald-500/40">
                        DETECTED
                      </span>
                    ) : (
                      <span className="px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 text-[10px] font-mono">
                        NOT FOUND
                      </span>
                    )}
                  </div>
                  <p className="text-xs font-bold text-white mt-1.5 truncate">
                    {scanResult.extracted_facts.fssai || 'Not detected on package'}
                  </p>
                </div>

                {/* Consumer Care */}
                <div className="p-3 rounded-xl border bg-slate-900/40 border-slate-800">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold block">
                    Consumer Grievance / Care
                  </span>
                  <p className="text-xs font-semibold text-white mt-1.5 truncate">
                    {scanResult.extracted_facts.customer_care || 'Not detected'}
                  </p>
                </div>

                {/* MRP */}
                <div className="p-3 rounded-xl border bg-slate-900/40 border-slate-800">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold block">
                    MRP & Taxes Declaration
                  </span>
                  <p className="text-xs font-semibold text-white mt-1.5 truncate">
                    {scanResult.extracted_facts.mrp || 'Not detected'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* 3. 10 Statutory Rules Verification Checklist */}
          <div className="bg-[#0c1220] border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-800/80 pb-4">
              <div>
                <h3 className="text-sm sm:text-base font-bold text-white flex items-center gap-2">
                  <CheckCircle2 size={18} className="text-indigo-400" />
                  <span>10 Statutory Legal Metrology Rules Checklist</span>
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Verification status based on targeted keyword detection and statutory requirements
                </p>
              </div>

              {/* Filter Pills */}
              <div className="flex items-center gap-1.5 p-1 bg-[#070c16] rounded-xl border border-slate-800 text-xs self-start sm:self-auto">
                <button
                  onClick={() => setFilterMode('all')}
                  className={`px-3 py-1 rounded-lg font-medium transition ${
                    filterMode === 'all'
                      ? 'bg-indigo-600 text-white shadow'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  All (10)
                </button>
                <button
                  onClick={() => setFilterMode('present')}
                  className={`px-3 py-1 rounded-lg font-medium transition flex items-center gap-1 ${
                    filterMode === 'present'
                      ? 'bg-emerald-600 text-white shadow'
                      : 'text-emerald-400 hover:text-emerald-300'
                  }`}
                >
                  <Check size={12} className="stroke-[3]" />
                  <span>Present ({presentCount})</span>
                </button>
                <button
                  onClick={() => setFilterMode('missing')}
                  className={`px-3 py-1 rounded-lg font-medium transition flex items-center gap-1 ${
                    filterMode === 'missing'
                      ? 'bg-rose-600 text-white shadow'
                      : 'text-rose-400 hover:text-rose-300'
                  }`}
                >
                  <X size={12} className="stroke-[3]" />
                  <span>Missing ({missingCount})</span>
                </button>
              </div>
            </div>

            {/* Checklist Cards */}
            <div className="space-y-3">
              {displayRules.map((rule, idx) => {
                const evalData = rule.evalData;
                const isPass = evalData?.isPass;

                return (
                  <div
                    key={rule.code}
                    className={`p-4 rounded-xl border transition-all ${
                      isPass
                        ? 'bg-[#080f1a] border-emerald-900/50 hover:border-emerald-700/60'
                        : 'bg-[#120a10] border-rose-900/50 hover:border-rose-700/60'
                    }`}
                  >
                    <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
                      {/* Left: Rule info */}
                      <div className="flex items-start gap-3 flex-1">
                        <div
                          className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border mt-0.5 ${
                            isPass
                              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                              : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                          }`}
                        >
                          {isPass ? (
                            <Check size={20} className="stroke-[3]" />
                          ) : (
                            <X size={20} className="stroke-[3]" />
                          )}
                        </div>

                        <div className="space-y-1.5 flex-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="text-xs font-mono font-bold text-white">
                              Rule {idx + 1}. {rule.title}
                            </span>
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800/90 text-slate-300 border border-slate-700">
                              {rule.code}
                            </span>
                          </div>

                          <p className="text-[11px] text-slate-400 leading-snug">
                            {rule.reference}
                          </p>

                          {/* Target Field and Keywords Badge */}
                          <div className="flex flex-wrap items-center gap-1.5 pt-1">
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-950/60 text-indigo-300 border border-indigo-800/80">
                              Target Field: <strong>{rule.targetField}</strong>
                            </span>
                            <span className="text-[10px] text-slate-500">
                              Keywords: {rule.keywords.slice(0, 3).map((kw) => `"${kw}"`).join(', ')}
                            </span>
                          </div>

                          {/* Detected Snippet or Failure Reason */}
                          <div
                            className={`p-2.5 rounded-lg text-xs mt-2 border ${
                              isPass
                                ? 'bg-emerald-950/30 border-emerald-900/60 text-emerald-300'
                                : 'bg-rose-950/30 border-rose-900/60 text-rose-300'
                            }`}
                          >
                            <span className="font-semibold block text-[11px] uppercase tracking-wider mb-0.5">
                              {isPass ? '✓ Verified Declaration:' : '✗ Statutory Non-Compliance:'}
                            </span>
                            <p className="leading-relaxed">
                              {evalData?.detectedText || evalData?.reason}
                            </p>
                          </div>
                        </div>
                      </div>

                      {/* Right: Big Status Badge */}
                      <div className="shrink-0 self-start sm:self-center">
                        <span
                          className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
                            isPass
                              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-sm shadow-emerald-500/10'
                              : 'bg-rose-500/20 text-rose-300 border border-rose-500/40 shadow-sm shadow-rose-500/10'
                          }`}
                        >
                          {isPass ? (
                            <>
                              <Check size={14} className="stroke-[3]" />
                              <span>Present</span>
                            </>
                          ) : (
                            <>
                              <X size={14} className="stroke-[3]" />
                              <span>Missing</span>
                            </>
                          )}
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Statutory Rules Standards Reference */}
      <div className="bg-[#0c1220] border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
          <div>
            <h2 className="text-sm sm:text-base font-bold text-white">Legal Metrology Declarations Standards</h2>
            <p className="text-xs text-slate-400">Statutory declarations enforced by the Department of Consumer Affairs</p>
          </div>
          <Link
            to="/customer/rules"
            className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
          >
            <span>View Rule Book</span>
            <ChevronRight size={14} />
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
                <div key={r.id || r.rule_code} className="p-3 bg-[#080d18] border border-slate-800 rounded-lg flex items-center justify-between">
                  <div>
                    <div className="text-xs font-medium text-white">{r.rule_code || r.name || 'Statutory Rule'}</div>
                    <div className="text-[11px] text-slate-400">
                      {r.category} &bull; Section: {version.statutory_reference || r.rule_reference || 'LMPC Rules, 2011'}
                    </div>
                  </div>
                  <StatusBadge status={version.verification_status || r.verification_status || 'demo'} />
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Citizen Geo-Reporting Modal */}
      {showReportModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-[#0f172a] border border-slate-700 rounded-2xl w-full max-w-lg p-6 shadow-2xl space-y-4 animate-in fade-in zoom-in duration-200">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2 text-rose-400">
                <AlertCircle size={20} />
                <h3 className="text-base font-bold text-white">Report Non-Compliant Product</h3>
              </div>
              <button
                onClick={() => setShowReportModal(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition"
              >
                <X size={18} />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="p-3 bg-slate-900 rounded-xl border border-slate-800 space-y-1">
                <span className="text-slate-400 font-medium block">Detected Non-Compliances:</span>
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {(scanResult?.violations || []).map((v) => (
                    <span key={v.rule_code} className="px-2 py-0.5 rounded bg-rose-950/80 border border-rose-800/80 text-rose-300 font-mono text-[11px]">
                      {v.rule_code}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">
                  Select Retail Store / Establishment:
                </label>
                <select
                  value={selectedStoreId}
                  onChange={(e) => setSelectedStoreId(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500"
                >
                  {stores.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.business_name} — {s.shop_address}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">
                  Observation / Comments (Optional):
                </label>
                <textarea
                  rows={3}
                  value={reportNotes}
                  onChange={(e) => setReportNotes(e.target.value)}
                  placeholder="e.g., Shopkeeper charged ₹10 above MRP / MRP sticker pasted over original print."
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex items-center gap-2 text-slate-400 text-[11px] pt-1">
                <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
                <span>GPS Location Coordinates will be tagged automatically to alert nearby Officer.</span>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-slate-800">
              <button
                onClick={() => setShowReportModal(false)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmitGeoReport}
                disabled={reporting}
                className="px-5 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold transition shadow-lg shadow-rose-900/40 flex items-center gap-1.5 disabled:opacity-50"
              >
                {reporting ? <RefreshCw size={14} className="animate-spin" /> : <AlertCircle size={14} />}
                <span>{reporting ? 'Dispatching...' : 'Confirm & Dispatch Report'}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
