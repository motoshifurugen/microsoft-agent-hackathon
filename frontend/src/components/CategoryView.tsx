import type { ReactNode } from "react";
import { ArrowLeft } from "lucide-react";
import type { CaseDetail } from "@/types/api";

interface CategoryViewProps {
  category: string;
  cases: CaseDetail[];
  renderCase: (c: CaseDetail) => ReactNode;
  onBack: () => void;
}

// カテゴリ選択後に遷移する事例一覧の専用画面。
// home の大きな事例リストをここへ切り出し、トップ画面の情報量を絞る。
export function CategoryView({ category, cases, renderCase, onBack }: CategoryViewProps) {
  return (
    <div className="flex flex-col gap-6">
      <button
        type="button"
        onClick={onBack}
        className="inline-flex w-fit items-center gap-1 text-sm text-[var(--color-muted-foreground)] transition-colors hover:text-[var(--color-foreground)]"
      >
        <ArrowLeft className="h-4 w-4" />
        ホームに戻る
      </button>

      <div>
        <h1 className="text-xl font-bold leading-tight">{category}</h1>
        <p className="mt-1 text-sm text-[var(--color-muted-foreground)]">
          {cases.length} 件の使いこなし事例
        </p>
      </div>

      <div className="grid gap-3">
        {cases.map(renderCase)}
        {cases.length === 0 && (
          <p className="rounded-lg border border-dashed border-[var(--color-border)] px-4 py-6 text-center text-sm text-[var(--color-muted-foreground)]">
            このカテゴリの事例はまだありません。最初の事例を共有してみませんか？
          </p>
        )}
      </div>
    </div>
  );
}
