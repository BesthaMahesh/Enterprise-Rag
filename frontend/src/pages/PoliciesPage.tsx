import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { DocumentItem } from '../types';
import { BookOpen, FileText, ChevronRight, Sparkles, CheckCircle2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const PoliciesPage: React.FC = () => {
  const [policies, setPolicies] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    loadPolicies();
  }, []);

  const loadPolicies = async () => {
    setLoading(true);
    try {
      const docs = await api.getDocuments();
      // Filter for general policies
      setPolicies(docs);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  const askAboutPolicy = (title: string) => {
    navigate('/assistant');
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-slate-900">HR Policies & Enterprise Handbook</h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Standard organizational guidelines and policy documents accessible under your current clearance.
        </p>
      </div>

      {loading ? (
        <div className="py-12 text-center text-xs text-slate-400">Loading enterprise policies...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {policies.map((pol) => (
            <div
              key={pol.id}
              className="bg-white border border-slate-200 rounded-xl p-5 shadow-2xs hover:border-blue-400 transition-all space-y-3 flex flex-col justify-between"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
                    <FileText className="w-4 h-4" />
                  </div>
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
                    v{pol.version}
                  </span>
                </div>
                <h3 className="text-sm font-bold text-slate-900">{pol.title}</h3>
                <p className="text-xs text-slate-500">
                  Domain: {pol.domain} &bull; {pol.chunk_count} Sections
                </p>
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                <span className="text-[10px] text-slate-400">
                  Effective: {pol.effective_date || '2026-01-01'}
                </span>
                <button
                  onClick={() => askAboutPolicy(pol.title)}
                  className="flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-700 cursor-pointer"
                >
                  <span>Ask AI</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
