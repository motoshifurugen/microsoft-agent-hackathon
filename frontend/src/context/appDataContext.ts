// AppData の Context 定義と useAppData フック。
// Provider 本体（AppData.tsx）と分離することで、fast-refresh の component-only エクスポート制約を満たす。
import { createContext, useContext, type ReactNode } from "react";
import type { CaseDetail, CategorySummary, TodayPick } from "@/types/api";

export interface AppDataValue {
  clientId: string;
  today: TodayPick | null;
  categories: CategorySummary[];
  allCases: CaseDetail[];
  myCases: CaseDetail[];
  bookmarks: CaseDetail[];
  bookmarkedIds: Set<string>;
  triedByCase: Record<string, string>;
  copyFlash: string | null;
  toggleBookmark: (caseId: string) => Promise<void>;
  handleCopy: (caseId: string, text: string) => void;
  handleCaseCreated: (created: CaseDetail) => void;
  renderCase: (c: CaseDetail) => ReactNode;
}

export const AppDataContext = createContext<AppDataValue | null>(null);

export function useAppData(): AppDataValue {
  const ctx = useContext(AppDataContext);
  if (!ctx) {
    throw new Error("useAppData must be used within AppDataProvider");
  }
  return ctx;
}
