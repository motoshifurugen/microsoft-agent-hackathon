import { useState } from "react";
import { MessageCircleQuestion } from "lucide-react";
import { Button } from "@/components/ui/button";
import { matchPain } from "@/lib/api";
import type { CaseDetail } from "@/types/api";

interface PainInputProps {
  clientId: string;
  onResult: (query: string, cases: CaseDetail[]) => void;
}

// ユーザーが自分の困りごとを自由入力し、類似事例を引き出す入力欄。
// メール監視を廃止した代わりの、明示的な困りごと収集経路。
export function PainInput({ clientId, onResult }: PainInputProps) {
  const [text, setText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const trimmed = text.trim();
  const canSubmit = trimmed.length > 0 && !submitting;

  const handleSubmit = async () => {
    if (!canSubmit) return;
    setSubmitting(true);
    setError(null);
    try {
      const res = await matchPain({ text: trimmed, client_id: clientId });
      onResult(res.query, res.cases);
    } catch {
      setError("マッチングに失敗しました。時間をおいて再度お試しください。");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-4 shadow-sm">
      <div className="flex items-center gap-1.5 text-sm font-semibold">
        <MessageCircleQuestion className="h-4 w-4 text-[var(--color-primary)]" />
        いま困っていることは？
      </div>
      <p className="mt-1 text-xs text-[var(--color-muted-foreground)]">
        業務の困りごとを書くと、社内の似た成功事例を探します。
      </p>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={3}
        placeholder="例: 毎月の月次レポート作成に時間がかかって困っている"
        className="mt-3 w-full resize-y rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-2 text-sm outline-none transition-colors focus:border-[var(--color-primary)] focus:ring-2 focus:ring-[var(--color-primary)]/20"
      />
      {error && <p className="mt-2 text-xs text-[var(--color-destructive)]">{error}</p>}
      <div className="mt-3 flex justify-end">
        <Button size="sm" onClick={() => void handleSubmit()} disabled={!canSubmit}>
          {submitting ? "探しています…" : "似た事例を探す"}
        </Button>
      </div>
    </section>
  );
}
