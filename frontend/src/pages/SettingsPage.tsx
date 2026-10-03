import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import {
  User,
  Shield,
  Globe,
  KeyRound,
  CheckCircle2,
  AlertCircle,
  LogOut,
  Sun,
  Moon,
} from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'profile' | 'preferences' | 'security' | 'account'>('profile');

  // Password state
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordMsg, setPasswordMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [passwordLoading, setPasswordLoading] = useState(false);

  // Preference states
  const [language, setLanguage] = useState('en');
  const [theme, setTheme] = useState<'light' | 'system'>('light');
  const [notifications, setNotifications] = useState({
    emailUpdates: true,
    securityAlerts: true,
  });

  const getRoleDisplayName = (role?: string) => {
    switch (role) {
      case 'ADMIN':
        return 'System Administrator';
      case 'HR':
        return 'HR Specialist';
      case 'FINANCE':
        return 'Finance Specialist';
      case 'SECURITY':
        return 'Security Officer';
      default:
        return 'Standard Employee';
    }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPassword || !confirmPassword) {
      setPasswordMsg({ type: 'error', text: 'Please fill in all password fields.' });
      return;
    }
    if (newPassword.length < 8) {
      setPasswordMsg({ type: 'error', text: 'Password must be at least 8 characters long.' });
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordMsg({ type: 'error', text: 'New passwords do not match.' });
      return;
    }

    setPasswordLoading(true);
    setPasswordMsg(null);

    try {
      if (user?.email) {
        const forgotRes = await api.forgotPassword(user.email);
        if (forgotRes.reset_token) {
          await api.resetPassword(forgotRes.reset_token, newPassword);
          setPasswordMsg({ type: 'success', text: 'Password updated successfully.' });
          setNewPassword('');
          setConfirmPassword('');
        } else {
          setPasswordMsg({
            type: 'success',
            text: 'Password update requested. Please verify through your email.',
          });
        }
      }
    } catch (err: any) {
      setPasswordMsg({ type: 'error', text: err.message || 'Failed to update password.' });
    } finally {
      setPasswordLoading(false);
    }
  };

  const handleSignOutAllSessions = async () => {
    if (window.confirm('Are you sure you want to sign out from all sessions?')) {
      await logout();
      navigate('/login');
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-4 sm:p-6 md:p-8 space-y-6 font-sans">
      {/* Page Header */}
      <div className="border-b border-slate-200/80 pb-5">
        <h2 className="text-xl font-bold tracking-tight text-slate-900">Settings</h2>
        <p className="text-xs text-slate-500 mt-1">
          Manage your enterprise profile, security preferences, and workspace settings.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        {/* Navigation Tabs */}
        <div className="md:col-span-4 lg:col-span-3 flex md:flex-col gap-1.5 overflow-x-auto no-scrollbar pb-1 md:pb-0 md:space-y-1">
          <button
            type="button"
            onClick={() => setActiveTab('profile')}
            className={`flex items-center gap-2.5 px-3.5 py-2.5 rounded-xl text-xs font-medium transition-colors text-left cursor-pointer shrink-0 md:w-full ${
              activeTab === 'profile'
                ? 'bg-white border border-slate-200 text-blue-600 font-semibold shadow-2xs'
                : 'text-slate-600 hover:bg-white hover:text-slate-900'
            }`}
          >
            <User className="w-4 h-4 shrink-0" />
            <span>Profile</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('preferences')}
            className={`flex items-center gap-2.5 px-3.5 py-2.5 rounded-xl text-xs font-medium transition-colors text-left cursor-pointer shrink-0 md:w-full ${
              activeTab === 'preferences'
                ? 'bg-white border border-slate-200 text-blue-600 font-semibold shadow-2xs'
                : 'text-slate-600 hover:bg-white hover:text-slate-900'
            }`}
          >
            <Globe className="w-4 h-4 shrink-0" />
            <span>Preferences</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('security')}
            className={`flex items-center gap-2.5 px-3.5 py-2.5 rounded-xl text-xs font-medium transition-colors text-left cursor-pointer shrink-0 md:w-full ${
              activeTab === 'security'
                ? 'bg-white border border-slate-200 text-blue-600 font-semibold shadow-2xs'
                : 'text-slate-600 hover:bg-white hover:text-slate-900'
            }`}
          >
            <KeyRound className="w-4 h-4 shrink-0" />
            <span>Security</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('account')}
            className={`flex items-center gap-2.5 px-3.5 py-2.5 rounded-xl text-xs font-medium transition-colors text-left cursor-pointer shrink-0 md:w-full ${
              activeTab === 'account'
                ? 'bg-white border border-slate-200 text-blue-600 font-semibold shadow-2xs'
                : 'text-slate-600 hover:bg-white hover:text-slate-900'
            }`}
          >
            <Shield className="w-4 h-4 shrink-0" />
            <span>Account Details</span>
          </button>
        </div>

        {/* Tab Content */}
        <div className="md:col-span-8 lg:col-span-9 bg-white border border-slate-200/80 rounded-2xl p-6 shadow-2xs">
          {/* Profile Tab */}
          {activeTab === 'profile' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-sm font-bold text-slate-900">Profile Information</h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Your identity details associated with the enterprise platform.
                </p>
              </div>

              <div className="flex items-center gap-4 pt-2">
                <div className="w-14 h-14 rounded-full bg-slate-100 border border-slate-300 flex items-center justify-center text-lg font-bold text-slate-700 shrink-0">
                  {user?.full_name?.charAt(0).toUpperCase() || 'U'}
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-slate-900">{user?.full_name}</h4>
                  <p className="text-xs text-slate-500">{user?.email}</p>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">
                    Full Name
                  </label>
                  <input
                    type="text"
                    readOnly
                    value={user?.full_name || ''}
                    className="w-full px-3.5 py-2 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-700 cursor-not-allowed"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">
                    Work Email
                  </label>
                  <input
                    type="email"
                    readOnly
                    value={user?.email || ''}
                    className="w-full px-3.5 py-2 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-700 cursor-not-allowed"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">
                    Department
                  </label>
                  <input
                    type="text"
                    readOnly
                    value={user?.department || 'General'}
                    className="w-full px-3.5 py-2 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-700 cursor-not-allowed"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Preferences Tab */}
          {activeTab === 'preferences' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-sm font-bold text-slate-900">Workspace Preferences</h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Customize language, theme, and communication settings.
                </p>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">
                    Theme
                  </label>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => setTheme('light')}
                      className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium border cursor-pointer ${
                        theme === 'light'
                          ? 'bg-blue-50 border-blue-300 text-blue-700 font-semibold'
                          : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                      }`}
                    >
                      <Sun className="w-3.5 h-3.5" />
                      <span>Light</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setTheme('system')}
                      className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium border cursor-pointer ${
                        theme === 'system'
                          ? 'bg-blue-50 border-blue-300 text-blue-700 font-semibold'
                          : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                      }`}
                    >
                      <Globe className="w-3.5 h-3.5" />
                      <span>System Default</span>
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">
                    Language
                  </label>
                  <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="w-full max-w-xs px-3.5 py-2 rounded-lg bg-white border border-slate-200 text-xs text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="en">English (United States)</option>
                    <option value="es">Español (Spanish)</option>
                    <option value="fr">Français (French)</option>
                    <option value="de">Deutsch (German)</option>
                  </select>
                </div>

                <div className="pt-3 border-t border-slate-100 space-y-3">
                  <h4 className="text-xs font-semibold text-slate-800">Notifications</h4>
                  <label className="flex items-center gap-2.5 text-xs text-slate-700 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={notifications.emailUpdates}
                      onChange={(e) =>
                        setNotifications({ ...notifications, emailUpdates: e.target.checked })
                      }
                      className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span>Receive enterprise policy update notifications</span>
                  </label>
                  <label className="flex items-center gap-2.5 text-xs text-slate-700 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={notifications.securityAlerts}
                      onChange={(e) =>
                        setNotifications({ ...notifications, securityAlerts: e.target.checked })
                      }
                      className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span>Receive login and security alerts</span>
                  </label>
                </div>
              </div>
            </div>
          )}

          {/* Security Tab */}
          {activeTab === 'security' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-sm font-bold text-slate-900">Security & Password</h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Change your enterprise password or manage active sessions.
                </p>
              </div>

              {passwordMsg && (
                <div
                  className={`p-3 rounded-lg text-xs flex items-center gap-2 ${
                    passwordMsg.type === 'success'
                      ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                      : 'bg-red-50 text-red-800 border border-red-200'
                  }`}
                >
                  {passwordMsg.type === 'success' ? (
                    <CheckCircle2 className="w-4 h-4 shrink-0" />
                  ) : (
                    <AlertCircle className="w-4 h-4 shrink-0" />
                  )}
                  <span>{passwordMsg.text}</span>
                </div>
              )}

              <form onSubmit={handlePasswordChange} className="space-y-4 max-w-sm">
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">
                    New Password
                  </label>
                  <input
                    type="password"
                    required
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Enter new password (min. 8 chars)"
                    className="w-full px-3.5 py-2 rounded-lg bg-white border border-slate-200 text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">
                    Confirm New Password
                  </label>
                  <input
                    type="password"
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Confirm new password"
                    className="w-full px-3.5 py-2 rounded-lg bg-white border border-slate-200 text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <button
                  type="submit"
                  disabled={passwordLoading}
                  className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium transition-colors disabled:opacity-50 cursor-pointer"
                >
                  {passwordLoading ? 'Updating password...' : 'Update Password'}
                </button>
              </form>

              <div className="pt-4 border-t border-slate-100">
                <h4 className="text-xs font-bold text-slate-800 mb-1">Session Management</h4>
                <p className="text-xs text-slate-500 mb-3">
                  Sign out from all active sessions and devices across the enterprise network.
                </p>
                <button
                  type="button"
                  onClick={handleSignOutAllSessions}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-red-200 text-red-600 hover:bg-red-50 text-xs font-medium transition-colors cursor-pointer"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span>Sign out from all sessions</span>
                </button>
              </div>
            </div>
          )}

          {/* Account Details Tab */}
          {activeTab === 'account' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-sm font-bold text-slate-900">Account Information</h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Information regarding your authorized account tier and organizational access.
                </p>
              </div>

              <div className="space-y-3 divide-y divide-slate-100 text-xs">
                <div className="flex items-center justify-between py-2">
                  <span className="text-slate-500 font-medium">Access Tier</span>
                  <span className="font-semibold text-slate-800">{getRoleDisplayName(user?.role)}</span>
                </div>
                <div className="flex items-center justify-between py-2">
                  <span className="text-slate-500 font-medium">Department</span>
                  <span className="font-semibold text-slate-800">{user?.department || 'General'}</span>
                </div>
                <div className="flex items-center justify-between py-2">
                  <span className="text-slate-500 font-medium">Account Status</span>
                  <span className="inline-flex items-center gap-1.5 text-emerald-700 font-semibold">
                    <span className="w-2 h-2 rounded-full bg-emerald-500" />
                    Active & Verified
                  </span>
                </div>
                <div className="flex items-center justify-between py-2">
                  <span className="text-slate-500 font-medium">Session ID</span>
                  <span className="font-mono text-slate-400 text-[11px]">auth_sess_{user?.id || '0'}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
