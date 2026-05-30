// ヘッダの検索入力。Cmd/Ctrl+K でフォーカスし、読み込み済み事例へのクライアントサイド検索を駆動する。
// 検索結果は HomePage に表示するため、ホーム以外で入力されたらホームへ遷移する。
import { useEffect, useRef } from "react";
import { Search } from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAppData } from "@/context/appDataContext";

export function SearchBar() {
  const { searchQuery, setSearchQuery } = useAppData();
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  const handleChange = (value: string) => {
    setSearchQuery(value);
    if (value.trim() && location.pathname !== "/") {
      navigate("/");
    }
  };

  return (
    <div className="relative w-full max-w-md">
      <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-muted-foreground)]" />
      <input
        ref={inputRef}
        type="search"
        value={searchQuery}
        onChange={(e) => handleChange(e.target.value)}
        placeholder="事例を検索（業務・効果・プロンプトなど）"
        className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] py-2 pl-9 pr-12 text-sm shadow-sm outline-none transition-colors focus:border-[var(--color-primary)] focus:ring-2 focus:ring-[var(--color-primary)]/20"
      />
      <kbd className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 rounded border border-[var(--color-border)] bg-[var(--color-muted)] px-1.5 py-0.5 text-[10px] font-medium text-[var(--color-muted-foreground)]">
        ⌘K
      </kbd>
    </div>
  );
}
