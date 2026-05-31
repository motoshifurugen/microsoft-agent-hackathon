// 2 ペインのアプリシェル。左に固定 Sidebar、右に各ページ（<Outlet>）。
// 共有状態とデータ取得は AppDataProvider に集約する。
import { Outlet } from "react-router-dom";
import { Sidebar } from "@/components/Sidebar";
import { AppDataProvider } from "@/context/AppData";

export function AppLayout() {
  return (
    <AppDataProvider>
      <div className="flex min-h-screen bg-[var(--color-background)] text-[var(--color-foreground)]">
        <Sidebar />
        <div className="flex min-w-0 flex-1 flex-col">
          <Outlet />
        </div>
      </div>
    </AppDataProvider>
  );
}
