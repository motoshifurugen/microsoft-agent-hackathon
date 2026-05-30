// 保存したスキル: タブで「保存した事例（サーバー永続）」と「最近試した（localStorage）」を切り替える。
import { useMemo, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { RecentTriedList } from "@/components/RecentTriedList";
import { Tabs } from "@/components/Tabs";
import { useAppData } from "@/context/appDataContext";

export function BookmarksPage() {
  const { bookmarks, triedByCase, renderCase } = useAppData();
  const [tab, setTab] = useState<"saved" | "tried">("saved");

  const triedCount = useMemo(() => Object.keys(triedByCase).length, [triedByCase]);

  return (
    <>
      <PageHeader title="保存したスキル" />
      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-5 px-6 py-8">
        <Tabs
          items={[
            { id: "saved", label: "保存した", count: bookmarks.length },
            { id: "tried", label: "最近試した", count: triedCount },
          ]}
          active={tab}
          onChange={(id) => setTab(id as "saved" | "tried")}
        />

        {tab === "saved" ? (
          bookmarks.length > 0 ? (
            <div className="grid gap-3">{bookmarks.map(renderCase)}</div>
          ) : (
            <p className="rounded-lg border border-dashed border-[var(--color-border)] px-4 py-10 text-center text-sm text-[var(--color-muted-foreground)]">
              保存した事例はまだありません。事例カードの保存ボタンで、後で見返せます。
            </p>
          )
        ) : (
          <RecentTriedList />
        )}
      </main>
    </>
  );
}
