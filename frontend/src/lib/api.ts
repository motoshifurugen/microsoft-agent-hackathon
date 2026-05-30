// Kodama API client (fetch wrapper)
// Vite dev server は /api を localhost:8001 にプロキシ。本番ビルドでは同一オリジン想定。

import type {
  BoardAnswer,
  BoardQuestion,
  BoardQuestionDetail,
  CaseDetail,
  CategoryCasesResponse,
  CategorySummary,
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

// 登録セレクト用の固定カテゴリマスタ (表示順)。
export const fetchCategoryMaster = (): Promise<string[]> => getJson("/categories/master");

// 自分 (client_id) が登録した成功事例を新しい順で取得。
export const fetchMyCases = (clientId: string): Promise<CaseDetail[]> =>
  getJson(`/cases?client_id=${encodeURIComponent(clientId)}`);

export const fetchToday = (): Promise<TodayPick> => getJson("/today");

// AIに相談チャット。/api/agent/chat の SSE を ReadableStream で受信し、トークンを逐次中継する。
export interface AgentChatHandlers {
  onToken: (text: string) => void;
  onDone: () => void;
  onError: (message: string) => void;
}

export async function streamAgentChat(
  payload: { message: string; client_id?: string },
  handlers: AgentChatHandlers,
  signal?: AbortSignal,
): Promise<void> {
  let res: Response;
  try {
    res = await fetch(`${BASE}/agent/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal,
    });
  } catch {
    handlers.onError("AI への接続に失敗しました");
    return;
  }

  if (!res.ok || !res.body) {
    handlers.onError(`チャットの開始に失敗しました (${res.status})`);
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  const dispatch = (raw: string) => {
    const line = raw.trim();
    if (!line.startsWith("data:")) return;
    const body = line.slice(5).trim();
    if (!body) return;
    try {
      const evt = JSON.parse(body) as { type: string; text?: string; message?: string };
      if (evt.type === "token" && evt.text) handlers.onToken(evt.text);
      else if (evt.type === "done") handlers.onDone();
      else if (evt.type === "error") handlers.onError(evt.message ?? "エラーが発生しました");
    } catch {
      // 不完全な JSON は無視 (次チャンクで補完される)
    }
  };

  try {
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() ?? "";
      for (const part of parts) dispatch(part);
    }
    if (buffer.trim()) dispatch(buffer);
  } catch {
    handlers.onError("ストリームの受信中にエラーが発生しました");
  }
}

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
