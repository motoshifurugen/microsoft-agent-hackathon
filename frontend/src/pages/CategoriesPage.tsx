// カテゴリ一覧: グループ絞り込みチップ + 事例の多い順ソート + カードグリッド。
// グループ分けは静的なフロントマッピング、件数は API の実数。
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { CategoryGrid } from "@/components/CategoryGrid";
import { PageHeader } from "@/components/PageHeader";
import { useAppData } from "@/context/appDataContext";
import { cn } from "@/lib/utils";

const GROUPS = ["すべて", "バックオフィス", "開発・技術", "コミュニケーション"] as const;
type Group = (typeof GROUPS)[number];

const CATEGORY_GROUP: Record<string, Exclude<Group, "すべて">> = {
  月次レポート作成: "バックオフィス",
  データ集計: "バックオフィス",
  アンケート集計: "バックオフィス",
  経費精算: "バックオフィス",
  コードレビュー: "開発・技術",
  議事録要約: "コミュニケーション",
  メール作成: "コミュニケーション",
  問い合わせ対応: "コミュニケーション",
  提案書作成: "コミュニケーション",
};

export function CategoriesPage() {
  const { categories } = useAppData();
  const navigate = useNavigate();
  const [group, setGroup] = useState<Group>("すべて");

  const visible = useMemo(() => {
    const filtered =
      group === "すべて"
        ? categories
        : categories.filter((c) => CATEGORY_GROUP[c.name] === group);
    return [...filtered].sort((a, b) => b.case_count - a.case_count);
  }, [categories, group]);

  return (
    <>
      <PageHeader title="カテゴリで探す" />
      <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-5 px-6 py-8">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap gap-2">
            {GROUPS.map((g) => (
              <button
                key={g}
                type="button"
                onClick={() => setGroup(g)}
                className={cn(
                  "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
                  group === g
                    ? "border-[var(--color-primary)] bg-[var(--color-primary-subtle)] text-[var(--color-primary)]"
                    : "border-[var(--color-border)] text-[var(--color-muted-foreground)] hover:bg-[var(--color-muted)]",
                )}
              >
                {g}
              </button>
            ))}
          </div>
          <span className="text-xs text-[var(--color-muted-foreground)]">並べ替え: 事例の多い順</span>
        </div>

        {visible.length > 0 ? (
          <CategoryGrid
            categories={visible}
            selected={null}
            onSelect={(name) => navigate(`/categories/${encodeURIComponent(name)}`)}
          />
        ) : (
          <p className="rounded-lg border border-dashed border-[var(--color-border)] px-4 py-10 text-center text-sm text-[var(--color-muted-foreground)]">
            {categories.length === 0 ? "カテゴリを読み込み中…" : "該当するカテゴリがありません"}
          </p>
        )}
      </main>
    </>
  );
}
