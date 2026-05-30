// カテゴリ詳細: /categories/:name。当該カテゴリの事例を再現性スコア降順で表示する。
import { useMemo } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { CategoryView } from "@/components/CategoryView";
import { PageHeader } from "@/components/PageHeader";
import { useAppData } from "@/context/appDataContext";

export function CategoryDetailPage() {
  const { name } = useParams<{ name: string }>();
  const navigate = useNavigate();
  const { allCases, renderCase } = useAppData();
  const category = name ?? "";

  const cases = useMemo(
    () =>
      allCases
        .filter((c) => c.business_type === category)
        .sort((a, b) => b.reproducibility_score - a.reproducibility_score),
    [allCases, category],
  );

  return (
    <>
      <PageHeader title={category} subtitle="再現性の高い順に表示" />
      <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-8">
        <CategoryView
          category={category}
          cases={cases}
          renderCase={renderCase}
          onBack={() => navigate("/categories")}
        />
      </main>
    </>
  );
}
