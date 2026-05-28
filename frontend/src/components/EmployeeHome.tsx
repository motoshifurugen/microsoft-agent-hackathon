import { useEffect, useState } from "react";
import { ArrowRight, Sparkles, Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchCategories, fetchToday } from "@/lib/api";
import type { CategorySummary, TodayPick } from "@/types/api";

interface EmployeeHomeProps {
  onSelectCategory: (name: string) => void;
}

export function EmployeeHome({ onSelectCategory }: EmployeeHomeProps) {
  const [today, setToday] = useState<TodayPick | null>(null);
  const [categories, setCategories] = useState<CategorySummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([fetchToday(), fetchCategories()])
      .then(([t, c]) => {
        setToday(t);
        setCategories(c);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : String(err));
      });
  }, []);

  if (error) {
    return (
      <div className="rounded-md border border-[var(--color-destructive)] bg-[var(--color-destructive)]/10 p-4 text-sm">
        読み込みに失敗しました: {error}
      </div>
    );
  }

  if (!today) {
    return (
      <div className="flex items-center gap-2 text-sm text-[var(--color-muted-foreground)]">
        <Loader2 className="h-4 w-4 animate-spin" />
        読み込み中…
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      <section>
        <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[var(--color-muted-foreground)]">
          <Sparkles className="h-3.5 w-3.5" />
          今日のおすすめ
        </div>
        <Card>
          <CardHeader>
            <CardTitle className="text-2xl">{today.headline}</CardTitle>
            <div className="flex flex-wrap gap-2 pt-1">
              <Badge variant="secondary">{today.case.business_type}</Badge>
              {today.case.quantitative_effect && (
                <Badge>{today.case.quantitative_effect}</Badge>
              )}
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm leading-relaxed">{today.case.what_worked}</p>
          </CardContent>
        </Card>
      </section>

      <section>
        <div className="mb-3 flex items-center justify-between">
          <div className="text-xs font-semibold uppercase tracking-wider text-[var(--color-muted-foreground)]">
            業務カテゴリから探す
          </div>
          <div className="text-xs text-[var(--color-muted-foreground)]">
            {categories.length} カテゴリ
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          {categories.map((category) => (
            <Button
              key={category.name}
              variant="outline"
              size="sm"
              onClick={() => onSelectCategory(category.name)}
            >
              {category.name}
              <Badge variant="muted" className="ml-1">
                {category.case_count}
              </Badge>
              <ArrowRight className="h-3 w-3 opacity-60" />
            </Button>
          ))}
        </div>
      </section>
    </div>
  );
}
