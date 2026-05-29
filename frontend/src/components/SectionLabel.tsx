// セクション見出しラベル (uppercase 小文字)。
// 複数セクションで使い回す共通コンポーネント。
import type { ReactNode } from "react";

interface SectionLabelProps {
  icon?: ReactNode;
  children: ReactNode;
}

export function SectionLabel({ icon, children }: SectionLabelProps) {
  return (
    <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-[var(--color-muted-foreground)]">
      {icon}
      {children}
    </div>
  );
}
