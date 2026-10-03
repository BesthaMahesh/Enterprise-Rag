import React, { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { ChatMessage, SourceCitation } from '../types';
import { MarkdownRenderer } from '../components/MarkdownRenderer';
import {
  Send,
  Sparkles,
  Bot,
  Copy,
  Check,
  RotateCcw,
  ThumbsUp,
  ThumbsDown,
  FileText,
  X,
  ArrowRight,
  AlertCircle,
  ExternalLink,
} from 'lucide-react';

interface GroupedSource {
  document_title: string;
  sections: string[];
  snippets: string[];
}

export const AssistantPage: React.FC = () => {
  const { user } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputQuery, setInputQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [lastQuery, setLastQuery] = useState<string>('');
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [feedbackState, setFeedbackState] = useState<Record<string, 'up' | 'down'>>({});
  const [activeSource, setActiveSource] = useState<GroupedSource | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const resetChatState = () => {
    sessionStorage.removeItem('active_conversation_id');
    setConversationId(undefined);
    setMessages([]);
    setInputQuery('');
    setErrorMessage(null);
    setActiveSource(null);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.focus();
    }
  };

  const loadSpecificConversation = async (convId: string) => {
    try {
      setIsLoading(true);
      const details = await api.getConversation(convId);
      setConversationId(details.id);
      sessionStorage.setItem('active_conversation_id', details.id);
      if (details.messages) {
        setMessages(
          details.messages.map((m: any) => ({
            id: m.id,
            conversation_id: m.conversation_id,
            role: m.role,
            content: m.content,
            sources: m.sources,
            metrics: m.metrics,
            tokens: m.tokens,
            created_at: m.created_at,
          }))
        );
      }
    } catch {
      sessionStorage.removeItem('active_conversation_id');
      setErrorMessage('Could not load this conversation. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // Handle incoming route state & restore active conversation
  useEffect(() => {
    if (location.state?.newChat) {
      sessionStorage.removeItem('active_conversation_id');
      resetChatState();
    } else if (location.state?.conversationId) {
      sessionStorage.setItem('active_conversation_id', location.state.conversationId);
      loadSpecificConversation(location.state.conversationId);
    } else {
      const activeId = sessionStorage.getItem('active_conversation_id');
      if (activeId && (!conversationId || messages.length === 0)) {
        loadSpecificConversation(activeId);
      }
    }
  }, [location.state]);

  // Listen for custom in-page new conversation event
  useEffect(() => {
    const handleNewConvEvent = () => resetChatState();
    window.addEventListener('chat:new-conversation', handleNewConvEvent);
    return () => window.removeEventListener('chat:new-conversation', handleNewConvEvent);
  }, []);

  // Scroll to bottom when messages update
  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading, errorMessage]);

  const handleSend = async (queryText?: string) => {
    const q = (queryText !== undefined ? queryText : inputQuery).trim();
    if (!q || isLoading) return;

    setLastQuery(q);
    setErrorMessage(null);

    const userMsgId = `usr_${Date.now()}`;
    const userMessage: ChatMessage = {
      id: userMsgId,
      role: 'user',
      content: q,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputQuery('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
    setIsLoading(true);

    try {
      const res = await api.sendChat(q, conversationId, false);
      setConversationId(res.conversation_id);
      sessionStorage.setItem('active_conversation_id', res.conversation_id);

      const assistantMessage: ChatMessage = {
        id: res.message_id,
        conversation_id: res.conversation_id,
        role: 'assistant',
        content: res.answer,
        sources: res.sources,
        metrics: res.metrics,
        created_at: res.created_at,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      // Restore input text so user does not lose question
      setInputQuery(q);
      setErrorMessage(err.message || 'Something went wrong while processing your question.');
    } finally {
      setIsLoading(false);
      setTimeout(() => textareaRef.current?.focus(), 100);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputQuery(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 180)}px`;
  };

  const copyToClipboard = (text: string, msgId: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(msgId);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleFeedback = async (msgId: string, type: 'up' | 'down') => {
    const current = feedbackState[msgId];
    const newFeedback = current === type ? undefined : type;

    setFeedbackState((prev) => ({
      ...prev,
      [msgId]: newFeedback!,
    }));

    if (newFeedback) {
      try {
        await api.sendFeedback({
          message_id: msgId,
          feedback: newFeedback,
          conversation_id: conversationId,
        });
      } catch {
        // feedback recorded optimistically
      }
    }
  };

  const handleRegenerate = (index: number) => {
    for (let i = index - 1; i >= 0; i--) {
      if (messages[i].role === 'user') {
        handleSend(messages[i].content);
        break;
      }
    }
  };

  // Group and strictly deduplicate sources by document title
  const getGroupedSources = (sources?: SourceCitation[]): GroupedSource[] => {
    if (!sources || sources.length === 0) return [];

    const map = new Map<string, GroupedSource>();

    sources.forEach((src) => {
      const docTitle = src.document_title || 'Authorized Document';
      const cleanSection = src.section ? src.section.replace(/Acme Technologies\s*[\u2014-]\s*/gi, '').trim() : 'Overview';

      if (!map.has(docTitle)) {
        map.set(docTitle, {
          document_title: docTitle,
          sections: cleanSection ? [cleanSection] : ['Overview'],
          snippets: src.snippet ? [src.snippet] : [],
        });
      } else {
        const item = map.get(docTitle)!;
        if (cleanSection && !item.sections.includes(cleanSection)) {
          item.sections.push(cleanSection);
        }
        if (src.snippet && !item.snippets.includes(src.snippet)) {
          item.snippets.push(src.snippet);
        }
      }
    });

    return Array.from(map.values());
  };

  const suggestedPrompts = [
    'What is the leave policy?',
    'Can I work remotely?',
    'What employee benefits are available?',
    'How do I request business travel?',
  ];

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)] bg-slate-50/50 relative overflow-hidden font-sans">
      {/* Messages Stream */}
      <div className="flex-1 overflow-y-auto px-4 sm:px-6 md:px-8 py-6 space-y-6">
        {messages.length === 0 ? (
          <div className="max-w-xl mx-auto my-auto pt-8 sm:pt-14 pb-8 text-center flex flex-col items-center justify-center">
            {/* AI Icon */}
            <div className="w-12 h-12 rounded-2xl bg-blue-600/10 border border-blue-600/20 text-blue-600 flex items-center justify-center mb-4 shadow-xs">
              <Sparkles className="w-6 h-6" />
            </div>

            <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 mb-2">
              Enterprise AI Assistant
            </h2>
            <h3 className="text-sm sm:text-base font-medium text-slate-700 mb-2">
              How can I help you today?
            </h3>

            <p className="text-xs sm:text-sm text-slate-500 max-w-md leading-relaxed mb-8">
              Ask about workplace policies, benefits, procedures, and other information available to you.
            </p>

            {/* Suggested Prompts Grid */}
            <div className="w-full grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-left">
              {suggestedPrompts.map((prompt, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSend(prompt)}
                  className="p-3.5 rounded-xl bg-white border border-slate-200/90 hover:border-blue-400 hover:bg-blue-50/40 text-slate-700 hover:text-blue-700 text-xs font-medium transition-all shadow-2xs flex items-center justify-between gap-2.5 group cursor-pointer"
                >
                  <span className="leading-snug">{prompt}</span>
                  <ArrowRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-blue-600 transition-colors shrink-0" />
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="max-w-3xl mx-auto space-y-6">
            {messages.map((msg, index) => {
              const groupedSources = msg.role === 'assistant' ? getGroupedSources(msg.sources) : [];

              return (
                <div
                  key={msg.id}
                  className={`flex gap-3.5 ${
                    msg.role === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  {/* Assistant Avatar */}
                  {msg.role === 'assistant' && (
                    <div className="w-8 h-8 rounded-lg bg-blue-600 text-white flex items-center justify-center shrink-0 shadow-xs mt-0.5">
                      <Bot className="w-4 h-4" />
                    </div>
                  )}

                  {/* Message Bubble Container */}
                  <div
                    className={`flex flex-col space-y-2 max-w-[94%] sm:max-w-[85%] ${
                      msg.role === 'user' ? 'items-end' : 'items-start'
                    }`}
                  >
                    <div
                      className={`p-3.5 sm:p-5 rounded-2xl text-xs sm:text-[13px] leading-relaxed ${
                        msg.role === 'user'
                          ? 'bg-slate-900 text-white rounded-tr-none shadow-xs'
                          : 'bg-white border border-slate-200/90 text-slate-800 rounded-tl-none shadow-2xs'
                      }`}
                    >
                      {msg.role === 'user' ? (
                        <div className="whitespace-pre-wrap">{msg.content}</div>
                      ) : (
                        <MarkdownRenderer content={msg.content} />
                      )}

                      {/* Deduplicated Sources Section */}
                      {msg.role === 'assistant' && groupedSources.length > 0 && (
                        <div className="mt-4 pt-3.5 border-t border-slate-100">
                          <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-2.5 flex items-center justify-between">
                            <span className="flex items-center gap-1.5">
                              <FileText className="w-3.5 h-3.5 text-blue-600" />
                              <span>Sources</span>
                            </span>
                            <span className="text-[10px] text-slate-400 font-normal lowercase tracking-normal">
                              Based on authorized knowledge
                            </span>
                          </div>

                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                            {groupedSources.map((gSrc, srcIdx) => (
                              <div
                                key={srcIdx}
                                className="p-2.5 rounded-xl bg-slate-50/80 border border-slate-200/80 hover:border-blue-300 hover:bg-blue-50/30 transition-all flex flex-col justify-between gap-2"
                              >
                                <div>
                                  <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-800">
                                    <FileText className="w-3.5 h-3.5 text-blue-600 shrink-0" />
                                    <span className="truncate">{gSrc.document_title}</span>
                                  </div>
                                  <p className="text-[11px] text-slate-500 mt-0.5 line-clamp-1">
                                    Relevant section: {gSrc.sections.join(', ')}
                                  </p>
                                </div>
                                <button
                                  type="button"
                                  onClick={() => setActiveSource(gSrc)}
                                  className="inline-flex items-center gap-1 text-[11px] font-medium text-blue-600 hover:text-blue-700 cursor-pointer self-start py-1"
                                >
                                  <span>View source</span>
                                  <ArrowRight className="w-3 h-3" />
                                </button>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Actions Bar for Assistant */}
                    {msg.role === 'assistant' && (
                      <div className="flex flex-wrap items-center gap-1 sm:gap-1.5 pl-0.5 text-slate-400 text-xs">
                        <button
                          type="button"
                          onClick={() => copyToClipboard(msg.content, msg.id)}
                          className="inline-flex items-center gap-1 px-2 py-1.5 hover:bg-white rounded-lg text-slate-500 hover:text-slate-800 transition-colors cursor-pointer border border-transparent hover:border-slate-200 active:scale-95"
                          title="Copy answer"
                          aria-label="Copy answer"
                        >
                          {copiedId === msg.id ? (
                            <>
                              <Check className="w-3.5 h-3.5 text-emerald-600" />
                              <span className="text-[11px] text-emerald-600 font-medium">Copied</span>
                            </>
                          ) : (
                            <>
                              <Copy className="w-3.5 h-3.5" />
                              <span className="text-[11px]">Copy</span>
                            </>
                          )}
                        </button>

                        <button
                          type="button"
                          onClick={() => handleFeedback(msg.id, 'up')}
                          className={`inline-flex items-center gap-1 px-2 py-1.5 rounded-lg transition-colors cursor-pointer border active:scale-95 ${
                            feedbackState[msg.id] === 'up'
                              ? 'bg-blue-50 border-blue-200 text-blue-700 font-semibold'
                              : 'border-transparent hover:border-slate-200 hover:bg-white text-slate-500 hover:text-slate-800'
                          }`}
                          title="Helpful"
                          aria-label="Helpful"
                        >
                          <ThumbsUp className="w-3.5 h-3.5" />
                          <span className="text-[11px]">Helpful</span>
                        </button>

                        <button
                          type="button"
                          onClick={() => handleFeedback(msg.id, 'down')}
                          className={`inline-flex items-center gap-1 px-2 py-1.5 rounded-lg transition-colors cursor-pointer border active:scale-95 ${
                            feedbackState[msg.id] === 'down'
                              ? 'bg-red-50 border-red-200 text-red-700 font-semibold'
                              : 'border-transparent hover:border-slate-200 hover:bg-white text-slate-500 hover:text-slate-800'
                          }`}
                          title="Not helpful"
                          aria-label="Not helpful"
                        >
                          <ThumbsDown className="w-3.5 h-3.5" />
                          <span className="text-[11px] hidden xs:inline sm:inline">Not helpful</span>
                        </button>

                        <button
                          type="button"
                          onClick={() => handleRegenerate(index)}
                          className="inline-flex items-center gap-1 px-2 py-1.5 hover:bg-white rounded-lg text-slate-500 hover:text-slate-800 transition-colors cursor-pointer border border-transparent hover:border-slate-200 active:scale-95"
                          title="Regenerate response"
                          aria-label="Regenerate response"
                        >
                          <RotateCcw className="w-3.5 h-3.5" />
                          <span className="text-[11px] hidden xs:inline sm:inline">Regenerate</span>
                        </button>
                      </div>
                    )}
                  </div>

                  {/* User Avatar */}
                  {msg.role === 'user' && (
                    <div className="w-8 h-8 rounded-full bg-slate-800 text-white flex items-center justify-center shrink-0 text-xs font-bold shadow-xs mt-0.5">
                      {user?.full_name?.charAt(0).toUpperCase() || 'U'}
                    </div>
                  )}
                </div>
              );
            })}

            {/* Loading State */}
            {isLoading && (
              <div className="flex gap-3.5 justify-start">
                <div className="w-8 h-8 rounded-lg bg-blue-600 text-white flex items-center justify-center shrink-0 shadow-xs">
                  <Bot className="w-4 h-4 animate-pulse" />
                </div>
                <div className="p-4 rounded-2xl bg-white border border-slate-200/90 text-xs text-slate-600 rounded-tl-none shadow-2xs flex items-center gap-2.5">
                  <div className="flex gap-1 items-center">
                    <span className="w-1.5 h-1.5 bg-blue-600 rounded-full animate-bounce [animation-delay:-0.3s]" />
                    <span className="w-1.5 h-1.5 bg-blue-600 rounded-full animate-bounce [animation-delay:-0.15s]" />
                    <span className="w-1.5 h-1.5 bg-blue-600 rounded-full animate-bounce" />
                  </div>
                  <span className="font-medium text-slate-500">Assistant is thinking...</span>
                </div>
              </div>
            )}

            {/* Error State */}
            {errorMessage && (
              <div className="p-4 rounded-xl bg-red-50/80 border border-red-200 text-xs text-red-800 flex items-center justify-between gap-3 shadow-2xs">
                <div className="flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
                  <span>{errorMessage}</span>
                </div>
                {lastQuery && (
                  <button
                    type="button"
                    onClick={() => handleSend(lastQuery)}
                    className="px-3 py-1.5 rounded-lg bg-red-600 text-white text-xs font-medium hover:bg-red-700 transition-colors shrink-0 cursor-pointer"
                  >
                    Try again
                  </button>
                )}
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Clean Source Preview Modal */}
      {activeSource && (
        <div
          className="fixed inset-0 bg-slate-900/50 z-50 flex items-center justify-center p-3 sm:p-4 backdrop-blur-2xs"
          onClick={() => setActiveSource(null)}
        >
          <div
            className="w-[94%] sm:w-full max-w-lg bg-white rounded-2xl border border-slate-200 shadow-2xl p-4 sm:p-6 overflow-hidden flex flex-col space-y-4 animate-in fade-in zoom-in-95 duration-150 max-h-[85vh]"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-3 border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2.5 min-w-0">
                <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
                  <FileText className="w-4 h-4" />
                </div>
                <div className="min-w-0">
                  <h3 className="text-sm font-bold text-slate-900 truncate">
                    {activeSource.document_title}
                  </h3>
                  <p className="text-[11px] text-slate-500 truncate">
                    Relevant section: {activeSource.sections.join(', ')}
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={() => setActiveSource(null)}
                className="p-1 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-100 cursor-pointer min-w-[32px] min-h-[32px] flex items-center justify-center"
                aria-label="Close preview"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="bg-slate-50 rounded-xl p-3 sm:p-4 border border-slate-100 text-xs text-slate-700 leading-relaxed max-h-60 sm:max-h-72 overflow-y-auto space-y-3">
              <p className="font-semibold text-slate-500 text-[11px] uppercase tracking-wider">
                Relevant Excerpt
              </p>
              {activeSource.snippets.map((snip, sIdx) => (
                <div key={sIdx} className="bg-white p-3 rounded-lg border border-slate-200/80 whitespace-pre-wrap leading-relaxed text-slate-800">
                  {snip}
                </div>
              ))}
            </div>

            <div className="flex justify-end pt-1">
              <button
                type="button"
                onClick={() => setActiveSource(null)}
                className="w-full sm:w-auto px-4 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-medium transition-colors cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Chat Composer */}
      <div className="p-2.5 sm:p-4 bg-white border-t border-slate-200/90 shrink-0">
        <div className="max-w-3xl mx-auto">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="relative flex items-end rounded-2xl border border-slate-300/80 bg-slate-50/70 focus-within:border-blue-500 focus-within:bg-white focus-within:ring-2 focus-within:ring-blue-500/10 transition-all p-1.5 sm:p-2 shadow-2xs"
          >
            <textarea
              ref={textareaRef}
              rows={1}
              value={inputQuery}
              onChange={handleTextareaChange}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything about your workplace..."
              className="flex-1 max-h-36 py-1.5 px-2.5 sm:px-3 bg-transparent text-xs sm:text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none resize-none leading-relaxed"
            />

            <button
              type="submit"
              disabled={isLoading || !inputQuery.trim()}
              className="p-2 sm:p-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white transition-colors disabled:opacity-40 disabled:hover:bg-blue-600 cursor-pointer shrink-0 shadow-sm min-w-[38px] min-h-[38px] flex items-center justify-center active:scale-95"
              aria-label="Send query"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>

          <p className="text-[10px] sm:text-[11px] text-center text-slate-400 mt-1.5 sm:mt-2">
            Answers are grounded in authorized enterprise knowledge.
          </p>
        </div>
      </div>
    </div>
  );
};
