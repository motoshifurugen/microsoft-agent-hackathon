// 困りごと掲示板: 質問の閲覧・投稿・回答。Q&A ロジックは BoardSection に集約済み。
import { useMemo } from "react";
import { BoardSection } from "@/components/BoardSection";
import { PageHeader } from "@/components/PageHeader";
import { useAppData } from "@/context/appDataContext";

export function BoardPage() {
  const { categories } = useAppData();
  const categoryNames = useMemo(() => categories.map((c) => c.name), [categories]);

  return (
    <>
      <PageHeader title="困りごと掲示板" subtitle="業務の困りごとを投稿し、社内の知恵を集める" />
      <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-8">
        <BoardSection categories={categoryNames} />
      </main>
    </>
  );
}
