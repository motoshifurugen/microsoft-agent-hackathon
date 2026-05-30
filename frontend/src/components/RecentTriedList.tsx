// localStorage の「最近試した」記録をコンパクトな行リストで表示する。
// tried は caseId → ISO8601 文字列。新しい順に並べ、読み込み済み事例と突き合わせる。
import { useMemo } from "react";
import { useAppData } from "@/context/appDataContext";

export function RecentTriedList() {
  const { triedByCase, allCases } = useAppData();

  const items = useMemo(
    () =>
      Object.entries(triedByCase)
        .sort(([, a], [, b]) => (b ?? "").localeCompare(a ?? ""))
        .map(([cid]) => allCases.find((c) => c.case_id === cid))
        .filter((c): c is NonNullable<typeof c> => Boolean(c)),
    [triedByCase, allCases],
  );

  if (items.length === 0) {
    return (
      <p className="rounded-lg border border-dashed border-[var(--color-border)] px-4 py-10 text-center text-sm text-[var(--color-muted-foreground)]">
        まだ試した事例はありません。気になる事例のプロンプトをコピーすると、ここに記録されます。
      </p>
    );
  }

  return (
    <ul className="grid gap-2 text-sm">
      {items.map((c) => (
        <li
          key={c.case_id}
          className="rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] px-3 py-2"
        >
          <div className="font-medium">{c.owner_label}の事例</div>
          <div className="text-xs text-[var(--color-muted-foreground)]">
            {c.business_type}・{c.quantitative_effect || "効果未登録"}
          </div>
        </li>
      ))}
    </ul>
  );
}
