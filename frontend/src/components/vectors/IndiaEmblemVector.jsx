import React from 'react';

export default function IndiaEmblemVector({ className = "h-11" }) {
  return (
    <div className={`flex items-center gap-3.5 ${className}`}>
      {/* Precision Vector Emblem (Lion Capital / Ashok Stambh) */}
      <svg 
        viewBox="0 0 100 120" 
        className="h-full w-auto text-amber-400 shrink-0 drop-shadow-[0_2px_10px_rgba(245,158,11,0.25)]" 
        fill="currentColor"
      >
        {/* Crown & Lions Upper Silhouette */}
        <path d="M50 8 C46 8, 43 11, 43 15 C43 18, 45 20, 47 21 C45 23, 44 26, 44 29 C44 32, 46 34, 48 35 C46 36, 45 38, 45 41 C45 44, 48 46, 50 46 C52 46, 55 44, 55 41 C55 38, 54 36, 52 35 C54 34, 56 32, 56 29 C56 26, 55 23, 53 21 C55 20, 57 18, 57 15 C57 11, 54 8, 50 8 Z" opacity="0.95" />
        
        {/* Left Lion Head & Mane */}
        <path d="M30 18 C26 18, 23 21, 23 25 C23 28, 25 30, 27 31 C25 33, 24 36, 24 39 C24 43, 27 46, 31 47 C33 47, 36 46, 38 44 C36 41, 35 37, 36 33 C37 29, 39 26, 41 23 C38 20, 34 18, 30 18 Z" opacity="0.85" />
        
        {/* Right Lion Head & Mane */}
        <path d="M70 18 C74 18, 77 21, 77 25 C77 28, 75 30, 73 31 C75 33, 76 36, 76 39 C76 43, 73 46, 69 47 C67 47, 64 46, 62 44 C64 41, 65 37, 64 33 C63 29, 61 26, 59 23 C62 20, 66 18, 70 18 Z" opacity="0.85" />
        
        {/* Central Body & Chest Pillars */}
        <path d="M38 48 C37 54, 38 62, 39 70 C42 71, 46 72, 50 72 C54 72, 58 71, 61 70 C62 62, 63 54, 62 48 C58 50, 54 51, 50 51 C46 51, 42 50, 38 48 Z" />
        <path d="M26 49 C25 56, 27 64, 31 70 C33 69, 35 68, 36 67 C35 61, 34 55, 35 49 C32 49, 29 49, 26 49 Z" opacity="0.8" />
        <path d="M74 49 C75 56, 73 64, 69 70 C67 69, 65 68, 64 67 C65 61, 66 55, 65 49 C68 49, 71 49, 74 49 Z" opacity="0.8" />

        {/* Abacus Platform & Ashoka Chakra (Dharma Wheel) */}
        <rect x="18" y="74" width="64" height="12" rx="2" fill="currentColor" opacity="0.95" />
        
        {/* Ashoka Chakra Wheel */}
        <circle cx="50" cy="80" r="5" fill="#030712" />
        <circle cx="50" cy="80" r="4.2" fill="none" stroke="currentColor" strokeWidth="1" />
        <circle cx="50" cy="80" r="1.2" fill="currentColor" />
        {/* Chakra Spokes */}
        <line x1="50" y1="76" x2="50" y2="84" stroke="currentColor" strokeWidth="0.6" />
        <line x1="46" y1="80" x2="54" y2="80" stroke="currentColor" strokeWidth="0.6" />
        <line x1="47.2" y1="77.2" x2="52.8" y2="82.8" stroke="currentColor" strokeWidth="0.6" />
        <line x1="47.2" y1="82.8" x2="52.8" y2="77.2" stroke="currentColor" strokeWidth="0.6" />

        {/* Galloping Horse & Humped Bull accents on Abacus */}
        <circle cx="30" cy="80" r="2.5" opacity="0.6" />
        <circle cx="70" cy="80" r="2.5" opacity="0.6" />

        {/* Inverted Lotus Base Platform */}
        <path d="M22 88 C32 94, 68 94, 78 88 L80 92 C70 98, 30 98, 20 92 Z" fill="currentColor" opacity="0.9" />

        {/* Satyameva Jayate Banner */}
        <rect x="24" y="99" width="52" height="11" rx="2" fill="#030712" stroke="currentColor" strokeWidth="1" />
        <text 
          x="50" 
          y="107.5" 
          textAnchor="middle" 
          fontSize="7" 
          fontWeight="bold" 
          fill="currentColor" 
          fontFamily="serif"
          letterSpacing="0.8"
        >
          सत्यमेव जयते
        </text>
      </svg>

      {/* Official Government of India Typography */}
      <div className="flex flex-col justify-center">
        <div className="flex items-center gap-1.5">
          <span className="text-xs sm:text-sm font-extrabold tracking-wide text-white font-sans uppercase">
            भारत सरकार
          </span>
          <span className="text-[11px] text-slate-500 font-light">•</span>
          <span className="text-xs sm:text-sm font-semibold tracking-tight text-slate-200">
            Government of India
          </span>
        </div>
        <div className="text-[10px] sm:text-[11px] text-indigo-300 font-medium tracking-tight">
          Ministry of Consumer Affairs, Food & Public Distribution
        </div>
        <div className="text-[9px] sm:text-[10px] font-mono uppercase tracking-wider text-amber-400/90 font-semibold">
          Legal Metrology Division (LMPC)
        </div>
      </div>
    </div>
  );
}
