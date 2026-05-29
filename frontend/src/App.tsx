import { useCallback, useEffect, useMemo, useState } from "react";
import { Compass, Heart, Search, Sparkles } from "lucide-react";
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
  const [allCases, setAllCases] = useState<CaseDetail[]>([]);
  const [copyFlash, setCopyFlash] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  const feedback = useLocalStorageJson(FEEDBACK_KEY);
  const tried = useLocalStorageJson(TRIED_KEY);

  useEffect(() => {
    fetchToday()
      .then(setToday)
      .catch(() => setToday(null));

    fetchCategories()
      .then(async (c) => {
        setCategories(c);
        if (c[0]) setSelectedCategory(c[0].name);
        const results = await Promise.all(
          c.map((cat) => fetchCasesInCategory(cat.name).catch(() => null)),
        );
        const merged = results.flatMap((r) => (r ? r.cases : []));
        setAllCases(merged);
      })
      .catch(() => setCategories([]));
  }, []);

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

  const trimmedQuery = searchQuery.trim();
  const hasQuery = trimmedQuery.length > 0;

  const displayedCases = useMemo(() => {
    if (hasQuery) {
      const q = trimmedQuery.toLowerCase();
      return allCases.filter((c) =>
        [
          c.owner_label,
          c.business_type,
          c.what_worked,
          c.why_worked,
          c.concrete_prompt,
          c.quantitative_effect,
        ].some((field) => field?.toLowerCase().includes(q)),
      );
    }
    if (!selectedCategory) return allCases;
    return allCases.filter((c) => c.business_type === selectedCategory);
  }, [allCases, hasQuery, trimmedQuery, selectedCategory]);

  const triedCases = Object.entries(tried.value)
    .sort(([, a], [, b]) => (b ?? "").localeCompare(a ?? ""))
    .map(([cid]) => allCases.find((c) => c.case_id === cid))
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

      <main className="mx-auto flex max-w-3xl flex-col gap-8 px-5 py-8">
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-muted-foreground)]" />
          <input
            type="search"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="事例を検索（業務・効果・プロンプトなど）"
            className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] py-2.5 pl-9 pr-3 text-sm shadow-sm outline-none transition-colors focus:border-[var(--color-primary)] focus:ring-2 focus:ring-[var(--color-primary)]/20"
          />
        </div>

        {!hasQuery && (
          <section>
            <SectionLabel>業務カテゴリで探す</SectionLabel>
            <div className="mt-3">
              <CategoryGrid
                categories={categories}
                selected={selectedCategory}
                onSelect={setSelectedCategory}
              />
            </div>
          </section>
        )}

        <section>
          <SectionLabel icon={<Sparkles className="h-3.5 w-3.5" />}>
            {hasQuery ? (
              <>
                検索結果
                <span className="ml-1 text-[var(--color-muted-foreground)]">
                  — 「{trimmedQuery}」に一致 {displayedCases.length} 件
                </span>
              </>
            ) : (
              <>
                {selectedCategory ?? "事例"}
                <span className="ml-1 text-[var(--color-muted-foreground)]">
                  — {displayedCases.length} 件
                </span>
              </>
            )}
          </SectionLabel>
          <div className="grid gap-3 pt-3">
            {displayedCases.map((c) => (
              <CaseCard
                key={c.case_id}
                caseDetail={c}
                feedback={feedback.value[c.case_id] as "good" | "soso" | undefined}
                onCopy={() => handleCopy(c.case_id, c.concrete_prompt)}
                onFeedback={(v) => handleFeedback(c.case_id, v)}
              />
            ))}
            {displayedCases.length === 0 && (
              <p className="rounded-lg border border-dashed border-[var(--color-border)] px-4 py-6 text-center text-sm text-[var(--color-muted-foreground)]">
                {allCases.length === 0
                  ? "事例を読み込み中…"
                  : "条件に一致する事例が見つかりません"}
              </p>
            )}
          </div>
        </section>

        {!hasQuery && today && <TodaySection today={today} />}

        {!hasQuery && triedCases.length > 0 && (
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

        {!hasQuery && <BoardSection categories={categories.map((c) => c.name)} />}

        {!hasQuery && <ShareCTA onClick={handleShareIntent} />}

        <footer className="pb-6 pt-2 text-center text-[11px] text-[var(--color-muted-foreground)]">
          Kodama — Microsoft Agent Hackathon 2026
        </footer>
      </main>
    </div>
  );
}
