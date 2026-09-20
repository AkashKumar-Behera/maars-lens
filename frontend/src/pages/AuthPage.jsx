import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  Shield, 
  Lock, 
  Mail, 
  User, 
  Phone, 
  Eye, 
  EyeOff, 
  ArrowRight, 
  AlertCircle, 
  CheckCircle2, 
  Scale, 
  Zap, 
  Building2,
  Check,
  Award,
  Sparkles,
  ChevronRight,
  ShieldCheck,
  FileCheck2,
  BadgeCheck
} from 'lucide-react';

export default function AuthPage({ initialMode = 'login' }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { login, register } = useAuth();

  // false = Sign In, true = Citizen Register
  const [isSignUp, setIsSignUp] = useState(initialMode === 'register' || location.pathname === '/register');

  useEffect(() => {
    setIsSignUp(location.pathname === '/register');
  }, [location.pathname]);

  // Selected Demo Role tracking
  const [selectedDemoRole, setSelectedDemoRole] = useState('admin');

  // Login State (Pre-filled with admin for instant testing)
  const [loginEmail, setLoginEmail] = useState('admin@maars.gov.in');
  const [loginPassword, setLoginPassword] = useState('admin123');
  const [showLoginPassword, setShowLoginPassword] = useState(false);
  const [loginLoading, setLoginLoading] = useState(false);
  const [loginError, setLoginError] = useState(null);

  // Register State
  const [regFullName, setRegFullName] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regPhone, setRegPhone] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [regConfirmPassword, setRegConfirmPassword] = useState('');
  const [showRegPassword, setShowRegPassword] = useState(false);
  const [showRegConfirmPassword, setShowRegConfirmPassword] = useState(false);
  const [regLoading, setRegLoading] = useState(false);
  const [regError, setRegError] = useState(null);

  const toggleMode = (targetSignUp) => {
    setLoginError(null);
    setRegError(null);
    setIsSignUp(targetSignUp);
    if (targetSignUp) {
      navigate('/register', { replace: false });
    } else {
      navigate('/login', { replace: false });
    }
  };

  const demoRoles = [
    { id: 'admin', label: 'Admin', email: 'admin@maars.gov.in', pass: 'admin123', color: 'purple' },
    { id: 'officer', label: 'Officer', email: 'officer@maars.gov.in', pass: 'officer123', color: 'indigo' },
    { id: 'retailer', label: 'Retailer', email: 'retailer@store.in', pass: 'retailer123', color: 'amber' },
    { id: 'citizen', label: 'Citizen', email: 'citizen@maars.gov.in', pass: 'citizen123', color: 'emerald' },
  ];

  const fillDemoCredentials = (roleId, email, pass) => {
    setSelectedDemoRole(roleId);
    setLoginEmail(email);
    setLoginPassword(pass);
    setLoginError(null);
  };

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setLoginError(null);
    setLoginLoading(true);

    try {
      const user = await login(loginEmail, loginPassword);
      navigate(`/${user.role}`);
    } catch (err) {
      setLoginError(err.response?.data?.detail || err.message || 'Authentication failed. Please verify credentials.');
    } finally {
      setLoginLoading(false);
    }
  };

  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    setRegError(null);

    if (!regEmail.includes('@') || !regEmail.includes('.')) {
      setRegError('Please provide a valid email address.');
      return;
    }

    if (regPassword.length < 6) {
      setRegError('Password must be at least 6 characters.');
      return;
    }

    if (regPassword !== regConfirmPassword) {
      setRegError('Passwords do not match.');
      return;
    }

    setRegLoading(true);

    try {
      await register({
        fullName: regFullName.trim(),
        email: regEmail.trim(),
        password: regPassword,
        phone: regPhone.trim() || undefined,
      });
      navigate('/customer');
    } catch (err) {
      const detail = err.response?.data?.detail;
      let msg = 'Registration failed.';
      if (typeof detail === 'string') msg = detail;
      else if (Array.isArray(detail)) msg = detail.map((d) => d.msg || JSON.stringify(d)).join('; ');
      else if (err.message) msg = err.message;
      setRegError(msg);
    } finally {
      setRegLoading(false);
    }
  };

  return (
    <div className="h-screen max-h-screen w-screen overflow-hidden bg-[#070b14] text-slate-100 flex flex-col justify-between font-sans selection:bg-indigo-600 selection:text-white relative">
      
      {/* Background Soft Lighting Gradients */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[450px] bg-indigo-600/10 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute -bottom-20 -right-20 w-[400px] h-[400px] bg-indigo-600/5 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute inset-0 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:28px_28px] opacity-20 pointer-events-none" />

      {/* Top Navigation Bar */}
      <header className="h-14 px-6 sm:px-12 flex items-center justify-between shrink-0 z-20 border-b border-slate-800/40 bg-[#070b14]/70 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-indigo-600/30 ring-1 ring-white/20">
            <Shield className="text-white" size={17} />
          </div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-white text-sm tracking-tight">MAARS Lens</span>
            <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-indigo-950/80 text-indigo-300 border border-indigo-700/40">
              LMPC Portal
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2.5 text-xs text-slate-400">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
          </span>
          <span className="hidden sm:inline font-medium text-slate-300">National Legal Metrology System</span>
        </div>
      </header>

      {/* Main Content: Single Viewport Centered Card */}
      <main className="flex-1 min-h-0 flex items-center justify-center px-4 py-2 z-10">
        <div className="w-full max-w-[920px] h-[540px] bg-[#0c1220] border border-slate-800/90 rounded-2xl shadow-2xl shadow-black/90 flex overflow-hidden backdrop-blur-xl ring-1 ring-white/5">
          
          {/* ================================================================= */}
          {/* LEFT PANEL: Official Authority & Regulatory Platform Overview   */}
          {/* ================================================================= */}
          <div className="hidden md:flex md:w-5/12 p-8 flex-col justify-between bg-gradient-to-br from-[#0f172a] via-[#0c1322] to-[#080d18] border-r border-slate-800/80 relative overflow-hidden">
            
            {/* Subtle inner top glow */}
            <div className="absolute -top-16 -left-16 w-44 h-44 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

            {/* Header: Official Insignia */}
            <div className="relative z-10">
              <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-300 text-[11px] font-semibold tracking-wide uppercase mb-3">
                <Building2 size={13} className="text-amber-400" />
                <span>Government of India</span>
              </div>
              <h1 className="text-xl font-bold text-white tracking-tight leading-snug">
                Ministry of Consumer Affairs
              </h1>
              <p className="text-xs text-indigo-300/90 font-medium mt-1 flex items-center gap-1.5">
                <Scale size={13} className="text-indigo-400" />
                <span>Legal Metrology Division (LMPC)</span>
              </p>
            </div>

            {/* Core Pillars / Mission */}
            <div className="space-y-4 my-auto py-2 relative z-10">
              <p className="text-xs text-slate-400 leading-relaxed">
                Centralized enforcement platform for verifying mandatory packaged commodity declarations under 
                <span className="text-slate-200 font-semibold"> Legal Metrology Rules, 2011</span>.
              </p>

              <div className="space-y-2.5 text-xs text-slate-300">
                <div className="flex items-center gap-3 p-2.5 rounded-xl bg-slate-800/50 border border-slate-750/50">
                  <div className="w-6 h-6 rounded-lg bg-emerald-500/15 text-emerald-400 flex items-center justify-center shrink-0 border border-emerald-500/30">
                    <BadgeCheck size={14} />
                  </div>
                  <span className="font-medium text-[11.5px] text-slate-200">Rule 6 Automated Declaration Verification</span>
                </div>

                <div className="flex items-center gap-3 p-2.5 rounded-xl bg-slate-800/50 border border-slate-750/50">
                  <div className="w-6 h-6 rounded-lg bg-indigo-500/15 text-indigo-400 flex items-center justify-center shrink-0 border border-indigo-500/30">
                    <Scale size={14} />
                  </div>
                  <span className="font-medium text-[11.5px] text-slate-200">Rule 12 Standard Size & Tolerance Auditing</span>
                </div>

                <div className="flex items-center gap-3 p-2.5 rounded-xl bg-slate-800/50 border border-slate-750/50">
                  <div className="w-6 h-6 rounded-lg bg-purple-500/15 text-purple-400 flex items-center justify-center shrink-0 border border-purple-500/30">
                    <ShieldCheck size={14} />
                  </div>
                  <span className="font-medium text-[11.5px] text-slate-200">Tamper-Evident Digital Chain of Custody</span>
                </div>
              </div>
            </div>

            {/* Regulatory Framework Indicator */}
            <div className="pt-3 border-t border-slate-800/70 flex items-center gap-2 text-[11px] text-slate-400 relative z-10">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0" />
              <span>Statutory Legal Metrology Enforcement Framework</span>
            </div>
          </div>

          {/* ================================================================= */}
          {/* RIGHT PANEL: Sleek Segmented Switcher & Crisp Auth Form           */}
          {/* ================================================================= */}
          <div className="w-full md:w-7/12 p-6 sm:p-8 flex flex-col justify-between bg-[#090f1d]/95">
            
            {/* Top Segmented Pill Tab Switcher */}
            <div className="space-y-1">
              <div className="flex bg-[#070b14] p-1 rounded-xl border border-slate-800 shadow-inner">
                <button
                  type="button"
                  onClick={() => toggleMode(false)}
                  className={`flex-1 py-1.5 px-3 rounded-lg text-xs font-semibold transition-all cursor-pointer flex items-center justify-center gap-1.5 ${
                    !isSignUp 
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30' 
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                  }`}
                >
                  <Lock size={12} />
                  <span>Sign In</span>
                </button>
                <button
                  type="button"
                  onClick={() => toggleMode(true)}
                  className={`flex-1 py-1.5 px-3 rounded-lg text-xs font-semibold transition-all cursor-pointer flex items-center justify-center gap-1.5 ${
                    isSignUp 
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30' 
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                  }`}
                >
                  <User size={12} />
                  <span>Citizen Registration</span>
                </button>
              </div>
            </div>

            {/* -------------------- SIGN IN FORM -------------------- */}
            {!isSignUp ? (
              <div className="space-y-4 my-auto py-2">
                
                {/* 1-Click Interactive Demo Role Selector */}
                <div className="bg-[#070c17] border border-slate-800 rounded-xl p-2.5 text-xs space-y-2">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="font-semibold text-slate-300 flex items-center gap-1.5">
                      <Zap size={13} className="text-amber-400" />
                      Quick-Fill Demo Roles:
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono">1-click test</span>
                  </div>

                  <div className="grid grid-cols-4 gap-1.5">
                    {demoRoles.map((role) => {
                      const isActive = selectedDemoRole === role.id && loginEmail === role.email;
                      const roleColors = {
                        purple: isActive 
                          ? 'bg-purple-600 text-white border-purple-400 shadow-sm shadow-purple-600/40 ring-1 ring-purple-400' 
                          : 'bg-slate-900/90 text-purple-300 border-purple-500/25 hover:border-purple-500/60 hover:bg-slate-800',
                        indigo: isActive 
                          ? 'bg-indigo-600 text-white border-indigo-400 shadow-sm shadow-indigo-600/40 ring-1 ring-indigo-400' 
                          : 'bg-slate-900/90 text-indigo-300 border-indigo-500/25 hover:border-indigo-500/60 hover:bg-slate-800',
                        amber: isActive 
                          ? 'bg-amber-600 text-white border-amber-400 shadow-sm shadow-amber-600/40 ring-1 ring-amber-400' 
                          : 'bg-slate-900/90 text-amber-300 border-amber-500/25 hover:border-amber-500/60 hover:bg-slate-800',
                        emerald: isActive 
                          ? 'bg-emerald-600 text-white border-emerald-400 shadow-sm shadow-emerald-600/40 ring-1 ring-emerald-400' 
                          : 'bg-slate-900/90 text-emerald-300 border-emerald-500/25 hover:border-emerald-500/60 hover:bg-slate-800',
                      };

                      return (
                        <button
                          key={role.id}
                          type="button"
                          onClick={() => fillDemoCredentials(role.id, role.email, role.pass)}
                          className={`py-1 px-1.5 rounded-lg border text-[11px] font-semibold transition cursor-pointer text-center truncate ${roleColors[role.color]}`}
                        >
                          {role.label}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Error Banner */}
                {loginError && (
                  <div className="p-2.5 rounded-xl bg-rose-950/70 border border-rose-800 text-rose-300 text-xs flex items-center gap-2">
                    <AlertCircle size={14} className="shrink-0 text-rose-400" />
                    <span>{loginError}</span>
                  </div>
                )}

                {/* Form Fields */}
                <form onSubmit={handleLoginSubmit} className="space-y-3.5" autoComplete="off">
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider mb-1">
                      Email Address
                    </label>
                    <div className="relative rounded-xl shadow-sm">
                      <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                        <Mail size={15} />
                      </div>
                      <input
                        type="email"
                        value={loginEmail}
                        onChange={(e) => {
                          setLoginEmail(e.target.value);
                          setSelectedDemoRole(null);
                        }}
                        placeholder="name@maars.gov.in"
                        className="block w-full pl-10 pr-3.5 py-2.5 bg-[#0c1424] border border-slate-700/80 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 text-xs sm:text-sm transition"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider mb-1">
                      Password
                    </label>
                    <div className="relative rounded-xl shadow-sm">
                      <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                        <Lock size={15} />
                      </div>
                      <input
                        type={showLoginPassword ? 'text' : 'password'}
                        value={loginPassword}
                        onChange={(e) => {
                          setLoginPassword(e.target.value);
                          setSelectedDemoRole(null);
                        }}
                        placeholder="••••••••"
                        className="block w-full pl-10 pr-10 py-2.5 bg-[#0c1424] border border-slate-700/80 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 text-xs sm:text-sm transition"
                        required
                      />
                      <button
                        type="button"
                        onClick={() => setShowLoginPassword(!showLoginPassword)}
                        className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-white cursor-pointer"
                      >
                        {showLoginPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                      </button>
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={loginLoading}
                    className="w-full flex justify-center items-center py-2.5 px-4 rounded-xl text-xs sm:text-sm font-semibold text-white bg-gradient-to-r from-indigo-600 via-indigo-500 to-blue-600 hover:from-indigo-500 hover:to-blue-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/40 shadow-lg shadow-indigo-600/30 transition-all disabled:opacity-50 cursor-pointer active:scale-[0.99]"
                  >
                    {loginLoading ? (
                      <span className="inline-flex items-center gap-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                        Authenticating...
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-2">
                        Sign In to Portal
                        <ArrowRight size={15} />
                      </span>
                    )}
                  </button>
                </form>
              </div>
            ) : (
              /* -------------------- REGISTRATION FORM -------------------- */
              <div className="space-y-3 my-auto py-1">
                {regError && (
                  <div className="p-2.5 rounded-xl bg-rose-950/70 border border-rose-800 text-rose-300 text-xs flex items-center gap-2">
                    <AlertCircle size={14} className="shrink-0 text-rose-400" />
                    <span>{regError}</span>
                  </div>
                )}

                <form onSubmit={handleRegisterSubmit} className="space-y-2.5" autoComplete="off">
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider mb-1">
                      Full Legal Name <span className="text-rose-400">*</span>
                    </label>
                    <div className="relative rounded-xl shadow-sm">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                        <User size={14} />
                      </div>
                      <input
                        type="text"
                        value={regFullName}
                        onChange={(e) => setRegFullName(e.target.value)}
                        placeholder="e.g. Ramesh Kumar"
                        className="block w-full pl-9 pr-3 py-2 bg-[#0c1424] border border-slate-700/80 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 text-xs"
                        required
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider mb-1">
                        Email Address <span className="text-rose-400">*</span>
                      </label>
                      <input
                        type="email"
                        value={regEmail}
                        onChange={(e) => setRegEmail(e.target.value)}
                        placeholder="name@example.com"
                        className="block w-full px-3 py-2 bg-[#0c1424] border border-slate-700/80 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 text-xs"
                        required
                      />
                    </div>

                    <div>
                      <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider mb-1">
                        Phone (Optional)
                      </label>
                      <input
                        type="tel"
                        value={regPhone}
                        onChange={(e) => setRegPhone(e.target.value)}
                        placeholder="+91 9876543210"
                        className="block w-full px-3 py-2 bg-[#0c1424] border border-slate-700/80 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 text-xs"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider mb-1">
                        Password <span className="text-rose-400">*</span>
                      </label>
                      <div className="relative rounded-xl shadow-sm">
                        <input
                          type={showRegPassword ? 'text' : 'password'}
                          value={regPassword}
                          onChange={(e) => setRegPassword(e.target.value)}
                          placeholder="Min. 6 chars"
                          className="block w-full pl-3 pr-8 py-2 bg-[#0c1424] border border-slate-700/80 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 text-xs"
                          required
                        />
                        <button
                          type="button"
                          onClick={() => setShowRegPassword(!showRegPassword)}
                          className="absolute inset-y-0 right-0 pr-2 flex items-center text-slate-400 hover:text-white"
                        >
                          {showRegPassword ? <EyeOff size={13} /> : <Eye size={13} />}
                        </button>
                      </div>
                    </div>

                    <div>
                      <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider mb-1">
                        Confirm <span className="text-rose-400">*</span>
                      </label>
                      <div className="relative rounded-xl shadow-sm">
                        <input
                          type={showRegConfirmPassword ? 'text' : 'password'}
                          value={regConfirmPassword}
                          onChange={(e) => setRegConfirmPassword(e.target.value)}
                          placeholder="Re-enter"
                          className="block w-full pl-3 pr-8 py-2 bg-[#0c1424] border border-slate-700/80 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 text-xs"
                          required
                        />
                        <button
                          type="button"
                          onClick={() => setShowRegConfirmPassword(!showRegConfirmPassword)}
                          className="absolute inset-y-0 right-0 pr-2 flex items-center text-slate-400 hover:text-white"
                        >
                          {showRegConfirmPassword ? <EyeOff size={13} /> : <Eye size={13} />}
                        </button>
                      </div>
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={regLoading}
                    className="w-full flex justify-center items-center py-2.5 px-4 rounded-xl text-xs sm:text-sm font-semibold text-white bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 shadow-md transition disabled:opacity-50 cursor-pointer mt-1"
                  >
                    {regLoading ? (
                      <span className="inline-flex items-center gap-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                        Creating Account...
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-2">
                        Complete Registration
                        <ArrowRight size={15} />
                      </span>
                    )}
                  </button>
                </form>
              </div>
            )}

            {/* Micro Security Badge */}
            <div className="text-center text-[10.5px] text-slate-500 border-t border-slate-800/80 pt-2 flex items-center justify-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              <span>Authorized Legal Metrology Node • Cryptographically Protected</span>
            </div>
          </div>
        </div>
      </main>

      {/* Bottom Legal Footer */}
      <footer className="h-10 px-6 sm:px-12 flex items-center justify-between text-[11px] text-slate-500 border-t border-slate-800/50 bg-[#070b14]/70 backdrop-blur-md shrink-0 z-20">
        <div>Government of India • Ministry of Consumer Affairs, Food & Public Distribution</div>
        <div className="hidden sm:block">Legal Metrology Act, 2009 & Packaged Commodities Rules, 2011</div>
      </footer>
    </div>
  );
}
