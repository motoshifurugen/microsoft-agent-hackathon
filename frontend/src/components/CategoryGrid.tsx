// 業務カテゴリのグリッド表示。
// アイコン・説明文はデザイン由来の静的マッピング（装飾コピー）、件数は API の実数。
import {
  ArrowRight,
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
// データ層の business_type は正規化していないため、ここで吸収する。
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

// カテゴリ名 → 装飾コピー（design.pen 由来）。未知カテゴリはフォールバックを使う。
const CATEGORY_DESC: Record<string, string> = {
  月次レポート作成: "前週ログから下書きを自動生成",
  提案書作成: "見出し構成と要約をテンプレ化",
  議事録要約: "3節構造で時間 1/4",
  コードレビュー: "観点別の懸念リスト出力",
  問い合わせ対応: "一次返信の半自動化",
  データ集計: "CSV からの自動集計",
  メール作成: "返信テンプレートで省力化",
  経費精算チェック: "領収書 OCR からチェック表へ",
};

const DESC_FALLBACK = "AI 活用の事例を見る";

interface CategoryGridProps {
  categories: CategorySummary[];
  selected: string | null;
  onSelect: (name: string) => void;
}

export function CategoryGrid({ categories, selected, onSelect }: CategoryGridProps) {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {categories.map((c) => {
        const Icon = CATEGORY_ICONS[c.name] ?? Sparkles;
        const desc = CATEGORY_DESC[c.name] ?? DESC_FALLBACK;
        const isSelected = selected === c.name;
        return (
          <button
            key={c.name}
            type="button"
            onClick={() => onSelect(c.name)}
            className={cn(
              "group flex flex-col rounded-xl border bg-[var(--color-card)] p-4 text-left shadow-card transition-all",
              "hover:-translate-y-0.5 hover:shadow-cta",
              isSelected
                ? "border-[var(--color-primary)] ring-2 ring-[var(--color-primary)]/30"
                : "border-[var(--color-border)]",
            )}
          >
            <div className="flex items-center justify-between gap-2">
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[var(--color-primary-subtle)] text-[var(--color-primary)]">
                <Icon className="h-5 w-5" />
              </span>
              <span className="rounded-full bg-[var(--color-muted)] px-2 py-0.5 text-[11px] font-medium text-[var(--color-secondary-foreground)]">
                {c.case_count} 件
              </span>
            </div>
            <div className="mt-3 text-sm font-semibold leading-tight">{c.name}</div>
            <p className="mt-1 line-clamp-2 text-[11px] leading-relaxed text-[var(--color-muted-foreground)]">
              {desc}
            </p>
            <span className="mt-3 inline-flex items-center gap-1 text-[11px] font-medium text-[var(--color-primary)]">
              事例を見る
              <ArrowRight className="h-3 w-3 transition-transform group-hover:translate-x-0.5" />
            </span>
          </button>
        );
      })}
    </div>
  );
}
