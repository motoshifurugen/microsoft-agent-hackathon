// ホーム: 検索時は検索結果、通常時は 今日のおすすめ + 困りごと入力 + マッチ結果。
import { useMemo, useState } from "react";
import { Sparkles } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { PainInput } from "@/components/PainInput";
import { SectionLabel } from "@/components/SectionLabel";
import { TodayCard } from "@/components/TodayCard";
import { useAppData } from "@/context/appDataContext";
import type { CaseDetail } from "@/types/api";

function EmptyHint({ children }: { children: React.ReactNode }) {
  return (
    <p className="rounded-lg border border-dashed border-[var(--color-border)] px-4 py-6 text-center text-sm text-[var(--color-muted-foreground)]">
      {children}
    </p>
  );
}

export function HomePage() {
  const { today, allCases, clientId, searchQuery, renderCase } = useAppData();
  const [painResult, setPainResult] = useState<{ query: string; cases: CaseDetail[] } | null>(null);

  const trimmedQuery = searchQuery.trim();
  const hasQuery = trimmedQuery.length > 0;

  const searchResults = useMemo(() => {
    if (!hasQuery) return [];
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
  }, [allCases, hasQuery, trimmedQuery]);

  return (
    <>
      <PageHeader title="ホーム" />
      <main className="mx-auto flex w-full max-w-[968px] flex-1 flex-col gap-8 px-6 py-8">
        {hasQuery ? (
          <section>
            <SectionLabel icon={<Sparkles className="h-3.5 w-3.5" />}>
              検索結果
              <span className="ml-1 text-[var(--color-muted-foreground)]">
                — 「{trimmedQuery}」に一致 {searchResults.length} 件
              </span>
            </SectionLabel>
            <div className="grid gap-3 pt-3">
              {searchResults.map(renderCase)}
              {searchResults.length === 0 && (
                <EmptyHint>
                  {allCases.length === 0
                    ? "事例を読み込み中…"
                    : "条件に一致する事例が見つかりません"}
                </EmptyHint>
              )}
            </div>
          </section>
        ) : (
          <>
            {today && <TodayCard today={today} />}

            <PainInput clientId={clientId} onResult={(query, cases) => setPainResult({ query, cases })} />

            {painResult && (
              <section>
                <SectionLabel icon={<Sparkles className="h-3.5 w-3.5" />}>
                  あなたの困りごとに近い事例
                  <span className="ml-1 text-[var(--color-muted-foreground)]">
                    — 「{painResult.query}」{painResult.cases.length} 件
                  </span>
                </SectionLabel>
                <div className="grid gap-3 pt-3">
                  {painResult.cases.map(renderCase)}
                  {painResult.cases.length === 0 && (
                    <EmptyHint>
                      近い事例はまだありません。あなたが最初の成功事例を共有してみませんか？
                    </EmptyHint>
                  )}
                </div>
              </section>
            )}
          </>
        )}
      </main>
    </>
  );
}
