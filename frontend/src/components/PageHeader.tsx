// 各ページ共通のヘッダ。タイトルと、右側にテーマ切替を置く。
import { ThemeToggle } from "@/components/ThemeToggle";
import { useAppData } from "@/context/appDataContext";

interface PageHeaderProps {
  title: string;
}

export function PageHeader({ title }: PageHeaderProps) {
  const { copyFlash } = useAppData();

  return (
    <header className="sticky top-0 z-10 border-b border-[var(--color-border)] bg-[var(--color-card)]/95 backdrop-blur">
      <div className="flex items-center justify-between gap-4 px-6 py-3">
        <div className="min-w-0">
          <h1 className="truncate text-lg font-bold leading-tight">{title}</h1>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          {copyFlash && (
            <span className="hidden text-xs text-[var(--color-primary)] sm:inline">{copyFlash}</span>
          )}
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
