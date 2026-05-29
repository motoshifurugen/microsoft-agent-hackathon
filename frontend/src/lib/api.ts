// Kodama API client (fetch wrapper)
// Vite dev server は /api を localhost:8001 にプロキシ。本番ビルドでは同一オリジン想定。

import type {
  BoardAnswer,
  BoardQuestion,
  BoardQuestionDetail,
  CaseDetail,
  CategoryCasesResponse,
  CategorySummary,
  PainMatchResponse,
  RecommendationResponse,
  StrategyExecuteResponse,
  StrategyId,
  TodayPick,
  UserSummary,
} from "@/types/api";

const BASE = "/api";

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) {
    throw new Error(`GET ${path} failed: ${res.status}`);
  }
  return (await res.json()) as T;
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`POST ${path} failed: ${res.status}`);
  }
  return (await res.json()) as T;
}

async function deleteJson<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { method: "DELETE" });
  if (!res.ok) {
    throw new Error(`DELETE ${path} failed: ${res.status}`);
  }
  return (await res.json()) as T;
}

// 社員系
export const fetchCategories = (): Promise<CategorySummary[]> => getJson("/categories");

export const fetchCasesInCategory = (name: string): Promise<CategoryCasesResponse> =>
  getJson(`/categories/${encodeURIComponent(name)}/cases`);

export const fetchToday = (): Promise<TodayPick> => getJson("/today");

export const matchPain = (payload: {
  text: string;
  client_id?: string;
  business_context?: string;
  top_k?: number;
}): Promise<PainMatchResponse> => postJson("/pain/match", payload);

// Skill ブックマーク (サーバー側永続)。いずれも当該 client_id の保存事例一覧を返す。
// 成功事例の登録 (共有フォーム)
export const createCase = (payload: {
  client_id: string;
  owner_label: string;
  business_type: string;
  what_worked: string;
  why_worked?: string;
  concrete_prompt?: string;
  quantitative_effect?: string;
  reproducibility_score?: number;
}): Promise<CaseDetail> => postJson("/cases", payload);

export const fetchBookmarks = (clientId: string): Promise<CaseDetail[]> =>
  getJson(`/bookmarks?client_id=${encodeURIComponent(clientId)}`);

export const addBookmark = (clientId: string, caseId: string): Promise<CaseDetail[]> =>
  postJson("/bookmarks", { client_id: clientId, case_id: caseId });

export const removeBookmark = (clientId: string, caseId: string): Promise<CaseDetail[]> =>
  deleteJson(
    `/bookmarks?client_id=${encodeURIComponent(clientId)}&case_id=${encodeURIComponent(caseId)}`,
  );

// 管理者系
export const fetchAdminUsers = (): Promise<UserSummary[]> => getJson("/admin/users");

export const fetchRecommendations = (userId: string): Promise<RecommendationResponse> =>
  getJson(`/admin/users/${encodeURIComponent(userId)}/recommendations`);

export const executeStrategy = (
  strategyId: StrategyId,
  targetUserId: string,
  caseId: string,
): Promise<StrategyExecuteResponse> =>
  postJson(`/admin/strategies/${strategyId}/execute`, {
    target_user_id: targetUserId,
    case_id: caseId,
  });

// 困りごと掲示板
export const fetchBoardQuestions = (): Promise<BoardQuestion[]> => getJson("/board/questions");

export const fetchBoardQuestionDetail = (id: string): Promise<BoardQuestionDetail> =>
  getJson(`/board/questions/${encodeURIComponent(id)}`);

export const createBoardQuestion = (payload: {
  title: string;
  body: string;
  business_category?: string | null;
  author?: string;
}): Promise<BoardQuestion> => postJson("/board/questions", payload);

export const createBoardAnswer = (
  questionId: string,
  payload: { body: string; author?: string },
): Promise<BoardAnswer> =>
  postJson(`/board/questions/${encodeURIComponent(questionId)}/answers`, payload);
