import { useState, useEffect } from 'react';
import { MapPin } from 'lucide-react';

const LocationPicker = ({ onLocationChange }) => {
  const [districts] = useState(['Mumbai', 'Pune', 'Nagpur']);
  const [wards] = useState(['Ward A', 'Ward B', 'Ward C']);
  const [areas] = useState(['Andheri', 'Bandra', 'Colaba']);
  
  const [selection, setSelection] = useState({ district: '', ward: '', area: '', gps: null });

  useEffect(() => {
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition((pos) => {
        const coords = { lat: pos.coords.latitude, lng: pos.coords.longitude };
        setSelection(s => ({ ...s, gps: coords }));
        onLocationChange({ ...selection, gps: coords });
      }, () => {
        console.log("GPS not available");
      });
    }
  }, []);

  const handleChange = (field, value) => {
    const newSel = { ...selection, [field]: value };
    setSelection(newSel);
    onLocationChange(newSel);
  };

  return (
    <div className="bg-white p-4 border rounded-md shadow-sm space-y-4">
      <div className="flex items-center text-indigo-700 font-medium mb-2">
        <MapPin size={20} className="mr-2" />
        Location Details
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">District</label>
          <select 
            value={selection.district} 
            onChange={(e) => handleChange('district', e.target.value)}
            className="w-full border-gray-300 rounded-md shadow-sm p-2 border"
          >
            <option value="">Select District</option>
            {districts.map(d => <option key={d} value={d}>{d}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Ward</label>
          <select 
            value={selection.ward} 
            onChange={(e) => handleChange('ward', e.target.value)}
            className="w-full border-gray-300 rounded-md shadow-sm p-2 border"
          >
            <option value="">Select Ward</option>
            {wards.map(w => <option key={w} value={w}>{w}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Area</label>
          <select 
            value={selection.area} 
            onChange={(e) => handleChange('area', e.target.value)}
            className="w-full border-gray-300 rounded-md shadow-sm p-2 border"
          >
            <option value="">Select Area</option>
            {areas.map(a => <option key={a} value={a}>{a}</option>)}
          </select>
        </div>
      </div>
      
      {selection.gps && (
        <div className="text-xs text-gray-500 flex items-center mt-2">
          <span className="w-2 h-2 rounded-full bg-green-500 mr-2"></span>
          GPS Captured: {selection.gps.lat.toFixed(4)}, {selection.gps.lng.toFixed(4)}
        </div>
      )}
    </div>
  );
};

export default LocationPicker;
