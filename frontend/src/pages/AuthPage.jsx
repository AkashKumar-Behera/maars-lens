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
  BadgeCheck,
  Store,
  Upload,
  FileText,
  Image as ImageIcon,
  X,
  Briefcase,
  MapPin,
  KeyRound,
  Users
} from 'lucide-react';

export default function AuthPage({ initialMode = 'login' }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { login, register } = useAuth();

  // false = Sign In, true = Register
  const [isSignUp, setIsSignUp] = useState(initialMode === 'register' || location.pathname === '/register');

  useEffect(() => {
    setIsSignUp(location.pathname === '/register');
  }, [location.pathname]);

  // Selected Demo Role tracking
  const [selectedDemoRole, setSelectedDemoRole] = useState('admin');

  // Login State
  const [loginEmail, setLoginEmail] = useState('admin@maars.gov.in');
  const [loginPassword, setLoginPassword] = useState('admin123');
  const [showLoginPassword, setShowLoginPassword] = useState(false);
  const [loginLoading, setLoginLoading] = useState(false);
  const [loginError, setLoginError] = useState(null);

  // Register State
  const [regRole, setRegRole] = useState('citizen'); // 'citizen', 'retailer', 'officer', 'admin'
  const [regFullName, setRegFullName] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regPhone, setRegPhone] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [regConfirmPassword, setRegConfirmPassword] = useState('');
  const [showRegPassword, setShowRegPassword] = useState(false);
  const [showRegConfirmPassword, setShowRegConfirmPassword] = useState(false);

  // Retailer Specific State
  const [regRetailerId, setRegRetailerId] = useState('');
  const [regBusinessName, setRegBusinessName] = useState('');
  const [regRegistrationNo, setRegRegistrationNo] = useState('');
  const [regBusinessType, setRegBusinessType] = useState('Grocery & Supermarket');
  const [regAddress, setRegAddress] = useState('');
  const [regDistrict, setRegDistrict] = useState('');
  const [regState, setRegState] = useState('');

  // Officer Specific State
  const [regOfficerId, setRegOfficerId] = useState('');
  const [regEmployeeId, setRegEmployeeId] = useState('');
  const [regDesignation, setRegDesignation] = useState('Legal Metrology Inspector (LMI)');
  const [regJurisdiction, setRegJurisdiction] = useState('');

  // Admin Specific State
  const [regAdminId, setRegAdminId] = useState('');
  const [regDepartment, setRegDepartment] = useState('Legal Metrology Central Cell');
  const [regAdminKey, setRegAdminKey] = useState('');

  // Proof Upload State (Image or PDF)
  const [regProofName, setRegProofName] = useState('');
  const [regProofData, setRegProofData] = useState('');
  const [regProofType, setRegProofType] = useState('');
  const [regProofSize, setRegProofSize] = useState(0);

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

  const handleProofFileChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Max 10MB
    if (file.size > 10 * 1024 * 1024) {
      setRegError('Proof file size must be less than 10MB.');
      return;
    }

    const isPdf = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');
    const isImg = file.type.startsWith('image/');

    if (!isPdf && !isImg) {
      setRegError('Please upload a valid image (PNG, JPG, WEBP) or PDF file.');
      return;
    }

    setRegProofName(file.name);
    setRegProofType(isPdf ? 'pdf' : 'image');
    setRegProofSize((file.size / (1024 * 1024)).toFixed(2));

    const reader = new FileReader();
    reader.onload = () => {
      setRegProofData(reader.result);
      setRegError(null);
    };
    reader.onerror = () => {
      setRegError('Failed to read the uploaded proof document.');
    };
    reader.readAsDataURL(file);
  };

  const handleRemoveProof = () => {
    setRegProofName('');
    setRegProofData('');
    setRegProofType('');
    setRegProofSize(0);
  };

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setLoginError(null);
    setLoginLoading(true);

    try {
      const user = await login(loginEmail, loginPassword);
      const targetRole = user.role === 'customer' ? 'customer' : user.role;
      navigate(`/${targetRole}`);
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

    // Role-specific field validations
    if (regRole === 'retailer') {
      if (!regBusinessName.trim()) {
        setRegError('Business Name is required for Retailer registration.');
        return;
      }
      if (!regAddress.trim() || !regDistrict.trim() || !regState.trim()) {
        setRegError('Complete Address, District, and State are required for Retailer registration.');
        return;
      }
    }

    if (regRole === 'officer') {
      if (!regOfficerId.trim() && !regEmployeeId.trim()) {
        setRegError('Officer ID or Employee ID is required for Officer registration.');
        return;
      }
      if (!regJurisdiction.trim()) {
        setRegError('Jurisdiction area is required for Officer registration.');
        return;
      }
    }

    setRegLoading(true);

    try {
      const payload = {
        fullName: regFullName.trim(),
        email: regEmail.trim(),
        password: regPassword,
        phone: regPhone.trim() || undefined,
        role: regRole,

        // Retailer
        retailer_id: regRetailerId.trim() || undefined,
        business_name: regBusinessName.trim() || undefined,
        registration_no: regRegistrationNo.trim() || undefined,
        business_type: regBusinessType || undefined,
        address: regAddress.trim() || undefined,
        district: regDistrict.trim() || undefined,
        state: regState.trim() || undefined,

        // Officer
        officer_id: regOfficerId.trim() || undefined,
        employee_id: regEmployeeId.trim() || undefined,
        designation: regDesignation || undefined,
        jurisdiction: regJurisdiction.trim() || undefined,

        // Admin
        admin_id: regAdminId.trim() || undefined,
        department: regDepartment.trim() || undefined,
        admin_secret_key: regAdminKey.trim() || undefined,

        // Proof
        proof_filename: regProofName || undefined,
        proof_data: regProofData || undefined,
      };

      const user = await register(payload);
      const targetRole = user.role === 'customer' || user.role === 'citizen' ? 'customer' : user.role;
      navigate(`/${targetRole}`);
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

      {/* Main Content: Dynamic Adaptive Card */}
      <main className="flex-1 min-h-0 flex items-center justify-center px-4 py-2 sm:py-4 z-10 overflow-y-auto">
        <div className={`w-full ${isSignUp ? 'max-w-[1000px] h-[92vh] max-h-[780px]' : 'max-w-[920px] h-[540px]'} bg-[#0c1220] border border-slate-800/90 rounded-2xl shadow-2xl shadow-black/90 flex overflow-hidden backdrop-blur-xl ring-1 ring-white/5 transition-all duration-300 my-auto`}>
          
          {/* ================================================================= */}
          {/* LEFT PANEL: Official Authority & Regulatory Platform Overview   */}
          {/* ================================================================= */}
          <div className="hidden md:flex md:w-5/12 p-7 flex-col justify-between bg-gradient-to-br from-[#0f172a] via-[#0c1322] to-[#080d18] border-r border-slate-800/80 relative overflow-hidden">
            
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
            <div className="space-y-3.5 my-auto py-2 relative z-10">
              <p className="text-xs text-slate-400 leading-relaxed">
                Centralized enforcement platform for verifying mandatory packaged commodity declarations under 
                <span className="text-slate-200 font-semibold"> Legal Metrology Rules, 2011</span>.
              </p>

              <div className="space-y-2 text-xs text-slate-300">
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
              <span>Statutory Legal Metrology Enforcement Node</span>
            </div>
          </div>

          {/* ================================================================= */}
          {/* RIGHT PANEL: Sleek Segmented Switcher & Crisp Auth Form           */}
          {/* ================================================================= */}
          <div className="w-full md:w-7/12 p-5 sm:p-7 flex flex-col justify-between bg-[#090f1d]/95 overflow-hidden">
            
            {/* Top Segmented Tab Switcher */}
            <div className="space-y-1 shrink-0 pb-1">
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
                  <Users size={12} />
                  <span>Create Account</span>
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
              /* -------------------- DYNAMIC ROLE REGISTRATION FORM -------------------- */
              <div className="overflow-y-auto pr-1 flex-1 min-h-0 space-y-3 py-1.5">
                {regError && (
                  <div className="p-2.5 rounded-xl bg-rose-950/70 border border-rose-800 text-rose-300 text-xs flex items-center gap-2">
                    <AlertCircle size={14} className="shrink-0 text-rose-400" />
                    <span>{regError}</span>
                  </div>
                )}

                {/* Role Selection Tabs */}
                <div>
                  <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                    Select Account Role <span className="text-rose-400">*</span>
                  </label>
                  <div className="grid grid-cols-4 gap-1.5 p-1 bg-[#060a14] border border-slate-800 rounded-xl">
                    {[
                      { id: 'citizen', label: 'Citizen', icon: User, color: 'text-emerald-400', active: 'bg-emerald-950/70 border-emerald-600/70 text-white' },
                      { id: 'retailer', label: 'Retailer', icon: Store, color: 'text-amber-400', active: 'bg-amber-950/70 border-amber-600/70 text-white' },
                      { id: 'officer', label: 'Officer', icon: ShieldCheck, color: 'text-indigo-400', active: 'bg-indigo-950/70 border-indigo-600/70 text-white' },
                      { id: 'admin', label: 'Admin', icon: Lock, color: 'text-purple-400', active: 'bg-purple-950/70 border-purple-600/70 text-white' },
                    ].map((r) => {
                      const Icon = r.icon;
                      const isSelected = regRole === r.id;
                      return (
                        <button
                          key={r.id}
                          type="button"
                          onClick={() => {
                            setRegRole(r.id);
                            setRegError(null);
                          }}
                          className={`flex flex-col items-center justify-center py-2 px-1 rounded-lg text-xs font-semibold transition border cursor-pointer ${
                            isSelected
                              ? `${r.active} shadow-sm ring-1 ring-white/10`
                              : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                          }`}
                        >
                          <Icon size={16} className={`mb-1 ${isSelected ? r.color : 'text-slate-500'}`} />
                          <span>{r.label}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>

                <form onSubmit={handleRegisterSubmit} className="space-y-2.5" autoComplete="off">
                  {/* Base Field: Full Legal Name */}
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

                  {/* Base Fields: Email & Phone */}
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
                        Phone Number <span className="text-slate-500 font-normal">(Optional)</span>
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

                  {/* Base Fields: Password & Confirm Password */}
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
                        Confirm Password <span className="text-rose-400">*</span>
                      </label>
                      <div className="relative rounded-xl shadow-sm">
                        <input
                          type={showRegConfirmPassword ? 'text' : 'password'}
                          value={regConfirmPassword}
                          onChange={(e) => setRegConfirmPassword(e.target.value)}
                          placeholder="Re-enter password"
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

                  {/* ----------------- IF CITIZEN: Normal Notice ----------------- */}
                  {regRole === 'citizen' && (
                    <div className="p-2.5 rounded-xl bg-emerald-950/25 border border-emerald-800/35 text-[11px] text-emerald-300 flex items-center gap-2">
                      <CheckCircle2 size={15} className="shrink-0 text-emerald-400" />
                      <span>Citizen profile: Free access to live label scanning, Rule 6 validation, and public grievance logging.</span>
                    </div>
                  )}

                  {/* ----------------- IF RETAILER: Specific Fields ----------------- */}
                  {regRole === 'retailer' && (
                    <div className="space-y-2.5 p-3 rounded-xl bg-amber-950/20 border border-amber-800/30">
                      <div className="flex items-center gap-1.5 text-xs font-semibold text-amber-300">
                        <Store size={14} className="text-amber-400" />
                        <span>Retailer Business Details</span>
                      </div>

                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="block text-[10px] font-semibold text-slate-300 uppercase tracking-wider mb-1">
                            Retailer ID <span className="text-slate-500 font-normal">(Optional)</span>
                          </label>
                          <input
                            type="text"
                            value={regRetailerId}
                            onChange={(e) => setRegRetailerId(e.target.value)}
                            placeholder="e.g. RET-78210"
                            className="block w-full px-2.5 py-1.5 bg-[#0c1424] border border-slate-700/80 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-amber-500 text-xs"
                          />
                        </div>

                        <div>
                          <label className="block text-[10px] font-semibold text-slate-300 uppercase tracking-wider mb-1">
                            Business Name <span className="text-rose-400">*</span>
                          </label>
                          <input
                            type="text"
                            value={regBusinessName}
                            onChange={(e) => setRegBusinessName(e.target.value)}
                            placeholder="Store / Company Name"
                            className="block w-full px-2.5 py-1.5 bg-[#0c1424] border border-slate-700/80 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-amber-500 text-xs"
                            required
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="block text-[10px] font-semibold text-slate-300 uppercase tracking-wider mb-1">
                            Registration No <span className="text-slate-500 font-normal">(GST/Trade)</span>
                          </label>
                          <input
                            type="text"
                            value={regRegistrationNo}
                            onChange={(e) => setRegRegistrationNo(e.target.value)}
                            placeholder="GSTIN / License No"
                            className="block w-full px-2.5 py-1.5 bg-[#0c1424] border border-slate-700/80 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-amber-500 text-xs"
                          />
                        </div>

                        <div>
                          <label className="block text-[10px] font-semibold text-slate-300 uppercase tracking-wider mb-1">
                            Business Type
                          </label>
                          <select
                            value={regBusinessType}
                            onChange={(e) => setRegBusinessType(e.target.value)}
                            className="block w-full px-2 py-1.5 bg-[#0c1424] border border-slate-700/80 rounded-lg text-white focus:outline-none focus:border-amber-500 text-xs"
                          >
                            <option value="Grocery & Supermarket">Grocery & Supermarket</option>
                            <option value="Pharmacy & Chemist">Pharmacy & Chemist</option>
                            <option value="General Merchant Store">General Merchant Store</option>
                            <option value="FMCG Wholesaler">FMCG Wholesaler</option>
                            <option value="Electronics & Consumer Goods">Electronics & Consumer Goods</option>
                            <option value="Departmental Store">Departmental Store</option>
                            <option value="Other Commercial Enterprise">Other Commercial Enterprise</option>
                          </select>
                        </div>
                      </div>

                      <div>
                        <label className="block text-[10px] font-semibold text-slate-300 uppercase tracking-wider mb-1">
                          Address <span className="text-rose-400">*</span>
                        </label>
                        <input
                          type="text"
                          value={regAddress}
                          onChange={(e) => setRegAddress(e.target.value)}
                          placeholder="Premises / Shop Address"
                          className="block w-full px-2.5 py-1.5 bg-[#0c1424] border border-slate-700/80 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-amber-500 text-xs"
                          required
                        />
                      </div>

                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="block text-[10px] font-semibold text-slate-300 uppercase tracking-wider mb-1">
                            District <span className="text-rose-400">*</span>
                          </label>
                          <input
                            type="text"
                            value={regDistrict}
                            onChange={(e) => setRegDistrict(e.target.value)}
                            placeholder="e.g. Central Delhi"
                            className="block w-full px-2.5 py-1.5 bg-[#0c1424] border border-slate-700/80 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-amber-500 text-xs"
                            required
                          />
                        </div>

                        <div>
                          <label className="block text-[10px] font-semibold text-slate-300 uppercase tracking-wider mb-1">
                            State <span className="text-rose-400">*</span>
                          </label>
                          <input
                            type="text"
                            value={regState}
                            onChange={(e) => setRegState(e.target.value)}
                            placeholder="e.g. Delhi / Maharashtra"
                            className="block w-full px-2.5 py-1.5 bg-[#0c1424] border border-slate-700/80 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-amber-500 text-xs"
                            required
                          />
                        </div>
                      </div>

                      {/* Retailer Proof Upload */}
                      <div>
                        <label className="block text-[10px] font-semibold text-slate-300 uppercase tracking-wider mb-1">
                          Business Proof <span className="text-slate-400 font-normal">(GST Certificate / Trade License in IMG or PDF)</span>
                        </label>
                        {regProofName ? (
                          <div className="flex items-center justify-between p-2 rounded-lg bg-amber-950/40 border border-amber-700/50 text-xs text-amber-200">
                            <div className="flex items-center gap-2 truncate">
                              {regProofType === 'pdf' ? <FileText size={16} className="text-rose-400 shrink-0" /> : <ImageIcon size={16} className="text-amber-400 shrink-0" />}
                              <span className="truncate">{regProofName}</span>
                              <span className="text-[10px] text-amber-400/80">({regProofSize} MB)</span>
                            </div>
                            <button type="button" onClick={handleRemoveProof} className="text-slate-400 hover:text-rose-400 ml-2">
                              <X size={14} />
                            </button>
                          </div>
                        ) : (
                          <label className="flex items-center justify-center gap-2 px-3 py-2 border border-dashed border-slate-700 hover:border-amber-500/80 rounded-lg bg-[#0a101d] text-slate-400 hover:text-amber-300 text-xs cursor-pointer transition">
                            <Upload size={14} />
                            <span>Upload Proof Document (Image or PDF)</span>
                            <input type="file" accept="image/*,.pdf" onChange={handleProofFileChange} className="hidden" />
                          </label>
                        )}
                      </div>
                    </div>
                  )}

                  {/* ----------------- IF OFFICER: Specific Fields ----------------- */}
                  {regRole === 'officer' && (
                    <div className="space-y-2.5 p-3 rounded-xl bg-indigo-950/20 border border-indigo-800/30">
                      <div className="flex items-center gap-1.5 text-xs font-semibold text-indigo-300">
                        <ShieldCheck size={14} className="text-indigo-400" />
                        <span>Officer Departmental Credentials</span>
                      </div>

                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="block text-[10px] font-semibold text-slate-300 uppercase tracking-wider mb-1">
                            Officer ID <span className="text-rose-400">*</span>
                          </label>
                          <input
                            type="text"
                            value={regOfficerId}
                            onChange={(e) => setRegOfficerId(e.target.value)}
                            placeholder="e.g. OFF-DL-402"
                            className="block w-full px-2.5 py-1.5 bg-[#0c1424] border border-slate-700/80 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 text-xs"
                            required
                          />
                        </div>

                        <div>
                          <label className="block text-[10px] font-semibold text-slate-300 uppercase tracking-wider mb-1">
                            Employee ID <span className="text-rose-400">*</span>
                          </label>
                          <input
                            type="text"
                            value={regEmployeeId}
                            onChange={(e) => setRegEmployeeId(e.target.value)}
                            placeholder="e.g. EMP-982031"
                            className="block w-full px-2.5 py-1.5 bg-[#0c1424] border border-slate-700/80 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 text-xs"
                            required
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="block text-[10px] font-semibold text-slate-300 uppercase tracking-wider mb-1">
                            Designation <span className="text-rose-400">*</span>
                          </label>
                          <select
                            value={regDesignation}
                            onChange={(e) => setRegDesignation(e.target.value)}
                            className="block w-full px-2 py-1.5 bg-[#0c1424] border border-slate-700/80 rounded-lg text-white focus:outline-none focus:border-indigo-500 text-xs"
                          >
                            <option value="Legal Metrology Inspector (LMI)">Legal Metrology Inspector (LMI)</option>
                            <option value="Senior Inspector">Senior Inspector</option>
                            <option value="Assistant Controller">Assistant Controller</option>
                            <option value="Deputy Controller">Deputy Controller</option>
                            <option value="Field Enforcement Officer">Field Enforcement Officer</option>
                            <option value="Public Metrology Analyst">Public Metrology Analyst</option>
                          </select>
                        </div>

                        <div>
                          <label className="block text-[10px] font-semibold text-slate-300 uppercase tracking-wider mb-1">
                            Jurisdiction <span className="text-rose-400">*</span>
                          </label>
                          <input
                            type="text"
                            value={regJurisdiction}
                            onChange={(e) => setRegJurisdiction(e.target.value)}
                            placeholder="e.g. North Zone / District Circle"
                            className="block w-full px-2.5 py-1.5 bg-[#0c1424] border border-slate-700/80 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 text-xs"
                            required
                          />
                        </div>
                      </div>

                      {/* Officer ID Proof Upload */}
                      <div>
                        <label className="block text-[10px] font-semibold text-slate-300 uppercase tracking-wider mb-1">
                          ID Proof <span className="text-slate-400 font-normal">(Govt ID Card / Appointment Letter in IMG or PDF)</span>
                        </label>
                        {regProofName ? (
                          <div className="flex items-center justify-between p-2 rounded-lg bg-indigo-950/40 border border-indigo-700/50 text-xs text-indigo-200">
                            <div className="flex items-center gap-2 truncate">
                              {regProofType === 'pdf' ? <FileText size={16} className="text-rose-400 shrink-0" /> : <ImageIcon size={16} className="text-indigo-400 shrink-0" />}
                              <span className="truncate">{regProofName}</span>
                              <span className="text-[10px] text-indigo-400/80">({regProofSize} MB)</span>
                            </div>
                            <button type="button" onClick={handleRemoveProof} className="text-slate-400 hover:text-rose-400 ml-2">
                              <X size={14} />
                            </button>
                          </div>
                        ) : (
                          <label className="flex items-center justify-center gap-2 px-3 py-2 border border-dashed border-slate-700 hover:border-indigo-500/80 rounded-lg bg-[#0a101d] text-slate-400 hover:text-indigo-300 text-xs cursor-pointer transition">
                            <Upload size={14} />
                            <span>Upload Official ID Proof (Image or PDF)</span>
                            <input type="file" accept="image/*,.pdf" onChange={handleProofFileChange} className="hidden" />
                          </label>
                        )}
                      </div>
                    </div>
                  )}

                  {/* ----------------- IF ADMIN: Specific Fields ----------------- */}
                  {regRole === 'admin' && (
                    <div className="space-y-2.5 p-3 rounded-xl bg-purple-950/20 border border-purple-800/30">
                      <div className="flex items-center gap-1.5 text-xs font-semibold text-purple-300">
                        <Lock size={14} className="text-purple-400" />
                        <span>Administrative Authorization</span>
                      </div>

                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="block text-[10px] font-semibold text-slate-300 uppercase tracking-wider mb-1">
                            Admin ID <span className="text-slate-500 font-normal">(Optional)</span>
                          </label>
                          <input
                            type="text"
                            value={regAdminId}
                            onChange={(e) => setRegAdminId(e.target.value)}
                            placeholder="e.g. ADM-007"
                            className="block w-full px-2.5 py-1.5 bg-[#0c1424] border border-slate-700/80 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-purple-500 text-xs"
                          />
                        </div>

                        <div>
                          <label className="block text-[10px] font-semibold text-slate-300 uppercase tracking-wider mb-1">
                            Department
                          </label>
                          <input
                            type="text"
                            value={regDepartment}
                            onChange={(e) => setRegDepartment(e.target.value)}
                            placeholder="Ministry / Legal Cell"
                            className="block w-full px-2.5 py-1.5 bg-[#0c1424] border border-slate-700/80 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-purple-500 text-xs"
                          />
                        </div>
                      </div>

                      <div>
                        <label className="block text-[10px] font-semibold text-slate-300 uppercase tracking-wider mb-1">
                          Admin Security Key <span className="text-slate-500 font-normal">(e.g. ADMIN123 or MAARS@2026)</span>
                        </label>
                        <input
                          type="password"
                          value={regAdminKey}
                          onChange={(e) => setRegAdminKey(e.target.value)}
                          placeholder="Enter Master Security Key"
                          className="block w-full px-2.5 py-1.5 bg-[#0c1424] border border-slate-700/80 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-purple-500 text-xs"
                        />
                      </div>

                      {/* Admin Proof Upload */}
                      <div>
                        <label className="block text-[10px] font-semibold text-slate-300 uppercase tracking-wider mb-1">
                          Authorization Proof <span className="text-slate-400 font-normal">(Optional IMG or PDF)</span>
                        </label>
                        {regProofName ? (
                          <div className="flex items-center justify-between p-2 rounded-lg bg-purple-950/40 border border-purple-700/50 text-xs text-purple-200">
                            <div className="flex items-center gap-2 truncate">
                              {regProofType === 'pdf' ? <FileText size={16} className="text-rose-400 shrink-0" /> : <ImageIcon size={16} className="text-purple-400 shrink-0" />}
                              <span className="truncate">{regProofName}</span>
                              <span className="text-[10px] text-purple-400/80">({regProofSize} MB)</span>
                            </div>
                            <button type="button" onClick={handleRemoveProof} className="text-slate-400 hover:text-rose-400 ml-2">
                              <X size={14} />
                            </button>
                          </div>
                        ) : (
                          <label className="flex items-center justify-center gap-2 px-3 py-2 border border-dashed border-slate-700 hover:border-purple-500/80 rounded-lg bg-[#0a101d] text-slate-400 hover:text-purple-300 text-xs cursor-pointer transition">
                            <Upload size={14} />
                            <span>Upload Authorization Proof (Image or PDF)</span>
                            <input type="file" accept="image/*,.pdf" onChange={handleProofFileChange} className="hidden" />
                          </label>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Submit Registration Button */}
                  <button
                    type="submit"
                    disabled={regLoading}
                    className="w-full flex justify-center items-center py-2.5 px-4 rounded-xl text-xs sm:text-sm font-semibold text-white bg-gradient-to-r from-indigo-600 via-indigo-500 to-blue-600 hover:from-indigo-500 hover:to-blue-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 shadow-md transition disabled:opacity-50 cursor-pointer mt-2"
                  >
                    {regLoading ? (
                      <span className="inline-flex items-center gap-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                        Provisioning Account...
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-2 capitalize">
                        Register as {regRole}
                        <ArrowRight size={15} />
                      </span>
                    )}
                  </button>
                </form>
              </div>
            )}

            {/* Micro Security Badge */}
            <div className="text-center text-[10.5px] text-slate-500 border-t border-slate-800/80 pt-2 flex items-center justify-center gap-2 shrink-0">
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
