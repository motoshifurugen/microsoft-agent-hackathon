// FastAPI のレスポンス型に対応する TypeScript 型定義

export interface CaseDetail {
  case_id: string;
  owner_label: string;
  business_type: string;
  what_worked: string;
  why_worked: string;
  concrete_prompt: string;
  quantitative_effect: string;
  reproducibility_score: number;
  score: number;
}

export interface CategorySummary {
  name: string;
  case_count: number;
  sample_owner_label: string;
}

export interface CategoryCasesResponse {
  category: string;
  cases: CaseDetail[];
}

export interface TodayPick {
  case: CaseDetail;
  headline: string;
}

export interface UserSummary {
  user_id: string;
  owner_label: string;
  business_type: string;
  quantitative_effect: string;
}

export type StrategyId = "A" | "B";

export interface Strategy {
  id: StrategyId;
  title: string;
  description: string;
}

export interface RecommendationResponse {
  target_user_id: string;
  target_owner_label: string;
  target_business_type: string;
  cases: CaseDetail[];
  strategies: Strategy[];
}

export interface StrategyExecuteResponse {
  execution_id: string;
  strategy_id: StrategyId;
  target_user_id: string;
  case_id: string;
  message_preview: string;
  executed_at: string;
}

export interface PainMatchResponse {
  pain_point_id: string;
  query: string;
  cases: CaseDetail[];
}

export interface BoardQuestion {
  id: string;
  title: string;
  body: string;
  business_category: string | null;
  author: string;
  created_at: string;
  answer_count: number;
}

export interface BoardAnswer {
  id: string;
  question_id: string;
  body: string;
  author: string;
  created_at: string;
}

export interface BoardQuestionDetail extends BoardQuestion {
  answers: BoardAnswer[];
}
