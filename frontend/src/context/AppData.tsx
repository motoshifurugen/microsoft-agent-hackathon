// アプリ全体で共有する状態とデータ取得を集約する Provider。
// 各ページの CaseCard が prop drilling なしで動くよう、ブックマーク・フィードバック・
// コピー（試した記録）・検索クエリと、サーバーから取得した事例/カテゴリの元データを保持する。
import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { CaseCard } from "@/components/CaseCard";
import {
  AppDataContext,
  type AppDataValue,
  type FeedbackValue,
} from "@/context/appDataContext";
import { useClientId } from "@/hooks/useClientId";
import { useLocalStorageJson } from "@/hooks/useLocalStorageJson";
import {
  addBookmark,
  fetchBookmarks,
  fetchCasesInCategory,
  fetchCategories,
  fetchMyCases,
  fetchToday,
  removeBookmark,
} from "@/lib/api";
import type { CaseDetail, CategorySummary, TodayPick } from "@/types/api";

const FEEDBACK_KEY = "kodama-feedback";
const TRIED_KEY = "kodama-tried";
const COPY_FLASH_MS = 1600;

export function AppDataProvider({ children }: { children: ReactNode }) {
  const clientId = useClientId();
  const feedback = useLocalStorageJson(FEEDBACK_KEY);
  const tried = useLocalStorageJson(TRIED_KEY);

  const [today, setToday] = useState<TodayPick | null>(null);
  const [categories, setCategories] = useState<CategorySummary[]>([]);
  const [allCases, setAllCases] = useState<CaseDetail[]>([]);
  const [myCases, setMyCases] = useState<CaseDetail[]>([]);
  const [bookmarks, setBookmarks] = useState<CaseDetail[]>([]);
  const [copyFlash, setCopyFlash] = useState<string | null>(null);

  useEffect(() => {
    fetchToday()
      .then(setToday)
      .catch(() => setToday(null));

    fetchCategories()
      .then(async (c) => {
        setCategories(c);
        const results = await Promise.all(
          c.map((cat) => fetchCasesInCategory(cat.name).catch(() => null)),
        );
        setAllCases(results.flatMap((r) => (r ? r.cases : [])));
      })
      .catch(() => setCategories([]));
  }, []);

  useEffect(() => {
    fetchBookmarks(clientId)
      .then(setBookmarks)
      .catch(() => setBookmarks([]));

    fetchMyCases(clientId)
      .then(setMyCases)
      .catch(() => setMyCases([]));
  }, [clientId]);

  const bookmarkedIds = useMemo(() => new Set(bookmarks.map((b) => b.case_id)), [bookmarks]);

  const toggleBookmark = useCallback(
    async (caseId: string) => {
      const mutate = bookmarkedIds.has(caseId) ? removeBookmark : addBookmark;
      try {
        setBookmarks(await mutate(clientId, caseId));
      } catch {
        // ネットワーク失敗時は状態を変えない (次回操作で再同期)
      }
    },
    [bookmarkedIds, clientId],
  );

  const handleCopy = useCallback(
    (caseId: string, text: string) => {
      if (!text) return;
      void navigator.clipboard.writeText(text);
      tried.set(caseId, new Date().toISOString());
      setCopyFlash("プロンプトをコピーしました");
      setTimeout(() => setCopyFlash(null), COPY_FLASH_MS);
    },
    [tried],
  );

  const handleFeedback = useCallback(
    (caseId: string, value: FeedbackValue) => {
      feedback.toggle(caseId, value);
    },
    [feedback],
  );

  const handleCaseCreated = useCallback((created: CaseDetail) => {
    setAllCases((prev) => [created, ...prev]);
    setMyCases((prev) => [created, ...prev]);
  }, []);

  const renderCase = useCallback(
    (c: CaseDetail) => (
      <CaseCard
        key={c.case_id}
        caseDetail={c}
        feedback={feedback.value[c.case_id] as FeedbackValue | undefined}
        bookmarked={bookmarkedIds.has(c.case_id)}
        onCopy={() => handleCopy(c.case_id, c.concrete_prompt)}
        onFeedback={(v) => handleFeedback(c.case_id, v)}
        onToggleBookmark={() => void toggleBookmark(c.case_id)}
      />
    ),
    [feedback.value, bookmarkedIds, handleCopy, handleFeedback, toggleBookmark],
  );

  const value = useMemo<AppDataValue>(
    () => ({
      clientId,
      today,
      categories,
      allCases,
      myCases,
      bookmarks,
      bookmarkedIds,
      feedbackByCase: feedback.value,
      triedByCase: tried.value,
      copyFlash,
      toggleBookmark,
      handleCopy,
      handleFeedback,
      handleCaseCreated,
      renderCase,
    }),
    [
      clientId,
      today,
      categories,
      allCases,
      myCases,
      bookmarks,
      bookmarkedIds,
      feedback.value,
      tried.value,
      copyFlash,
      toggleBookmark,
      handleCopy,
      handleFeedback,
      handleCaseCreated,
      renderCase,
    ],
  );

  return <AppDataContext.Provider value={value}>{children}</AppDataContext.Provider>;
}
