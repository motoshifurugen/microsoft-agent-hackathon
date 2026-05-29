// 業務カテゴリごとの差し色定義。
// アイコン背景・選択時リング・CaseCard 左バー等で利用する。
// 8 色の中からカテゴリ名のハッシュで安定割当する（fallback 用）。

export interface CategoryPalette {
  bg: string;        // 淡背景 (アイコン背景)
  text: string;      // アイコン色
  ring: string;      // 選択時 ring
  bar: string;       // CaseCard 左アクセントバー
  tint: string;      // hover 時カードのほのかな tint
}

const PALETTE: Record<string, CategoryPalette> = {
  blue: {
    bg: "bg-blue-100 dark:bg-blue-500/15",
    text: "text-blue-600 dark:text-blue-300",
    ring: "ring-blue-400/40",
    bar: "bg-blue-500",
    tint: "from-blue-500/8 to-transparent",
  },
  emerald: {
    bg: "bg-emerald-100 dark:bg-emerald-500/15",
    text: "text-emerald-600 dark:text-emerald-300",
    ring: "ring-emerald-400/40",
    bar: "bg-emerald-500",
    tint: "from-emerald-500/8 to-transparent",
  },
  violet: {
    bg: "bg-violet-100 dark:bg-violet-500/15",
    text: "text-violet-600 dark:text-violet-300",
    ring: "ring-violet-400/40",
    bar: "bg-violet-500",
    tint: "from-violet-500/8 to-transparent",
  },
  orange: {
    bg: "bg-orange-100 dark:bg-orange-500/15",
    text: "text-orange-600 dark:text-orange-300",
    ring: "ring-orange-400/40",
    bar: "bg-orange-500",
    tint: "from-orange-500/8 to-transparent",
  },
  pink: {
    bg: "bg-pink-100 dark:bg-pink-500/15",
    text: "text-pink-600 dark:text-pink-300",
    ring: "ring-pink-400/40",
    bar: "bg-pink-500",
    tint: "from-pink-500/8 to-transparent",
  },
  teal: {
    bg: "bg-teal-100 dark:bg-teal-500/15",
    text: "text-teal-600 dark:text-teal-300",
    ring: "ring-teal-400/40",
    bar: "bg-teal-500",
    tint: "from-teal-500/8 to-transparent",
  },
  amber: {
    bg: "bg-amber-100 dark:bg-amber-500/15",
    text: "text-amber-600 dark:text-amber-300",
    ring: "ring-amber-400/40",
    bar: "bg-amber-500",
    tint: "from-amber-500/8 to-transparent",
  },
  indigo: {
    bg: "bg-indigo-100 dark:bg-indigo-500/15",
    text: "text-indigo-600 dark:text-indigo-300",
    ring: "ring-indigo-400/40",
    bar: "bg-indigo-500",
    tint: "from-indigo-500/8 to-transparent",
  },
};

const ORDER = ["blue", "emerald", "violet", "orange", "pink", "teal", "amber", "indigo"] as const;

// 既知カテゴリは固定割当。未知カテゴリはハッシュで割当（決定論的）。
const ASSIGNMENT: Record<string, (typeof ORDER)[number]> = {
  月次レポート作成: "blue",
  提案書作成: "violet",
  議事録要約: "emerald",
  コードレビュー: "indigo",
  問い合わせ対応: "pink",
  データ集計: "teal",
  メール作成: "amber",
  経費精算チェック: "orange",
};

function hashIndex(name: string): number {
  let h = 0;
  for (let i = 0; i < name.length; i++) {
    h = (h * 31 + name.charCodeAt(i)) >>> 0;
  }
  return h % ORDER.length;
}

export function getCategoryPalette(name: string): CategoryPalette {
  const key = ASSIGNMENT[name] ?? ORDER[hashIndex(name)];
  return PALETTE[key];
}
