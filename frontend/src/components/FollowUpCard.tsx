// Kodama 側から能動的に働きかける「フォローアップカード」。
// localStorage の tried（コピー＝試した記録）から「以前試したがフォロー未」の事例を 1 件拾い、
// 「先日試した○○、どうでした?」と問いかける。うまくいった→共有で A1 の成功事例登録フローへ繋ぐ。
import { useMemo, useState } from "react";
import { MessageCircleHeart } from "lucide-react";
import { SectionLabel } from "@/components/SectionLabel";
import { Button } from "@/components/ui/button";
import { useAppData } from "@/context/appDataContext";
import { useLocalStorageJson } from "@/hooks/useLocalStorageJson";

const FOLLOWUP_KEY = "kodama-tried-followup";

// 共有メッセージは Orchestrator のパターン4（成功体験の検知→登録提案）を能動的に起動する。
function shareMessage(businessType: string): string {
  return `「${businessType}」を試してみたら、うまくいきました。この成功体験を社内の事例として登録したいです。`;
}

interface FollowUpCardProps {
  /** 共有を選んだとき、AgentChat に自動送信させるメッセージを渡す。 */
  onShare: (message: string) => void;
}

export function FollowUpCard({ onShare }: FollowUpCardProps) {
  const { triedByCase, allCases } = useAppData();
  const followup = useLocalStorageJson(FOLLOWUP_KEY);
  // マウント時刻より前に試した事例だけを対象にする（「次に来訪したとき」の自然な体験）。
  const [mountTime] = useState(() => Date.now());
  // 「あとで」はセッション限り（リロードで再表示）。永続化しない。
  const [snoozed, setSnoozed] = useState<Set<string>>(() => new Set());

  const candidate = useMemo(() => {
    const sorted = Object.entries(triedByCase)
      .filter(([cid, ts]) => {
        if (followup.value[cid]) return false; // 共有済み / イマイチ済み
        if (snoozed.has(cid)) return false; // 当セッションで「あとで」
        const triedAt = ts ? Date.parse(ts) : NaN;
        return Number.isFinite(triedAt) && triedAt < mountTime;
      })
      .sort(([, a], [, b]) => (b ?? "").localeCompare(a ?? ""));

    for (const [cid] of sorted) {
      const found = allCases.find((c) => c.case_id === cid);
      if (found) return found;
    }
    return null;
  }, [triedByCase, allCases, followup.value, snoozed, mountTime]);

  if (!candidate) return null;

  const handleShare = () => {
    followup.set(candidate.case_id, "shared");
    onShare(shareMessage(candidate.business_type));
  };

  const handleReject = () => followup.set(candidate.case_id, "dismissed");

  const handleSnooze = () =>
    setSnoozed((prev) => new Set(prev).add(candidate.case_id));

  return (
    <section className="flex flex-col gap-3 rounded-2xl border border-[var(--color-primary)]/30 bg-[var(--color-accent)] p-5 shadow-card">
      <SectionLabel icon={<MessageCircleHeart className="h-3.5 w-3.5" />}>
        Kodama からの確認
      </SectionLabel>
      <div>
        <p className="text-sm font-medium text-[var(--color-foreground)]">
          先日試した「{candidate.business_type}」、どうでしたか?
        </p>
        <p className="mt-1 text-xs text-[var(--color-muted-foreground)]">
          {candidate.owner_label}の事例 ・{candidate.quantitative_effect || "効果未登録"}
        </p>
      </div>
      <div className="flex flex-wrap gap-2">
        <Button size="sm" onClick={handleShare}>
          うまくいった → 共有する
        </Button>
        <Button size="sm" variant="outline" onClick={handleReject}>
          イマイチだった
        </Button>
        <Button size="sm" variant="ghost" onClick={handleSnooze}>
          あとで
        </Button>
      </div>
    </section>
  );
}
