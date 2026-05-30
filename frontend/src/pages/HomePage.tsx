// ホーム: 今日のおすすめ + AIに相談（エージェント）。探す動線はエージェントに一本化した。
import { PageHeader } from "@/components/PageHeader";
import { AgentChat } from "@/components/AgentChat";
import { TodayCard } from "@/components/TodayCard";
import { useAppData } from "@/context/appDataContext";

export function HomePage() {
  const { today, clientId } = useAppData();

  return (
    <>
      <PageHeader title="ホーム" />
      <main className="mx-auto flex w-full max-w-7xl flex-1 flex-col gap-8 px-6 py-8">
        {today && <TodayCard today={today} />}
        <AgentChat clientId={clientId} />
      </main>
    </>
  );
}
