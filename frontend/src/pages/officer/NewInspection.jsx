import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { uploadScanApi, uploadInspectionImagesApi, scanListingApi } from '../../api/scans';
import { listAreasApi } from '../../api/areas';
import ImageUpload from '../../components/ImageUpload';
import LocationPicker from '../../components/LocationPicker';
import {
  Camera,
  CheckCircle2,
  AlertCircle,
  FileText,
  Building2,
  Tag,
  ArrowRight,
  ShieldAlert,
} from 'lucide-react';

const NewInspection = () => {
  const navigate = useNavigate();
  const [scanMode, setScanMode] = useState('physical'); // 'physical' or 'listing'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [productName, setProductName] = useState('');
  const [brandName, setBrandName] = useState('');
  const [location, setLocation] = useState({ district: '', ward: '', area: '', gps: null });
  const [selectedAreaId, setSelectedAreaId] = useState('b0000000-0000-0000-0000-000000000002');
  const [areas, setAreas] = useState([]);
  const [packageWidth, setPackageWidth] = useState('');
  const [packageHeight, setPackageHeight] = useState('');

  const [listingPastedText, setListingPastedText] = useState('');
  const [listingTitle, setListingTitle] = useState('');
  const [listingBrand, setListingBrand] = useState('');
  const [listingMrp, setListingMrp] = useState('');
  const [listingNetQty, setListingNetQty] = useState('');
  const [panels, setPanels] = useState([{ id: 1, type: 'front', file: null, preview: null }]);

  useEffect(() => {
    const fetchAreas = async () => {
      try {
        const data = await listAreasApi();
        if (Array.isArray(data) && data.length > 0) {
          setAreas(data);
          setSelectedAreaId(data[0].id);
        }
      } catch (err) {
        console.warn('Failed to load areas from backend, using default area ID:', err);
      }
    };
    fetchAreas();
  }, []);

  const handlePanelFileChange = (index, selectedFile) => {
    const updated = [...panels];
    updated[index].file = selectedFile;
    if (selectedFile) {
      const reader = new FileReader();
      reader.onloadend = () => {
        updated[index].preview = reader.result;
        setPanels([...updated]);
      };
      reader.readAsDataURL(selectedFile);
    } else {
      updated[index].preview = null;
      setPanels([...updated]);
    }
  };

  const handlePanelTypeChange = (index, type) => {
    const updated = [...panels];
    updated[index].type = type;
    setPanels(updated);
  };

  const addPanel = () => {
    if (panels.length < 5) {
      setPanels([...panels, { id: Date.now(), type: 'back', file: null, preview: null }]);
    }
  };

  const removePanel = (index) => {
    if (panels.length > 1) {
      const updated = panels.filter((_, i) => i !== index);
      setPanels(updated);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const validPanels = panels.filter((p) => p.file !== null);
    if (validPanels.length === 0) {
      setError('Please capture or upload at least one commodity label panel image.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const clientSubmissionId = crypto.randomUUID();
      const areaId = selectedAreaId || '33333333-3333-3333-3333-333333333333';
      const retailerId = null;

      const payload = {
        client_submission_id: clientSubmissionId,
        area_id: areaId,
        retailer_id: retailerId,
        product_name: productName || 'Packaged Commodity',
        brand_name: brandName || null,
        gps_lat: location.gps?.lat || null,
        gps_lng: location.gps?.lng || null,
      };

      // 1. Create inspection session record
      const result = await uploadScanApi(payload);
      const inspectionId = result.inspection_id;

      // 2. Upload panels to multi-panel OCR pipeline
      const formData = new FormData();
      validPanels.forEach((p) => {
        formData.append('files', p.file);
        formData.append('panel_types', p.type);
      });
      if (packageWidth) formData.append('pack_width_mm', packageWidth);
      if (packageHeight) formData.append('pack_height_mm', packageHeight);

      await uploadInspectionImagesApi(inspectionId, formData);

      // 3. Navigate to inspection details / review screen
      navigate(`/officer/inspections/${inspectionId}`);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to upload and process inspection scans');
    } finally {
      setLoading(false);
    }
  };

  const handleListingSubmit = async (e) => {
    e.preventDefault();
    if (!listingPastedText.trim() && !listingTitle.trim() && !listingMrp.trim()) {
      setError('Please provide either pasted listing text or key commodity declarations.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const areaId = selectedAreaId || 'b0000000-0000-0000-0000-000000000002';
      const payload = {
        area_id: areaId,
        title: listingTitle.trim() || undefined,
        brand: listingBrand.trim() || undefined,
        mrp: listingMrp.trim() || undefined,
        net_quantity: listingNetQty.trim() || undefined,
        pasted_text: listingPastedText.trim() || undefined,
      };

      const res = await scanListingApi(payload);
      navigate(`/officer/inspections/${res.inspection_id}`);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to evaluate e-commerce listing');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">New Commodity Inspection</h1>
        <p className="text-sm text-slate-400 mt-1">
          Capture package display panel, verify OCR-extracted declarations, and assess statutory compliance.
        </p>
      </div>

      {error && (
        <div className="p-4 bg-rose-950/60 border border-rose-800 rounded-xl text-rose-300 text-sm flex items-start space-x-2">
          <AlertCircle size={18} className="shrink-0 mt-0.5 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Mode Selector Tabs */}
      <div className="flex border-b border-slate-700 space-x-4">
        <button
          type="button"
          onClick={() => setScanMode('physical')}
          className={`pb-3 text-sm font-semibold border-b-2 flex items-center space-x-2 transition ${
            scanMode === 'physical'
              ? 'border-indigo-500 text-white'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Camera size={18} />
          <span>Physical Package Scan (Multi-Panel OCR)</span>
        </button>
        <button
          type="button"
          onClick={() => setScanMode('listing')}
          className={`pb-3 text-sm font-semibold border-b-2 flex items-center space-x-2 transition ${
            scanMode === 'listing'
              ? 'border-indigo-500 text-white'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <FileText size={18} />
          <span>E-Commerce Listing Scan (Pasted Text / Fields)</span>
        </button>
      </div>

      {scanMode === 'listing' ? (
        <form onSubmit={handleListingSubmit} className="space-y-6">
          <div className="bg-slate-800/90 border border-slate-700/80 rounded-xl p-6 shadow-lg space-y-4">
            <h2 className="text-base font-semibold text-white flex items-center space-x-2">
              <FileText size={20} className="text-indigo-400" />
              <span>E-Commerce Commodity Listing Details</span>
            </h2>
            <p className="text-xs text-slate-400">
              Paste the text content from an e-commerce product page (Amazon, Blinkit, Flipkart, etc.) or fill out known declarations to audit digital compliance under Legal Metrology E-Commerce Rules.
            </p>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                Pasted Product Listing Text
              </label>
              <textarea
                rows={5}
                value={listingPastedText}
                onChange={(e) => setListingPastedText(e.target.value)}
                placeholder="Paste commodity description, specifications, price, net quantity, manufacturer, and customer care details..."
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                  Product / Title
                </label>
                <input
                  type="text"
                  value={listingTitle}
                  onChange={(e) => setListingTitle(e.target.value)}
                  placeholder="e.g. Organic Rolled Oats 1kg"
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                  Brand Name
                </label>
                <input
                  type="text"
                  value={listingBrand}
                  onChange={(e) => setListingBrand(e.target.value)}
                  placeholder="e.g. HealthGrains"
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                  Maximum Retail Price (MRP)
                </label>
                <input
                  type="text"
                  value={listingMrp}
                  onChange={(e) => setListingMrp(e.target.value)}
                  placeholder="e.g. Rs. 350 (incl. of all taxes)"
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                  Net Quantity
                </label>
                <input
                  type="text"
                  value={listingNetQty}
                  onChange={(e) => setListingNetQty(e.target.value)}
                  placeholder="e.g. 1000g or 1kg"
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                type="submit"
                disabled={loading}
                className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold rounded-xl shadow-lg transition text-sm flex items-center space-x-2"
              >
                <span>{loading ? 'Evaluating Listing...' : 'Audit Listing Compliance'}</span>
                <ArrowRight size={16} />
              </button>
            </div>
          </div>
        </form>
      ) : (
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Step 1: Multi-Panel Image Capture */}
        <div className="bg-slate-800/90 border border-slate-700/80 rounded-xl p-6 shadow-lg space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-white flex items-center space-x-2">
              <Camera size={20} className="text-indigo-400" />
              <span>1. Package Display Panels (Multi-Panel OCR)</span>
            </h2>
            {panels.length < 5 && (
              <button
                type="button"
                onClick={addPanel}
                className="px-3 py-1 bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs font-semibold rounded-lg transition"
              >
                + Add Another Panel (Side/Back)
              </button>
            )}
          </div>

          <p className="text-xs text-slate-400">
            Upload images of all relevant commodity panels (front, back, side, top) to aggregate mandatory Legal Metrology declarations.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {panels.map((p, idx) => (
              <div key={p.id} className="p-4 bg-slate-900/60 border border-slate-700/60 rounded-xl space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-300 uppercase">Panel #{idx + 1}</span>
                  <div className="flex items-center space-x-2">
                    <select
                      value={p.type}
                      onChange={(e) => handlePanelTypeChange(idx, e.target.value)}
                      className="px-2 py-1 bg-slate-800 border border-slate-600 rounded text-xs text-white"
                    >
                      <option value="front">Principal Display Panel (Front)</option>
                      <option value="back">Back Panel (Information)</option>
                      <option value="side">Side Panel</option>
                      <option value="top">Top / Bottom Panel</option>
                      <option value="other">Other Panel</option>
                    </select>
                    {panels.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removePanel(idx)}
                        className="text-rose-400 hover:text-rose-300 text-xs font-bold px-2 py-1"
                      >
                        Remove
                      </button>
                    )}
                  </div>
                </div>

                {!p.preview ? (
                  <div
                    className="border border-dashed border-slate-700 rounded-lg p-4 text-center cursor-pointer hover:bg-slate-800/50 transition"
                    onClick={() => document.getElementById(`panel-input-${idx}`)?.click()}
                  >
                    <Camera size={24} className="mx-auto text-indigo-400 mb-1" />
                    <p className="text-xs text-slate-300 font-medium">Click to select panel image</p>
                    <input
                      id={`panel-input-${idx}`}
                      type="file"
                      accept="image/jpeg,image/png,image/webp"
                      className="hidden"
                      onChange={(e) => handlePanelFileChange(idx, e.target.files[0] || null)}
                    />
                  </div>
                ) : (
                  <div className="relative rounded-lg overflow-hidden border border-slate-700">
                    <img src={p.preview} alt={`Panel ${idx + 1}`} className="w-full h-40 object-cover bg-black" />
                    <button
                      type="button"
                      onClick={() => handlePanelFileChange(idx, null)}
                      className="absolute bottom-2 right-2 px-2 py-1 bg-black/80 hover:bg-black text-white text-[10px] rounded font-semibold"
                    >
                      Change
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Step 2: Commodity Metadata */}
        <div className="bg-slate-800/90 border border-slate-700/80 rounded-xl p-6 shadow-lg space-y-4">
          <h2 className="text-base font-semibold text-white mb-2 flex items-center space-x-2">
            <Tag size={20} className="text-indigo-400" />
            <span>2. Commodity Information (Optional Field Notes)</span>
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                Product / Commodity Name
              </label>
              <input
                type="text"
                value={productName}
                onChange={(e) => setProductName(e.target.value)}
                placeholder="e.g. Basmati Rice 5kg, Sunflower Oil 1L"
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                Brand / Manufacturer Name
              </label>
              <input
                type="text"
                value={brandName}
                onChange={(e) => setBrandName(e.target.value)}
                placeholder="e.g. Himalayan Harvest Foods"
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>
        </div>

        {/* Step 3: Location Details */}
        <div className="bg-slate-800/90 border border-slate-700/80 rounded-xl p-6 shadow-lg space-y-4">
          <h2 className="text-base font-semibold text-white mb-2 flex items-center space-x-2">
            <Building2 size={20} className="text-indigo-400" />
            <span>3. Enforcement Jurisdiction & Location</span>
          </h2>
          {areas.length > 0 && (
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                Designated Enforcement Zone
              </label>
              <select
                value={selectedAreaId}
                onChange={(e) => setSelectedAreaId(e.target.value)}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {areas.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.name} ({a.area_type})
                  </option>
                ))}
              </select>
            </div>
          )}
          <LocationPicker onLocationChange={(loc) => setLocation(loc)} />
        </div>

        {/* Step 4: Physical Dimension Calibration (Rule 7 Font Verification) */}
        <div className="bg-slate-800/90 border border-slate-700/80 rounded-xl p-6 shadow-lg space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-white flex items-center space-x-2">
              <ShieldAlert size={20} className="text-indigo-400" />
              <span>4. Physical Package Calibration (Optional for Font Height Verification)</span>
            </h2>
            <span className="text-[10px] uppercase font-mono px-2 py-0.5 bg-amber-500/10 text-amber-300 border border-amber-500/20 rounded">
              Rule 7 Calibration
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Digital 2D scans lack physical scale. Enter the measured package dimensions to compute estimated numeral heights against statutory minimum requirements. If omitted, font height rules will be flagged as <em>"Needs Manual Review"</em>.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                Measured Package Width (mm)
              </label>
              <input
                type="number"
                step="0.1"
                value={packageWidth}
                onChange={(e) => setPackageWidth(e.target.value)}
                placeholder="e.g. 120"
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                Measured Package Height (mm)
              </label>
              <input
                type="number"
                step="0.1"
                value={packageHeight}
                onChange={(e) => setPackageHeight(e.target.value)}
                placeholder="e.g. 180"
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>
        </div>

        {/* Submit Bar */}
        <div className="flex justify-end space-x-3 pt-2">
          <button
            type="submit"
            disabled={loading}
            className="flex items-center space-x-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold rounded-xl shadow-lg shadow-indigo-600/30 transition text-sm"
          >
            {loading ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>Submitting & Initializing Audit...</span>
              </>
            ) : (
              <>
                <span>Submit for Legal Metrology Audit</span>
                <ArrowRight size={16} />
              </>
            )}
          </button>
        </div>
      </form>
      )}
    </div>
  );
};

export default NewInspection;
