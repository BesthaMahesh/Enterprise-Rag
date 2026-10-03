export type UserRole = 'EMPLOYEE' | 'HR' | 'FINANCE' | 'ADMIN' | 'SECURITY';

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  department: string;
  is_active: boolean;
  created_at: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export interface SourceCitation {
  document_id: string;
  document_title: string;
  section?: string;
  page_number?: number;
  classification: string;
  snippet?: string;
  relevance_score?: number;
  allowed_roles: string[];
}

export interface RetrievalDebugMetrics {
  dense_count: number;
  sparse_count: number;
  rrf_fused_count: number;
  reranked_count: number;
  authorized_document_count: number;
  context_tokens: number;
  retrieval_latency_ms: number;
  llm_latency_ms: number;
  total_latency_ms: number;
  estimated_cost_usd: number;
  grounding_score: number;
  acl_decision: string;
  guardrail_decision: string;
  query_classification: string;
}

export interface ChatMessage {
  id: string;
  conversation_id?: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  sources?: SourceCitation[];
  metrics?: RetrievalDebugMetrics;
  tokens?: number;
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages?: ChatMessage[];
}

export interface DocumentItem {
  id: number;
  document_id: string;
  title: string;
  file_name: string;
  file_path: string;
  file_type: string;
  domain: string;
  classification: string;
  allowed_roles: string[];
  version: string;
  effective_date: string;
  status: string;
  chunk_count: number;
  language: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentChunkItem {
  id: number;
  chunk_id: string;
  document_id: string;
  chunk_index: number;
  content: string;
  section?: string;
  page_number?: number;
  token_count: number;
  allowed_roles: string[];
  classification: string;
}

export interface EvaluationSummary {
  runs_count: number;
  latest_run?: {
    id: string;
    run_name: string;
    evaluator_type: string;
    total_questions: number;
    metrics_summary: any;
    status: string;
    created_at: string;
    completed_at?: string;
  };
  retrieval_metrics: {
    recall_at_5: number;
    precision_at_5: number;
    mrr: number;
    ndcg: number;
  };
  generation_metrics: {
    faithfulness: number;
    answer_relevance: number;
    groundedness: number;
  };
  acl_metrics: {
    acl_precision: number;
    unauthorized_retrieval_rate: number;
    unauthorized_answer_rate: number;
    acl_recall: number;
  };
  security_metrics: {
    prompt_injection_block_rate: number;
    pii_leakage_rate: number;
  };
  operational_metrics: {
    average_latency_ms: number;
    total_time_ms: number;
    error_rate: number;
  };
}

export interface AuditLogItem {
  id: number;
  request_id: string;
  trace_id: string;
  user_email: string;
  role: string;
  action: string;
  resource?: string;
  query?: string;
  acl_decision: string;
  reason?: string;
  latency_ms: number;
  status_code: number;
  metadata?: any;
  created_at: string;
}

export interface AnalyticsData {
  summary: {
    total_queries: number;
    acl_denials: number;
    prompt_injections: number;
    average_latency_ms: number;
    total_indexed_documents: number;
    grounding_pass_rate: number;
  };
  role_distribution: { role: string; count: number }[];
  decision_distribution: { decision: string; count: number }[];
  recent_activity: {
    id: number;
    timestamp: string;
    user: string;
    role: string;
    action: string;
    decision: string;
    latency_ms: number;
  }[];
}
