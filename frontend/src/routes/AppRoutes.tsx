import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../layouts/DashboardLayout';
import { LoginPage } from '../pages/LoginPage';
import { RegisterPage } from '../pages/RegisterPage';
import { ForgotPasswordPage } from '../pages/ForgotPasswordPage';
import { ResetPasswordPage } from '../pages/ResetPasswordPage';
import { AssistantPage } from '../pages/AssistantPage';
import { ConversationsPage } from '../pages/ConversationsPage';
import { SettingsPage } from '../pages/SettingsPage';
import { AdminPage } from '../pages/AdminPage';
import { UserRole } from '../types';

const ProtectedRoute: React.FC<{ children: React.ReactNode; allowedRoles?: UserRole[] }> = ({
  children,
  allowedRoles,
}) => {
  const { isAuthenticated, isLoading, user } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-300 text-xs">
        <div className="flex items-center gap-2">
          <span className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <span>Authenticating session...</span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/assistant" replace />;
  }

  return <>{children}</>;
};

export const AppRoutes: React.FC = () => {
  const { isAuthenticated, isLoading, user } = useAuth();

  return (
    <Routes>
      <Route
        path="/login"
        element={isAuthenticated && !isLoading ? <Navigate to="/assistant" replace /> : <LoginPage />}
      />
      <Route
        path="/register"
        element={isAuthenticated && !isLoading ? <Navigate to="/assistant" replace /> : <RegisterPage />}
      />
      <Route
        path="/forgot-password"
        element={isAuthenticated && !isLoading ? <Navigate to="/assistant" replace /> : <ForgotPasswordPage />}
      />
      <Route
        path="/reset-password"
        element={isAuthenticated && !isLoading ? <Navigate to="/assistant" replace /> : <ResetPasswordPage />}
      />

      <Route
        path="/"
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/assistant" replace />} />
        <Route path="assistant" element={<AssistantPage />} />
        <Route path="conversations" element={<ConversationsPage />} />
        <Route path="settings" element={<SettingsPage />} />

        {/* Administration (Admin only) */}
        <Route
          path="admin"
          element={
            <ProtectedRoute allowedRoles={['ADMIN']}>
              <AdminPage />
            </ProtectedRoute>
          }
        />

        {/* Redirect any legacy endpoints to admin or assistant */}
        <Route
          path="documents"
          element={<Navigate to={user?.role === 'ADMIN' ? '/admin' : '/assistant'} replace />}
        />
        <Route path="policies" element={<Navigate to="/assistant" replace />} />
        <Route
          path="evaluation"
          element={<Navigate to={user?.role === 'ADMIN' ? '/admin' : '/assistant'} replace />}
        />
        <Route
          path="analytics"
          element={<Navigate to={user?.role === 'ADMIN' ? '/admin' : '/assistant'} replace />}
        />
        <Route
          path="audit"
          element={<Navigate to={user?.role === 'ADMIN' ? '/admin' : '/assistant'} replace />}
        />
      </Route>

      <Route path="*" element={<Navigate to="/assistant" replace />} />
    </Routes>
  );
};
