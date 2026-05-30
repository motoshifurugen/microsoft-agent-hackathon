// ホーム上部の「今日のおすすめ」カード。左に見出し/本文/アクション、右に WHAT WORKED 引用・
// 定量効果・帰属を分割表示する。コピーは試した記録と連動する。
import { ArrowRight, Copy, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useAppData } from "@/context/appDataContext";
import type { TodayPick } from "@/types/api";

export function TodayCard({ today }: { today: TodayPick }) {
  const { handleCopy } = useAppData();
  const c = today.case;

  return (
    <section className="overflow-hidden rounded-2xl border border-[var(--color-border)] bg-[var(--color-card)] shadow-card">
      <div className="grid gap-px bg-[var(--color-border)] md:grid-cols-[1.4fr_1fr]">
        <div className="bg-[var(--color-card)] p-6">
          <div className="inline-flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-[var(--color-primary)]">
            <Sparkles className="h-3.5 w-3.5" />
            今日のおすすめ
          </div>
          <h2 className="mt-2 text-xl font-bold leading-snug">{today.headline}</h2>
          <p className="mt-2 text-sm leading-relaxed text-[var(--color-muted-foreground)]">
            {c.what_worked}
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <Button
              size="sm"
              onClick={() => handleCopy(c.case_id, c.concrete_prompt)}
              disabled={!c.concrete_prompt}
            >
              <Copy className="h-3.5 w-3.5" />
              プロンプトをコピー
            </Button>
            <Link
              to={`/categories/${encodeURIComponent(c.business_type)}`}
              className="inline-flex h-8 items-center gap-2 rounded-md border border-[var(--color-border)] px-3 text-sm font-medium transition-colors hover:bg-[var(--color-accent)] hover:text-[var(--color-accent-foreground)]"
            >
              {c.business_type}
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>

        <div className="bg-[var(--color-primary-subtle)] p-6">
          {c.why_worked && (
            <>
              <div className="text-[10px] font-semibold uppercase tracking-wider text-[var(--color-accent-foreground)]">
                What worked
              </div>
              <p className="mt-1 text-sm leading-relaxed text-[var(--color-foreground)]">
                {c.why_worked}
              </p>
            </>
          )}
          {c.quantitative_effect && (
            <div className="mt-4 text-lg font-bold text-[var(--color-primary)]">
              {c.quantitative_effect}
            </div>
          )}
          <div className="mt-4 text-xs text-[var(--color-muted-foreground)]">
            — {c.owner_label}
          </div>
        </div>
      </div>
    </section>
  );
}
