import {
  User,
  Conversation,
  DocumentItem,
  DocumentChunkItem,
  EvaluationSummary,
  AuditLogItem,
  AnalyticsData,
  ChatMessage
} from '../types';

const envApiUrl = (import.meta.env.VITE_API_URL as string | undefined)?.trim().replace(/\/+$/, '') || '';
const API_BASE = envApiUrl
  ? (envApiUrl.endsWith('/api') ? envApiUrl : `${envApiUrl}/api`)
  : '/api';

function getAuthHeader(): Record<string, string> {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function fetchWithRetry(input: RequestInfo | URL, init?: RequestInit, retries = 2): Promise<Response> {
  try {
    return await window.fetch(input, init);
  } catch (err: any) {
    if (retries > 0) {
      await new Promise((r) => setTimeout(r, 2000));
      return fetchWithRetry(input, init, retries - 1);
    }
    throw new Error('Backend server is connecting or waking up from idle. Please click "Try again".');
  }
}
const fetch = fetchWithRetry;

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = 'Something went wrong while processing your request.';
    try {
      const errJson = await res.json();
      errorDetail = errJson.detail || errJson.message || errorDetail;
    } catch {
      if (res.status === 401) {
        errorDetail = 'Session expired. Please sign in again.';
      } else if (res.status === 403) {
        errorDetail = "I'm sorry, I don't have access to that information.";
      } else if (res.status === 429) {
        errorDetail = 'Too many requests. Please try again shortly.';
      } else if (res.status >= 500) {
        errorDetail = 'Something went wrong. Please try again.';
      } else {
        errorDetail = `${res.status} ${res.statusText}`;
      }
    }
    if (res.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.dispatchEvent(new Event('auth:unauthorized'));
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export const api = {
  // Auth
  async login(email: string, password: string) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    return handleResponse<{
      access_token: string;
      token_type: string;
      role: string;
      email: string;
      full_name: string;
      department: string;
    }>(res);
  },

  async forgotPassword(email: string) {
    const res = await fetch(`${API_BASE}/auth/forgot-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    });
    return handleResponse<{ message: string; reset_token?: string }>(res);
  },

  async resetPassword(token: string, new_password: string) {
    const res = await fetch(`${API_BASE}/auth/reset-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token, new_password }),
    });
    return handleResponse<{ message: string }>(res);
  },

  async logout() {
    const res = await fetch(`${API_BASE}/auth/logout`, {
      method: 'POST',
      headers: { ...getAuthHeader() },
    });
    return handleResponse<{ message: string }>(res);
  },

  async getMe() {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: { ...getAuthHeader() },
    });
    return handleResponse<User>(res);
  },

  // Chat
  async sendChat(query: string, conversation_id?: string, include_debug_metrics: boolean = true) {
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeader(),
      },
      body: JSON.stringify({
        query,
        conversation_id,
        include_debug_metrics,
      }),
    });
    return handleResponse<{
      conversation_id: string;
      message_id: string;
      answer: string;
      sources: any[];
      acl_decision: string;
      grounding_score: number;
      query_class: string;
      metrics?: any;
      created_at: string;
    }>(res);
  },

  async getConversations() {
    const res = await fetch(`${API_BASE}/conversations`, {
      headers: { ...getAuthHeader() },
    });
    return handleResponse<Conversation[]>(res);
  },

  async getConversation(id: string) {
    const res = await fetch(`${API_BASE}/conversations/${id}`, {
      headers: { ...getAuthHeader() },
    });
    return handleResponse<Conversation>(res);
  },

  async deleteConversation(id: string) {
    const res = await fetch(`${API_BASE}/conversations/${id}`, {
      method: 'DELETE',
      headers: { ...getAuthHeader() },
    });
    return handleResponse<{ message: string; id: string }>(res);
  },

  async sendFeedback(data: {
    message_id: string;
    feedback: 'up' | 'down';
    conversation_id?: string;
    comments?: string;
  }) {
    const res = await fetch(`${API_BASE}/chat/feedback`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeader(),
      },
      body: JSON.stringify(data),
    });
    return handleResponse<{ status: string; message_id: string }>(res);
  },

  // Documents
  async getDocuments(params?: { classification?: string; domain?: string; search?: string }) {
    const query = new URLSearchParams();
    if (params?.classification) query.set('classification', params.classification);
    if (params?.domain) query.set('domain', params.domain);
    if (params?.search) query.set('search', params.search);

    const res = await fetch(`${API_BASE}/documents?${query.toString()}`, {
      headers: { ...getAuthHeader() },
    });
    return handleResponse<DocumentItem[]>(res);
  },

  async getDocument(docId: string) {
    const res = await fetch(`${API_BASE}/documents/${docId}`, {
      headers: { ...getAuthHeader() },
    });
    return handleResponse<DocumentItem>(res);
  },

  async getDocumentChunks(docId: string) {
    const res = await fetch(`${API_BASE}/documents/${docId}/chunks`, {
      headers: { ...getAuthHeader() },
    });
    return handleResponse<DocumentChunkItem[]>(res);
  },

  async uploadDocument(formData: FormData) {
    const res = await fetch(`${API_BASE}/documents/upload`, {
      method: 'POST',
      headers: { ...getAuthHeader() },
      body: formData,
    });
    return handleResponse<DocumentItem>(res);
  },

  async reindexDocument(docId: string) {
    const res = await fetch(`${API_BASE}/documents/${docId}/reindex`, {
      method: 'POST',
      headers: { ...getAuthHeader() },
    });
    return handleResponse<{ success: boolean; document_id: string; chunks_indexed: number; message: string }>(res);
  },

  async deleteDocument(docId: string) {
    const res = await fetch(`${API_BASE}/documents/${docId}`, {
      method: 'DELETE',
      headers: { ...getAuthHeader() },
    });
    return handleResponse<{ message: string }>(res);
  },

  // Search
  async directSearch(query: string, topK: number = 5) {
    const res = await fetch(`${API_BASE}/search?q=${encodeURIComponent(query)}&top_k=${topK}`, {
      headers: { ...getAuthHeader() },
    });
    return handleResponse<{ query: string; role: string; results: any[] }>(res);
  },

  // Evaluation
  async getEvaluationSummary() {
    const res = await fetch(`${API_BASE}/evaluation`, {
      headers: { ...getAuthHeader() },
    });
    return handleResponse<EvaluationSummary>(res);
  },

  async runEvaluation(run_name?: string) {
    const res = await fetch(`${API_BASE}/evaluation/run`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeader(),
      },
      body: JSON.stringify({ run_name }),
    });
    return handleResponse<any>(res);
  },

  async getEvaluationRuns() {
    const res = await fetch(`${API_BASE}/evaluation/runs`, {
      headers: { ...getAuthHeader() },
    });
    return handleResponse<any[]>(res);
  },

  async getEvaluationRunDetails(runId: string) {
    const res = await fetch(`${API_BASE}/evaluation/runs/${runId}`, {
      headers: { ...getAuthHeader() },
    });
    return handleResponse<any>(res);
  },

  // Analytics & Observability
  async getAnalytics(days: number = 7) {
    const res = await fetch(`${API_BASE}/analytics?days=${days}`, {
      headers: { ...getAuthHeader() },
    });
    return handleResponse<AnalyticsData>(res);
  },

  // Audit
  async getAuditLogs(params?: { role?: string; action?: string; decision?: string; limit?: number; offset?: number }) {
    const query = new URLSearchParams();
    if (params?.role) query.set('role', params.role);
    if (params?.action) query.set('action', params.action);
    if (params?.decision) query.set('decision', params.decision);
    if (params?.limit) query.set('limit', params.limit.toString());
    if (params?.offset) query.set('offset', params.offset.toString());

    const res = await fetch(`${API_BASE}/audit?${query.toString()}`, {
      headers: { ...getAuthHeader() },
    });
    return handleResponse<{ total: number; offset: number; limit: number; logs: AuditLogItem[] }>(res);
  },

  // Health
  async getHealth() {
    const res = await fetch(`${API_BASE}/health`);
    return handleResponse<any>(res);
  }
};
