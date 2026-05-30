// 各ページ共通のヘッダ。タイトル/サブタイトルと、右側に検索バー・テーマ切替を置く。
import type { ReactNode } from "react";
import { SearchBar } from "@/components/SearchBar";
import { ThemeToggle } from "@/components/ThemeToggle";
import { useAppData } from "@/context/appDataContext";

interface PageHeaderProps {
  title: string;
  subtitle?: ReactNode;
}

export function PageHeader({ title, subtitle }: PageHeaderProps) {
  const { copyFlash } = useAppData();

  return (
    <header className="sticky top-0 z-10 border-b border-[var(--color-border)] bg-[var(--color-card)]/95 backdrop-blur">
      <div className="flex items-center justify-between gap-4 px-6 py-3">
        <div className="min-w-0">
          <h1 className="truncate text-lg font-bold leading-tight">{title}</h1>
          {subtitle && (
            <p className="truncate text-xs text-[var(--color-muted-foreground)]">{subtitle}</p>
          )}
        </div>
        <div className="flex shrink-0 items-center gap-2">
          {copyFlash && (
            <span className="hidden text-xs text-[var(--color-primary)] sm:inline">{copyFlash}</span>
          )}
          <div className="hidden md:block">
            <SearchBar />
          </div>
          <ThemeToggle />
        </div>
      </div>
      <div className="border-t border-[var(--color-border)] px-6 py-2 md:hidden">
        <SearchBar />
      </div>
    </header>
  );
}
