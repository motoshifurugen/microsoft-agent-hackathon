// 業務カテゴリのグリッド表示。
// 「あなたの業務、どこで使える？」セクションのメインビジュアル。
import {
  BarChart3,
  Code2,
  FileSpreadsheet,
  FileText,
  HelpCircle,
  Mail,
  MessagesSquare,
  Receipt,
  Sparkles,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import type { CategorySummary } from "@/types/api";

// カテゴリ名 → アイコンのマッピング。
// データ層の business_type の正規化はしていないため、ここで吸収する。
const CATEGORY_ICONS: Record<string, LucideIcon> = {
  月次レポート作成: FileSpreadsheet,
  提案書作成: FileText,
  議事録要約: MessagesSquare,
  コードレビュー: Code2,
  問い合わせ対応: HelpCircle,
  データ集計: BarChart3,
  メール作成: Mail,
  経費精算チェック: Receipt,
};

interface CategoryGridProps {
  categories: CategorySummary[];
  selected: string | null;
  onSelect: (name: string) => void;
}

export function CategoryGrid({ categories, selected, onSelect }: CategoryGridProps) {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {categories.map((c) => {
        const Icon = CATEGORY_ICONS[c.name] ?? Sparkles;
        const isSelected = selected === c.name;
        return (
          <button
            key={c.name}
            type="button"
            onClick={() => onSelect(c.name)}
            className={cn(
              "group flex items-center gap-3 rounded-xl border bg-[var(--color-card)] p-4 text-left shadow-sm transition-all",
              "hover:-translate-y-0.5 hover:shadow-md",
              isSelected
                ? "border-[var(--color-primary)] ring-2 ring-[var(--color-primary)]/30"
                : "border-[var(--color-border)]",
            )}
          >
            <span
              className={cn(
                "flex h-12 w-12 shrink-0 items-center justify-center rounded-full transition-colors",
                isSelected
                  ? "bg-[var(--color-primary)] text-[var(--color-primary-foreground)]"
                  : "bg-[var(--color-primary)]/10 text-[var(--color-primary)]",
              )}
            >
              <Icon className="h-5 w-5" />
            </span>
            <div className="min-w-0 flex-1">
              <div className="text-sm font-semibold leading-tight">{c.name}</div>
              <div className="mt-0.5 text-[11px] text-[var(--color-muted-foreground)]">
                {c.case_count} 件の使いこなし事例
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
}
