import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Sparkles, Eye, EyeOff, ArrowRight, AlertCircle, ShieldCheck, CheckCircle2, Lock } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password) {
      setError('Please enter both your work email and password.');
      return;
    }
    setError(null);
    setLoading(true);
    try {
      await login(email.trim(), password);
      navigate('/assistant');
    } catch (err: any) {
      setError(err.message || 'Invalid email or password.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between p-4 sm:p-6 md:p-8 relative overflow-hidden font-sans">
      {/* Background ambient lighting */}
      <div className="absolute -top-40 -left-40 w-96 h-96 bg-blue-600/15 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-40 -right-40 w-96 h-96 bg-indigo-600/15 rounded-full blur-3xl pointer-events-none" />

      {/* Main Container */}
      <div className="flex-1 flex items-center justify-center w-full max-w-6xl mx-auto py-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 w-full items-center">
          
          {/* Left Column: Brand & Capability Overview (Desktop/Tablet) */}
          <div className="hidden lg:flex lg:col-span-6 flex-col justify-center space-y-8 pr-4">
            <div className="space-y-4">
              <div className="inline-flex items-center gap-2.5 px-3 py-1.5 rounded-full bg-blue-900/40 border border-blue-700/40 text-blue-300 text-xs font-medium backdrop-blur-xs">
                <Sparkles className="w-3.5 h-3.5 text-blue-400" />
                <span>Enterprise Knowledge Platform</span>
              </div>
              
              <h1 className="text-3xl xl:text-4xl font-bold tracking-tight text-white leading-tight">
                Secure, grounded knowledge for every authorized employee.
              </h1>
              
              <p className="text-sm text-slate-400 leading-relaxed max-w-md">
                Access verified organizational policies, company guidelines, and authorized private intelligence with high confidence and citations.
              </p>
            </div>

            {/* 3 Capabilities */}
            <div className="space-y-4 pt-2">
              <div className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-blue-500/15 border border-blue-500/30 flex items-center justify-center text-blue-400 shrink-0 mt-0.5">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                </div>
                <div>
                  <h4 className="text-xs font-semibold text-slate-200">Secure enterprise knowledge access</h4>
                  <p className="text-[11px] text-slate-400 mt-0.5">Automated permission checks protect confidential information.</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-blue-500/15 border border-blue-500/30 flex items-center justify-center text-blue-400 shrink-0 mt-0.5">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                </div>
                <div>
                  <h4 className="text-xs font-semibold text-slate-200">Role-aware information retrieval</h4>
                  <p className="text-[11px] text-slate-400 mt-0.5">Accurate answers tailored strictly to your authorized department.</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-blue-500/15 border border-blue-500/30 flex items-center justify-center text-blue-400 shrink-0 mt-0.5">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                </div>
                <div>
                  <h4 className="text-xs font-semibold text-slate-200">Grounded answers with source citations</h4>
                  <p className="text-[11px] text-slate-400 mt-0.5">Every response is verified against authoritative internal documents.</p>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Authentication Card */}
          <div className="col-span-1 lg:col-span-6 flex justify-center">
            <div className="w-full max-w-md bg-slate-900/90 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-2xl backdrop-blur-md">
              
              {/* Brand Logo & Header */}
              <div className="mb-6 text-center lg:text-left">
                <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-md shadow-blue-600/30 mb-4 mx-auto lg:mx-0">
                  <Sparkles className="w-5 h-5" />
                </div>
                <h2 className="text-xl font-bold text-white tracking-tight">Welcome back</h2>
                <p className="text-xs text-slate-400 mt-1">
                  Sign in to access your enterprise knowledge workspace.
                </p>
              </div>

              {/* Error Alert */}
              {error && (
                <div className="mb-5 p-3 rounded-lg bg-red-500/10 border border-red-500/25 flex items-start gap-2.5 text-red-400 text-xs">
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              {/* Form */}
              <form onSubmit={handleLogin} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5" htmlFor="work-email">
                    Work email
                  </label>
                  <input
                    id="work-email"
                    type="email"
                    required
                    autoComplete="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@company.com"
                    className="w-full px-3.5 py-2.5 rounded-lg bg-slate-950/80 border border-slate-700 text-white text-xs placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="block text-xs font-medium text-slate-300" htmlFor="current-password">
                      Password
                    </label>
                    <Link
                      to="/forgot-password"
                      className="text-[11px] text-blue-400 hover:text-blue-300 transition-colors"
                    >
                      Forgot password?
                    </Link>
                  </div>
                  <div className="relative">
                    <input
                      id="current-password"
                      type={showPassword ? 'text' : 'password'}
                      required
                      autoComplete="current-password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Enter your password"
                      className="w-full pl-3.5 pr-10 py-2.5 rounded-lg bg-slate-950/80 border border-slate-700 text-white text-xs placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-200"
                      tabIndex={-1}
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full mt-2 py-2.5 px-4 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs transition-colors flex items-center justify-center gap-2 shadow-lg shadow-blue-600/25 disabled:opacity-50 cursor-pointer"
                >
                  {loading ? (
                    <>
                      <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      <span>Signing in...</span>
                    </>
                  ) : (
                    <>
                      <span>Sign In</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </>
                  )}
                </button>
              </form>

              {/* Security Badge */}
              <div className="mt-5 flex items-center justify-center gap-1.5 text-[11px] text-slate-500">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
                <span>Your access is protected by enterprise authentication and authorization controls.</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="w-full max-w-6xl mx-auto pt-4 border-t border-slate-800/60 flex flex-col sm:flex-row items-center justify-between text-[11px] text-slate-500 gap-2">
        <div>&copy; 2026 Enterprise Knowledge Platform. All rights reserved.</div>
        <div className="flex items-center gap-4">
          <span className="hover:text-slate-400 cursor-pointer">Privacy Policy</span>
          <span>&bull;</span>
          <span className="hover:text-slate-400 cursor-pointer">Security Standards</span>
          <span>&bull;</span>
          <span className="hover:text-slate-400 cursor-pointer">Terms of Service</span>
        </div>
      </footer>
    </div>
  );
};
