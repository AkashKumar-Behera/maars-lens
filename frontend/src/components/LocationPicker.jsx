import { useState, useEffect } from 'react';
import { MapPin, Navigation } from 'lucide-react';

const LocationPicker = ({ onLocationChange }) => {
  const [districts] = useState(['Mumbai Central', 'Pune Urban', 'Nagpur District', 'New Delhi Central', 'Bengaluru South']);
  const [wards] = useState(['Ward A - Commercial Hub', 'Ward B - Industrial Estate', 'Ward C - Retail Market', 'Ward D - Logistics Zone']);
  const [areas] = useState(['Connaught Place Market', 'Andheri West Suburb', 'Bandra Commercial Complex', 'Karol Bagh Market', 'Indiranagar Central']);
  
  const [selection, setSelection] = useState({ district: '', ward: '', area: '', gps: null });

  useEffect(() => {
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition((pos) => {
        const coords = { lat: pos.coords.latitude, lng: pos.coords.longitude };
        setSelection(s => ({ ...s, gps: coords }));
        if (onLocationChange) onLocationChange({ ...selection, gps: coords });
      }, () => {
        // Fallback default coordinates
        const fallbackCoords = { lat: 20.1611, lng: 85.8822 };
        setSelection(s => ({ ...s, gps: fallbackCoords }));
        if (onLocationChange) onLocationChange({ ...selection, gps: fallbackCoords });
      });
    }
  }, []);

  const handleChange = (field, value) => {
    const newSel = { ...selection, [field]: value };
    setSelection(newSel);
    if (onLocationChange) onLocationChange(newSel);
  };

  return (
    <div className="bg-slate-950/60 border border-slate-800/90 rounded-2xl p-4 sm:p-5 shadow-inner space-y-3.5 backdrop-blur-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center text-xs font-bold text-indigo-400 uppercase tracking-wider">
          <MapPin size={16} className="mr-2 text-indigo-400" />
          Jurisdiction & Physical Location Details
        </div>
        {selection.gps && (
          <div className="text-[11px] text-emerald-400 flex items-center font-mono bg-emerald-950/40 border border-emerald-800/60 px-2.5 py-0.5 rounded-full">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-2 animate-pulse" />
            GPS: {selection.gps.lat.toFixed(4)}, {selection.gps.lng.toFixed(4)}
          </div>
        )}
      </div>
      
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div>
          <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider mb-1">
            Enforcement District
          </label>
          <select 
            value={selection.district} 
            onChange={(e) => handleChange('district', e.target.value)}
            className="w-full bg-slate-900/90 border border-slate-700/80 rounded-xl text-white text-xs px-3 py-2 shadow-inner focus:outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-400 transition hover:border-slate-600 cursor-pointer"
          >
            <option value="" className="bg-slate-900 text-slate-400">Select District</option>
            {districts.map(d => <option key={d} value={d} className="bg-slate-900 text-white">{d}</option>)}
          </select>
        </div>

        <div>
          <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider mb-1">
            Administrative Ward
          </label>
          <select 
            value={selection.ward} 
            onChange={(e) => handleChange('ward', e.target.value)}
            className="w-full bg-slate-900/90 border border-slate-700/80 rounded-xl text-white text-xs px-3 py-2 shadow-inner focus:outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-400 transition hover:border-slate-600 cursor-pointer"
          >
            <option value="" className="bg-slate-900 text-slate-400">Select Ward</option>
            {wards.map(w => <option key={w} value={w} className="bg-slate-900 text-white">{w}</option>)}
          </select>
        </div>

        <div>
          <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider mb-1">
            Jurisdiction Area / Market
          </label>
          <select 
            value={selection.area} 
            onChange={(e) => handleChange('area', e.target.value)}
            className="w-full bg-slate-900/90 border border-slate-700/80 rounded-xl text-white text-xs px-3 py-2 shadow-inner focus:outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-400 transition hover:border-slate-600 cursor-pointer"
          >
            <option value="" className="bg-slate-900 text-slate-400">Select Area</option>
            {areas.map(a => <option key={a} value={a} className="bg-slate-900 text-white">{a}</option>)}
          </select>
        </div>
      </div>
    </div>
  );
};

export default LocationPicker;
