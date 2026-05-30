// ホーム: 今日のおすすめ + Kodama からのフォローアップ + AIに相談（エージェント）。探す動線はエージェントに一本化した。
import { useCallback, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { AgentChat } from "@/components/AgentChat";
import { FollowUpCard } from "@/components/FollowUpCard";
import { TodayCard } from "@/components/TodayCard";
import { useAppData } from "@/context/appDataContext";

export function HomePage() {
  const { today, clientId } = useAppData();
  const [pendingMessage, setPendingMessage] = useState<string | null>(null);
  const clearPending = useCallback(() => setPendingMessage(null), []);

  return (
    <>
      <PageHeader title="ホーム" />
      <main className="mx-auto flex w-full max-w-7xl flex-1 flex-col gap-8 px-6 py-8">
        {today && <TodayCard today={today} />}
        <FollowUpCard onShare={setPendingMessage} />
        <AgentChat
          clientId={clientId}
          pendingMessage={pendingMessage}
          onPendingConsumed={clearPending}
        />
      </main>
    </>
  );
}
