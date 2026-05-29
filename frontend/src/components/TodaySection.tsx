import { Sparkles } from "lucide-react";
import { SectionLabel } from "@/components/SectionLabel";
import type { TodayPick } from "@/types/api";

export function TodaySection({ today }: { today: TodayPick }) {
  return (
    <section>
      <SectionLabel icon={<Sparkles className="h-3.5 w-3.5" />}>今日のおすすめ</SectionLabel>
      <div className="mt-2 rounded-2xl border border-[var(--color-border)] bg-[var(--color-card)] p-5 shadow-sm">
        <p className="text-lg font-semibold leading-snug">{today.headline}</p>
        <p className="mt-2 text-sm leading-relaxed text-[var(--color-muted-foreground)]">
          {today.case.what_worked}
        </p>
      </div>
    </section>
  );
}
