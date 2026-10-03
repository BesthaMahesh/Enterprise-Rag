import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { Conversation } from '../types';
import {
  History,
  MessageSquare,
  Search,
  Plus,
  Calendar,
  ArrowRight,
  Trash2,
} from 'lucide-react';

export const ConversationsPage: React.FC = () => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    setLoading(true);
    try {
      const data = await api.getConversations();
      setConversations(data);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (e: React.MouseEvent, convId: string) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this conversation?')) return;

    setDeletingId(convId);
    try {
      await api.deleteConversation(convId);
      setConversations((prev) => prev.filter((c) => c.id !== convId));
    } catch {
      // ignore
    } finally {
      setDeletingId(null);
    }
  };

  const filtered = conversations.filter((c) =>
    (c.title || '').toLowerCase().includes(search.trim().toLowerCase())
  );

  // Group by date
  const groupConversations = (convs: Conversation[]) => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    const lastWeek = new Date(today);
    lastWeek.setDate(lastWeek.getDate() - 7);

    const groups: { [key: string]: Conversation[] } = {
      Today: [],
      Yesterday: [],
      'Previous 7 Days': [],
      Older: [],
    };

    convs.forEach((c) => {
      const convDate = new Date(c.updated_at || c.created_at);
      if (convDate >= today) {
        groups.Today.push(c);
      } else if (convDate >= yesterday) {
        groups.Yesterday.push(c);
      } else if (convDate >= lastWeek) {
        groups['Previous 7 Days'].push(c);
      } else {
        groups.Older.push(c);
      }
    });

    return groups;
  };

  const grouped = groupConversations(filtered);

  return (
    <div className="max-w-4xl mx-auto p-4 sm:p-6 md:p-8 space-y-6 font-sans">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-5">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <History className="w-5 h-5 text-blue-600" />
            <span>Conversations</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Access previous knowledge queries and continue your conversations.
          </p>
        </div>

        <button
          type="button"
          onClick={() => navigate('/assistant', { state: { newChat: true } })}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium transition-colors shadow-sm shadow-blue-600/20 cursor-pointer shrink-0"
        >
          <Plus className="w-4 h-4" />
          <span>New Conversation</span>
        </button>
      </div>

      {/* Search Bar */}
      <div className="relative">
        <Search className="w-4 h-4 absolute left-3.5 top-3 text-slate-400" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search conversation history..."
          className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-white border border-slate-200 text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 shadow-2xs"
        />
      </div>

      {/* List */}
      {loading ? (
        <div className="p-12 text-center text-xs text-slate-400 flex items-center justify-center gap-2">
          <span className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
          <span>Loading conversation history...</span>
        </div>
      ) : filtered.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center max-w-md mx-auto space-y-3 shadow-2xs">
          <div className="w-10 h-10 rounded-xl bg-slate-100 text-slate-400 flex items-center justify-center mx-auto">
            <MessageSquare className="w-5 h-5" />
          </div>
          <h3 className="text-sm font-semibold text-slate-800">No conversations found</h3>
          <p className="text-xs text-slate-500">
            {search
              ? 'No conversations match your search query.'
              : 'You have not started any conversations yet.'}
          </p>
          <button
            type="button"
            onClick={() => navigate('/assistant', { state: { newChat: true } })}
            className="mt-2 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 text-white text-xs font-medium hover:bg-blue-500 transition-colors cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Start a conversation</span>
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          {Object.entries(grouped).map(([groupTitle, convs]) => {
            if (convs.length === 0) return null;
            return (
              <div key={groupTitle} className="space-y-2">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 px-1">
                  {groupTitle}
                </h4>

                <div className="grid grid-cols-1 gap-2">
                  {convs.map((conv) => (
                    <div
                      key={conv.id}
                      onClick={() =>
                        navigate('/assistant', {
                          state: { conversationId: conv.id },
                        })
                      }
                      className="p-4 rounded-xl bg-white border border-slate-200/80 hover:border-blue-400 hover:bg-blue-50/20 transition-all shadow-2xs cursor-pointer flex items-center justify-between gap-4 group"
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <div className="w-8 h-8 rounded-lg bg-blue-50 group-hover:bg-blue-100 text-blue-600 flex items-center justify-center shrink-0 transition-colors">
                          <MessageSquare className="w-4 h-4" />
                        </div>
                        <div className="min-w-0">
                          <h5 className="text-xs font-semibold text-slate-800 group-hover:text-blue-700 truncate transition-colors">
                            {conv.title || 'Untitled Conversation'}
                          </h5>
                          <div className="flex items-center gap-3 text-[11px] text-slate-400 mt-0.5">
                            <span className="flex items-center gap-1">
                              <Calendar className="w-3 h-3" />
                              {new Date(conv.updated_at || conv.created_at).toLocaleDateString(
                                undefined,
                                {
                                  month: 'short',
                                  day: 'numeric',
                                  year: 'numeric',
                                }
                              )}
                            </span>
                            {conv.messages && conv.messages.length > 0 && (
                              <span>&bull; {conv.messages.length} messages</span>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-3 shrink-0">
                        <button
                          type="button"
                          disabled={deletingId === conv.id}
                          onClick={(e) => handleDelete(e, conv.id)}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 transition-colors cursor-pointer"
                          title="Delete conversation"
                          aria-label="Delete conversation"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                        <div className="flex items-center gap-1 text-slate-400 group-hover:text-blue-600 transition-colors">
                          <span className="text-xs font-medium hidden sm:inline">Resume</span>
                          <ArrowRight className="w-4 h-4" />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
