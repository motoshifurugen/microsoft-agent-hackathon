import { useCallback, useEffect, useState } from "react";
import { Compass, Heart, Sparkles } from "lucide-react";
import { BoardSection } from "@/components/BoardSection";
import { CaseCard } from "@/components/CaseCard";
import { CategoryGrid } from "@/components/CategoryGrid";
import { SectionLabel } from "@/components/SectionLabel";
import { ShareCTA } from "@/components/ShareCTA";
import { ThemeToggle } from "@/components/ThemeToggle";
import { TodaySection } from "@/components/TodaySection";
import { useLocalStorageJson } from "@/hooks/useLocalStorageJson";
import { fetchCasesInCategory, fetchCategories, fetchToday } from "@/lib/api";
import type { CaseDetail, CategorySummary, TodayPick } from "@/types/api";

const FEEDBACK_KEY = "kodama-feedback";
const TRIED_KEY = "kodama-tried";

export default function App() {
  const [today, setToday] = useState<TodayPick | null>(null);
  const [categories, setCategories] = useState<CategorySummary[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [cases, setCases] = useState<CaseDetail[]>([]);
  const [copyFlash, setCopyFlash] = useState<string | null>(null);

  const feedback = useLocalStorageJson(FEEDBACK_KEY);
  const tried = useLocalStorageJson(TRIED_KEY);

  useEffect(() => {
    fetchToday()
      .then(setToday)
      .catch(() => setToday(null));
    fetchCategories()
      .then((c) => {
        setCategories(c);
        if (!selectedCategory && c[0]) setSelectedCategory(c[0].name);
      })
      .catch(() => setCategories([]));
    // 初期マウント時のみ。selectedCategory 依存は除外する。
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!selectedCategory) return;
    fetchCasesInCategory(selectedCategory)
      .then((r) => setCases(r.cases))
      .catch(() => setCases([]));
  }, [selectedCategory]);

  const handleCopy = useCallback(
    (caseId: string, text: string) => {
      if (!text) return;
      void navigator.clipboard.writeText(text);
      tried.set(caseId, new Date().toISOString());
      setCopyFlash("プロンプトをコピーしました");
      setTimeout(() => setCopyFlash(null), 1600);
    },
    [tried],
  );

  const handleFeedback = useCallback(
    (caseId: string, value: "good" | "soso") => {
      feedback.toggle(caseId, value);
    },
    [feedback],
  );

  const handleShareIntent = useCallback(() => {
    setCopyFlash("ご自身の成功例は DX 推進部にメッセージで共有してください");
    setTimeout(() => setCopyFlash(null), 2500);
  }, []);

  const triedCases = Object.entries(tried.value)
    .sort(([, a], [, b]) => (b ?? "").localeCompare(a ?? ""))
    .map(([cid]) => cases.find((c) => c.case_id === cid))
    .filter((c): c is CaseDetail => Boolean(c))
    .slice(0, 3);

  return (
    <div className="min-h-screen bg-[var(--color-background)] text-[var(--color-foreground)]">
      <header className="sticky top-0 z-10 border-b border-[var(--color-border)] bg-[var(--color-card)]/95 backdrop-blur">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-5 py-3">
          <div className="flex items-center gap-2">
            <Compass className="h-5 w-5 text-[var(--color-primary)]" />
            <div className="leading-tight">
              <div className="text-base font-semibold">Kodama</div>
              <div className="text-[11px] text-[var(--color-muted-foreground)]">
                社内の小さな成功を、次の誰かの力に
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {copyFlash && <span className="text-xs text-[var(--color-primary)]">{copyFlash}</span>}
            <ThemeToggle />
          </div>
        </div>
      </header>

      <main className="mx-auto flex max-w-3xl flex-col gap-7 px-5 py-7">
        {today && <TodaySection today={today} />}

        <section>
          <div className="inline-block rounded-md bg-[var(--color-primary)]/10 px-2 py-0.5 text-[10px] font-semibold tracking-wider text-[var(--color-primary)]">
            活用シーン
          </div>
          <h2 className="mt-2 text-2xl font-bold leading-tight">あなたの業務、どこで使える？</h2>
          <p className="mt-1 text-sm text-[var(--color-muted-foreground)]">
            {categories.length} の業務カテゴリ — 当てはまる場面を 1 つでも見つけよう
          </p>
          <div className="mt-4">
            <CategoryGrid
              categories={categories}
              selected={selectedCategory}
              onSelect={setSelectedCategory}
            />
          </div>
        </section>

        <section>
          <SectionLabel icon={<Sparkles className="h-3.5 w-3.5" />}>
            {selectedCategory ?? "事例"} の事例 ({cases.length})
          </SectionLabel>
          <div className="grid gap-3 pt-2">
            {cases.map((c) => (
              <CaseCard
                key={c.case_id}
                caseDetail={c}
                feedback={feedback.value[c.case_id] as "good" | "soso" | undefined}
                onCopy={() => handleCopy(c.case_id, c.concrete_prompt)}
                onFeedback={(v) => handleFeedback(c.case_id, v)}
              />
            ))}
            {cases.length === 0 && (
              <p className="text-sm text-[var(--color-muted-foreground)]">事例を読み込み中…</p>
            )}
          </div>
        </section>

        {triedCases.length > 0 && (
          <section>
            <SectionLabel icon={<Heart className="h-3.5 w-3.5" />}>最近試したもの</SectionLabel>
            <ul className="grid gap-2 pt-2 text-sm">
              {triedCases.map((c) => (
                <li
                  key={c.case_id}
                  className="rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] px-3 py-2"
                >
                  <div className="font-medium">{c.owner_label}の事例</div>
                  <div className="text-xs text-[var(--color-muted-foreground)]">
                    {c.business_type}・{c.quantitative_effect || "効果未登録"}
                  </div>
                </li>
              ))}
            </ul>
          </section>
        )}

        <BoardSection categories={categories.map((c) => c.name)} />

        <ShareCTA onClick={handleShareIntent} />

        <footer className="pb-6 pt-2 text-center text-[11px] text-[var(--color-muted-foreground)]">
          Kodama — Microsoft Agent Hackathon 2026
        </footer>
      </main>
    </div>
  );
}
