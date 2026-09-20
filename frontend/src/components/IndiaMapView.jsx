import React, { useEffect, useRef, useState } from 'react';
import { Map, NavigationControl, Marker, Popup } from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

const MAPTILER_API_KEY = 'IG8L4cXU4hvolM8F63k6';

export default function IndiaMapView({ incidents = [], onSelectIncident = null, height = '450px' }) {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const [mapLoaded, setMapLoaded] = useState(false);

  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    try {
      const m = new Map({
        container: mapContainer.current,
        style: `https://api.maptiler.com/maps/streets-v2-dark/style.json?key=${MAPTILER_API_KEY}`,
        center: [78.9629, 21.5937], // Center of India
        zoom: 4.2,
        maxZoom: 16,
        minZoom: 3,
        attributionControl: false,
      });

      m.addControl(new NavigationControl({ showCompass: true }), 'top-right');

      m.on('load', () => {
        setMapLoaded(true);
        m.resize();
      });

      // Handle fallback if custom style fails
      m.on('error', (e) => {
        console.warn('MapLibre error or style issue:', e);
      });

      // Trigger resize after small delay to handle flex/grid layout settle
      setTimeout(() => {
        if (m) m.resize();
      }, 500);

      map.current = m;
    } catch (err) {
      console.error('Error initializing map:', err);
    }

    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, []);

  // Update markers when incidents change
  useEffect(() => {
    if (!map.current) return;

    // Remove existing markers if any
    const markers = [];

    incidents.forEach((inc) => {
      const lat = inc.gps_lat || (inc.geometry && inc.geometry.coordinates[1]);
      const lng = inc.gps_lng || (inc.geometry && inc.geometry.coordinates[0]);

      if (!lat || !lng) return;

      const props = inc.properties || inc;
      const isEscalated = props.escalated || inc.escalated_to_admin;
      const isResolved = props.status === 'resolved' || inc.status === 'resolved';

      // Custom marker DOM element
      const el = document.createElement('div');
      el.className = `flex items-center justify-center cursor-pointer transition transform hover:scale-125`;
      
      let badgeColor = 'bg-rose-500 border-rose-300';
      if (isResolved) badgeColor = 'bg-emerald-500 border-emerald-300';
      else if (isEscalated) badgeColor = 'bg-amber-500 border-amber-300 map-marker-pulse';

      el.innerHTML = `
        <div class="relative flex items-center justify-center">
          <div class="w-6 h-6 rounded-full ${badgeColor} border-2 shadow-lg flex items-center justify-center text-white text-xs font-bold">
            ${isResolved ? '✓' : '!'}
          </div>
        </div>
      `;

      // Popup
      const popup = new Popup({ offset: 25, closeButton: true }).setHTML(`
        <div style="color: #0f172a; padding: 6px; font-family: sans-serif; font-size: 12px; min-width: 180px;">
          <strong style="font-size: 13px; color: #1e293b; display: block; margin-bottom: 4px;">
            ${props.product_name || inc.product_name || 'Product Incident'}
          </strong>
          <div style="margin-bottom: 3px; color: #64748b;">
            <strong>Status:</strong> <span style="text-transform: uppercase; font-weight: 600; color: ${isResolved ? '#059669' : '#dc2626'};">${props.status || inc.status}</span>
          </div>
          <div style="margin-bottom: 3px; color: #475569;">
            <strong>Store:</strong> ${props.retailer_name || inc.retailer_name || 'Retailer Store'}
          </div>
          ${(props.failing_rule_codes || inc.failing_rule_codes || []).length > 0 ? `
            <div style="margin-top: 4px; padding: 4px; background: #fee2e2; border-radius: 4px; color: #991b1b; font-size: 11px;">
              Violations: ${(props.failing_rule_codes || inc.failing_rule_codes || []).join(', ')}
            </div>
          ` : ''}
        </div>
      `);

      el.addEventListener('click', () => {
        if (onSelectIncident) {
          onSelectIncident(inc);
        }
      });

      const marker = new Marker({ element: el })
        .setLngLat([lng, lat])
        .setPopup(popup)
        .addTo(map.current);

      markers.push(marker);
    });

    return () => {
      markers.forEach((m) => m.remove());
    };
  }, [incidents, onSelectIncident]);

  return (
    <div className="relative rounded-2xl overflow-hidden border border-slate-800 shadow-2xl bg-slate-900/80 backdrop-blur-md">
      {/* Top Map Header Badge */}
      <div className="absolute top-3 left-3 z-10 bg-slate-950/80 backdrop-blur-md px-3.5 py-1.5 rounded-xl border border-slate-700/60 flex items-center gap-2 text-xs shadow-md">
        <span className="h-2 w-2 rounded-full bg-rose-500 animate-ping"></span>
        <span className="font-semibold text-slate-200">MapTiler India Legal Metrology Radar</span>
        <span className="text-slate-400 font-mono text-[10px] ml-1">Live Incidents ({incidents.length})</span>
      </div>

      {/* Map Container */}
      <div ref={mapContainer} style={{ width: '100%', height }} />

      {/* Map Legend */}
      <div className="absolute bottom-3 left-3 z-10 bg-slate-950/85 backdrop-blur-md px-3 py-1.5 rounded-xl border border-slate-800 flex items-center gap-3 text-[11px] text-slate-300 shadow">
        <div className="flex items-center gap-1">
          <span className="w-2.5 h-2.5 rounded-full bg-rose-500 inline-block"></span>
          <span>Violation</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block"></span>
          <span>Escalated</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block"></span>
          <span>Resolved</span>
        </div>
      </div>
    </div>
  );
}
