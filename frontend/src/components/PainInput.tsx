import { useState } from "react";
import { ArrowRight, MessageCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { matchPain } from "@/lib/api";
import type { CaseDetail } from "@/types/api";

interface PainInputProps {
  clientId: string;
  onResult: (query: string, cases: CaseDetail[]) => void;
}

const MAX_LEN = 200;
const FAQ_CHIPS = ["議事録要約", "提案書", "集計"];

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
    <section className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-card)] p-5 shadow-card">
      <div className="flex items-center gap-3">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[var(--color-primary-subtle)] text-[var(--color-primary)]">
          <MessageCircle className="h-5 w-5" />
        </span>
        <div>
          <div className="text-[15px] font-semibold leading-tight">いま困っていることは？</div>
          <p className="text-xs text-[var(--color-muted-foreground)]">
            書くと、似た成功事例を探します
          </p>
        </div>
      </div>

      <textarea
        value={text}
        onChange={(e) => setText(e.target.value.slice(0, MAX_LEN))}
        rows={3}
        maxLength={MAX_LEN}
        placeholder="例: 毎月の月次レポート作成に時間がかかって困っている…"
        className="mt-3 w-full resize-y rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-2 text-sm outline-none transition-colors focus:border-[var(--color-primary)] focus:ring-2 focus:ring-[var(--color-primary)]/20"
      />
      <div className="mt-1 text-right font-mono text-[10px] text-[var(--color-muted-foreground)]">
        {text.length} / {MAX_LEN}
      </div>

      <div className="mt-2 flex flex-wrap items-center gap-2">
        <span className="text-[11px] text-[var(--color-muted-foreground)]">よくある質問:</span>
        {FAQ_CHIPS.map((chip) => (
          <button
            key={chip}
            type="button"
            onClick={() => setText(chip)}
            className="rounded-full bg-[var(--color-muted)] px-3 py-1 text-xs text-[var(--color-secondary-foreground)] transition-colors hover:bg-[var(--color-accent)] hover:text-[var(--color-accent-foreground)]"
          >
            {chip}
          </button>
        ))}
      </div>

      {error && <p className="mt-2 text-xs text-[var(--color-destructive)]">{error}</p>}

      <div className="mt-3 flex justify-end">
        <Button size="sm" onClick={() => void handleSubmit()} disabled={!canSubmit}>
          {submitting ? "探しています…" : "似た事例を探す"}
          <ArrowRight className="h-3.5 w-3.5" />
        </Button>
      </div>
    </section>
  );
}
