// 240px 固定サイドバー。ブランド / ナビゲーション / ユーザープロフィール / バージョン。
// プロフィールは認証が無いため、自分が登録した事例の最新 owner_label（例「営業部 佐藤さん」）から
// 部署と氏名を導出して表示する。事例ゼロなら「ゲスト」。
import { Bookmark, Compass, House, MessageSquare, Sparkles } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { NavLink } from "react-router-dom";
import { useAppData } from "@/context/appDataContext";
import { cn } from "@/lib/utils";

interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
}

const NAV_ITEMS: NavItem[] = [
  { to: "/", label: "ホーム", icon: House },
  { to: "/categories", label: "カテゴリで探す", icon: Compass },
  { to: "/bookmarks", label: "保存したスキル", icon: Bookmark },
  { to: "/board", label: "困りごと掲示板", icon: MessageSquare },
  { to: "/share", label: "事例を共有", icon: Sparkles },
];

interface Profile {
  dept: string;
  name: string;
  initial: string;
}

function deriveProfile(ownerLabel: string | undefined): Profile {
  const label = ownerLabel?.trim();
  if (!label) return { dept: "未所属", name: "ゲスト", initial: "G" };
  const parts = label.split(/\s+/).filter(Boolean);
  const [dept, name] = parts.length >= 2 ? [parts[0], parts.slice(1).join(" ")] : ["", parts[0]];
  return { dept, name, initial: name.slice(0, 1) || "G" };
}

export function Sidebar() {
  const { myCases } = useAppData();
  const profile = deriveProfile(myCases[0]?.owner_label);

  return (
    <aside className="sticky top-0 flex h-screen w-60 shrink-0 flex-col border-r border-[var(--color-border)] bg-[var(--color-card)]">
      <NavLink to="/" className="flex items-center gap-2 px-5 py-4">
        <Compass className="h-6 w-6 text-[var(--color-primary)]" />
        <div className="text-base font-bold leading-tight">Kodama</div>
      </NavLink>

      <nav className="flex flex-1 flex-col gap-1 px-3 py-2">
        {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-[var(--color-primary-subtle)] text-[var(--color-primary)]"
                  : "text-[var(--color-muted-foreground)] hover:bg-[var(--color-muted)] hover:text-[var(--color-foreground)]",
              )
            }
          >
            <Icon className="h-4 w-4 shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-[var(--color-border)] px-4 py-3">
        <div className="flex items-center gap-3">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[var(--color-primary)] text-sm font-semibold text-[var(--color-primary-foreground)]">
            {profile.initial}
          </span>
          <div className="min-w-0 leading-tight">
            <div className="truncate text-sm font-semibold">{profile.name}</div>
            <div className="truncate text-[11px] text-[var(--color-muted-foreground)]">
              {profile.dept || "未所属"}
            </div>
          </div>
        </div>
        <div className="mt-3 text-[10px] text-[var(--color-muted-foreground)]">v1.0.0 · 2026</div>
      </div>
    </aside>
  );
}
