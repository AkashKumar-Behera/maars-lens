import React from 'react';

export default function MetrologyHeroVector({ className = "w-full max-h-52" }) {
  return (
    <div className={`relative flex items-center justify-center ${className}`}>
      <svg 
        viewBox="0 0 540 260" 
        className="w-full h-full" 
        fill="none" 
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          {/* Gradients */}
          <linearGradient id="gridGlow" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#4f46e5" stopOpacity="0.15" />
            <stop offset="100%" stopColor="#06b6d4" stopOpacity="0.05" />
          </linearGradient>
          <linearGradient id="pkgBlue" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#2563eb" />
            <stop offset="100%" stopColor="#1e40af" />
          </linearGradient>
          <linearGradient id="scaleGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#1e293b" />
            <stop offset="100%" stopColor="#0f172a" />
          </linearGradient>
          <linearGradient id="scanBeam" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#38bdf8" stopOpacity="0" />
          </linearGradient>
          <linearGradient id="lcdScreen" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#082f49" />
            <stop offset="100%" stopColor="#0369a1" />
          </linearGradient>
        </defs>

        {/* Ambient Grid Backdrop */}
        <rect x="20" y="15" width="500" height="230" rx="16" fill="url(#gridGlow)" stroke="#334155" strokeWidth="1" strokeDasharray="4 4" />

        {/* ---------------- 1. Packaged Commodity with Label ---------------- */}
        <g transform="translate(45, 55)">
          {/* 3D Box Body */}
          <path d="M10 40 L65 15 L170 30 L115 55 Z" fill="#3b82f6" opacity="0.9" />
          <path d="M10 40 L115 55 L115 130 L10 115 Z" fill="url(#pkgBlue)" />
          <path d="M115 55 L170 30 L170 105 L115 130 Z" fill="#1d4ed8" />

          {/* Commodity Label Sheet */}
          <path d="M22 52 L105 64 L105 118 L22 106 Z" fill="#f8fafc" rx="3" />
          
          {/* Barcode Lines */}
          <g transform="translate(30, 68)">
            <rect x="0" y="0" width="2.5" height="22" fill="#0f172a" />
            <rect x="4" y="0" width="1.5" height="22" fill="#0f172a" />
            <rect x="7.5" y="0" width="3.5" height="22" fill="#0f172a" />
            <rect x="13" y="0" width="1.5" height="22" fill="#0f172a" />
            <rect x="16" y="0" width="3" height="22" fill="#0f172a" />
            <rect x="21" y="0" width="1" height="22" fill="#0f172a" />
            <rect x="24" y="0" width="4" height="22" fill="#0f172a" />
            <rect x="30" y="0" width="1.5" height="22" fill="#0f172a" />
            <rect x="33.5" y="0" width="2.5" height="22" fill="#0f172a" />
            <rect x="38" y="0" width="3.5" height="22" fill="#0f172a" />
          </g>

          {/* QR Code Matrix Box */}
          <g transform="translate(76, 68)">
            <rect x="0" y="0" width="22" height="22" fill="#0f172a" rx="1.5" />
            <rect x="2" y="2" width="6" height="6" fill="#f8fafc" />
            <rect x="14" y="2" width="6" height="6" fill="#f8fafc" />
            <rect x="2" y="14" width="6" height="6" fill="#f8fafc" />
            <rect x="4" y="4" width="2" height="2" fill="#0f172a" />
            <rect x="16" y="4" width="2" height="2" fill="#0f172a" />
            <rect x="4" y="16" width="2" height="2" fill="#0f172a" />
            <rect x="10" y="10" width="2" height="2" fill="#f8fafc" />
            <rect x="14" y="14" width="4" height="4" fill="#f8fafc" />
          </g>

          {/* Mandatory Declarations text simulation (Rule 6) */}
          <g transform="translate(30, 96)">
            <text x="0" y="0" fontSize="5.5" fontWeight="bold" fill="#0f172a" fontFamily="monospace">MRP ₹ 249.00 (INCL TAXES)</text>
            <text x="0" y="6.5" fontSize="5" fontWeight="bold" fill="#334155" fontFamily="monospace">NET QTY: 500 g | PKG: 09/26</text>
          </g>

          {/* Real-time Optical Laser Line */}
          <line x1="15" y1="78" x2="112" y2="78" stroke="#38bdf8" strokeWidth="1.5" filter="drop-shadow(0 0 4px #38bdf8)" />
          <polygon points="15,62 112,62 112,78 15,78" fill="url(#scanBeam)" opacity="0.35" />
        </g>

        {/* ---------------- 2. Digital Weighing Platform Scale ---------------- */}
        <g transform="translate(250, 65)">
          {/* Base Platform */}
          <path d="M15 50 L115 15 L225 35 L125 70 Z" fill="#334155" />
          {/* Stainless Platter */}
          <path d="M22 47 L112 18 L218 36 L128 65 Z" fill="#64748b" stroke="#94a3b8" strokeWidth="1" />
          
          {/* Lower Scale Chassis */}
          <path d="M15 50 L125 70 L125 105 L15 85 Z" fill="url(#scaleGrad)" stroke="#1e293b" />
          <path d="M125 70 L225 35 L225 70 L125 105 Z" fill="#0f172a" stroke="#1e293b" />

          {/* Digital LCD Indicator Panel */}
          <g transform="translate(35, 76)">
            <rect x="0" y="0" width="70" height="22" rx="4" fill="url(#lcdScreen)" stroke="#0284c7" strokeWidth="1" />
            <text x="8" y="16" fontSize="13" fontWeight="bold" fill="#38bdf8" fontFamily="monospace" letterSpacing="1">
              500.00
            </text>
            <text x="56" y="15" fontSize="8" fontWeight="bold" fill="#7dd3fc" fontFamily="sans-serif">
              g
            </text>
            {/* Tare & Zero Indicator dots */}
            <circle cx="8" cy="5" r="1.2" fill="#4ade80" />
            <circle cx="15" cy="5" r="1.2" fill="#38bdf8" />
          </g>

          {/* Precision Keypad buttons */}
          <circle cx="115" cy="84" r="3" fill="#1e293b" stroke="#475569" strokeWidth="0.8" />
          <circle cx="115" cy="94" r="3" fill="#0284c7" />
          <circle cx="125" cy="84" r="3" fill="#1e293b" stroke="#475569" strokeWidth="0.8" />
          <circle cx="125" cy="94" r="3" fill="#10b981" />
        </g>

        {/* ---------------- 3. Central Verification Audit Seal ---------------- */}
        <g transform="translate(230, 160)">
          {/* Shield Badge */}
          <circle cx="40" cy="40" r="34" fill="#020617" stroke="#4f46e5" strokeWidth="2" filter="drop-shadow(0 4px 12px rgba(79,70,229,0.3))" />
          <circle cx="40" cy="40" r="28" fill="none" stroke="#22c55e" strokeWidth="1.5" strokeDasharray="3 2" />
          
          {/* Checkmark Icon */}
          <path d="M28 40 L36 48 L52 30" stroke="#22c55e" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round" />
          
          {/* Small Trust Ribbon */}
          <rect x="8" y="60" width="64" height="15" rx="4" fill="#1e1b4b" stroke="#6366f1" strokeWidth="1" />
          <text x="40" y="70.5" textAnchor="middle" fontSize="7.5" fontWeight="bold" fill="#a5b4fc" fontFamily="sans-serif" letterSpacing="0.6">
            LMPC VERIFIED
          </text>
        </g>
      </svg>
    </div>
  );
}
