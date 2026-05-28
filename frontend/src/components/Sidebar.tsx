// 左サイドバー: 「自分の活用」と「メンバー支援」の 2 セクション。
// 現在のビュー (View) を切替えるシンプルな state ベースナビ。
import { Compass, Home, Layers, ListChecks, UserCog, Users } from "lucide-react";
import type { ViewKey } from "@/types/view";
import { cn } from "@/lib/utils";

interface SidebarProps {
  view: ViewKey;
  onChange: (view: ViewKey) => void;
}

const employeeItems: { key: ViewKey; label: string; icon: React.ReactNode }[] = [
  { key: "employee-home", label: "Home", icon: <Home className="h-4 w-4" /> },
  { key: "employee-categories", label: "業務カテゴリ", icon: <Layers className="h-4 w-4" /> },
];

const adminItems: { key: ViewKey; label: string; icon: React.ReactNode }[] = [
  { key: "admin-members", label: "メンバー支援", icon: <Users className="h-4 w-4" /> },
  { key: "admin-history", label: "履歴", icon: <ListChecks className="h-4 w-4" /> },
];

export function Sidebar({ view, onChange }: SidebarProps) {
  return (
    <aside className="w-60 shrink-0 border-r border-[var(--color-border)] bg-[var(--color-card)] p-4 flex flex-col gap-6">
      <div className="flex items-center gap-2 px-2 pt-1">
        <Compass className="h-5 w-5 text-[var(--color-primary)]" />
        <div>
          <div className="text-lg font-semibold leading-tight">Kodama</div>
          <div className="text-[11px] text-[var(--color-muted-foreground)] leading-tight">
            小さな成功を、次の誰かへ
          </div>
        </div>
      </div>

      <Section label="自分の活用" icon={<Compass className="h-3.5 w-3.5" />}>
        {employeeItems.map((item) => (
          <NavItem
            key={item.key}
            active={view === item.key}
            onClick={() => onChange(item.key)}
            icon={item.icon}
            label={item.label}
          />
        ))}
      </Section>

      <Section label="メンバー支援" icon={<UserCog className="h-3.5 w-3.5" />}>
        {adminItems.map((item) => (
          <NavItem
            key={item.key}
            active={view === item.key}
            onClick={() => onChange(item.key)}
            icon={item.icon}
            label={item.label}
          />
        ))}
      </Section>
    </aside>
  );
}

function Section({
  label,
  icon,
  children,
}: {
  label: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center gap-1.5 px-2 text-[10px] font-semibold uppercase tracking-wider text-[var(--color-muted-foreground)]">
        {icon}
        {label}
      </div>
      <div className="flex flex-col gap-0.5">{children}</div>
    </div>
  );
}

function NavItem({
  active,
  onClick,
  icon,
  label,
}: {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "flex w-full items-center gap-2 rounded-md px-2.5 py-1.5 text-sm transition-colors",
        active
          ? "bg-[var(--color-primary)] text-[var(--color-primary-foreground)]"
          : "text-[var(--color-foreground)] hover:bg-[var(--color-accent)]",
      )}
    >
      {icon}
      <span className="text-left">{label}</span>
    </button>
  );
}
