import { useEffect, useState } from "react";
import { ArrowLeft, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { CaseCard } from "@/components/CaseCard";
import { fetchCasesInCategory } from "@/lib/api";
import type { CategoryCasesResponse } from "@/types/api";

interface CategoryViewProps {
  category: string;
  onBack: () => void;
  onCopy: (text: string) => void;
}

export function CategoryView({ category, onBack, onCopy }: CategoryViewProps) {
  const [data, setData] = useState<CategoryCasesResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // カテゴリ変更時にデータをリセットして再取得する。
  useEffect(() => {
    setData(null);
    setError(null);
    fetchCasesInCategory(category)
      .then(setData)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : String(err)));
  }, [category]);

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="sm" onClick={onBack}>
          <ArrowLeft className="h-4 w-4" />
          戻る
        </Button>
        <h2 className="text-xl font-semibold">{category}</h2>
        {data && (
          <span className="text-xs text-[var(--color-muted-foreground)]">
            ({data.cases.length} 件)
          </span>
        )}
      </div>

      {error && (
        <div className="rounded-md border border-[var(--color-destructive)] bg-[var(--color-destructive)]/10 p-4 text-sm">
          {error}
        </div>
      )}

      {!data && !error && (
        <div className="flex items-center gap-2 text-sm text-[var(--color-muted-foreground)]">
          <Loader2 className="h-4 w-4 animate-spin" />
          読み込み中…
        </div>
      )}

      {data && (
        <div className="grid gap-4">
          {data.cases.map((c) => (
            <CaseCard
              key={c.case_id}
              caseDetail={c}
              onCopy={() => onCopy(c.concrete_prompt)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
