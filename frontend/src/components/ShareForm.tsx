import { useState } from "react";
import { Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { createCase } from "@/lib/api";
import type { CaseDetail } from "@/types/api";

interface ShareFormProps {
  clientId: string;
  onCreated: (created: CaseDetail) => void;
}

const inputClass =
  "mt-1 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-2 text-sm outline-none transition-colors focus:border-[var(--color-primary)] focus:ring-2 focus:ring-[var(--color-primary)]/20";

// ユーザーが自分の成功事例をその場で登録するフォーム。
// 必須: owner_label / business_type / what_worked。残りは任意。
export function ShareForm({ clientId, onCreated }: ShareFormProps) {
  const [open, setOpen] = useState(false);
  const [ownerLabel, setOwnerLabel] = useState("");
  const [businessType, setBusinessType] = useState("");
  const [whatWorked, setWhatWorked] = useState("");
  const [whyWorked, setWhyWorked] = useState("");
  const [concretePrompt, setConcretePrompt] = useState("");
  const [quantitativeEffect, setQuantitativeEffect] = useState("");
  const [reproducibility, setReproducibility] = useState(0.5);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  const canSubmit =
    ownerLabel.trim().length > 0 &&
    businessType.trim().length > 0 &&
    whatWorked.trim().length > 0 &&
    !submitting;

  const reset = () => {
    setOwnerLabel("");
    setBusinessType("");
    setWhatWorked("");
    setWhyWorked("");
    setConcretePrompt("");
    setQuantitativeEffect("");
    setReproducibility(0.5);
  };

  const handleSubmit = async () => {
    if (!canSubmit) return;
    setSubmitting(true);
    setError(null);
    try {
      const created = await createCase({
        client_id: clientId,
        owner_label: ownerLabel.trim(),
        business_type: businessType.trim(),
        what_worked: whatWorked.trim(),
        why_worked: whyWorked.trim(),
        concrete_prompt: concretePrompt.trim(),
        quantitative_effect: quantitativeEffect.trim(),
        reproducibility_score: reproducibility,
      });
      onCreated(created);
      reset();
      setDone(true);
      setOpen(false);
      setTimeout(() => setDone(false), 3000);
    } catch {
      setError("登録に失敗しました。時間をおいて再度お試しください。");
    } finally {
      setSubmitting(false);
    }
  };

  if (!open) {
    return (
      <section className="rounded-xl border border-dashed border-[var(--color-border)] bg-[var(--color-muted)] p-5 text-center">
        <p className="text-sm">
          {done
            ? "成功事例を登録しました。次の誰かの力になります。"
            : "あなたの成功事例を、次の誰かに届けませんか？"}
        </p>
        <Button className="mt-3" onClick={() => setOpen(true)}>
          <Sparkles className="h-3.5 w-3.5" />
          自分の成功を共有する
        </Button>
      </section>
    );
  }

  return (
    <section className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-5 shadow-sm">
      <div className="flex items-center gap-1.5 text-sm font-semibold">
        <Sparkles className="h-4 w-4 text-[var(--color-primary)]" />
        成功事例を共有する
      </div>
      <p className="mt-1 text-xs text-[var(--color-muted-foreground)]">
        登録した事例はカテゴリ一覧や検索の対象になり、社内で再利用されます。
      </p>

      <div className="mt-4 grid gap-3">
        <label className="block text-xs font-medium">
          表示名 <span className="text-[var(--color-destructive)]">*</span>
          <input
            value={ownerLabel}
            onChange={(e) => setOwnerLabel(e.target.value)}
            placeholder="例: 営業部 サンプルさん"
            className={inputClass}
          />
        </label>

        <label className="block text-xs font-medium">
          業務カテゴリ <span className="text-[var(--color-destructive)]">*</span>
          <input
            value={businessType}
            onChange={(e) => setBusinessType(e.target.value)}
            placeholder="例: 週次報告作成"
            className={inputClass}
          />
        </label>

        <label className="block text-xs font-medium">
          うまくいったこと <span className="text-[var(--color-destructive)]">*</span>
          <textarea
            value={whatWorked}
            onChange={(e) => setWhatWorked(e.target.value)}
            rows={2}
            placeholder="例: Copilot で前週ログから下書きを生成した"
            className={`${inputClass} resize-y`}
          />
        </label>

        <label className="block text-xs font-medium">
          なぜ効いたか（任意）
          <textarea
            value={whyWorked}
            onChange={(e) => setWhyWorked(e.target.value)}
            rows={2}
            placeholder="例: 定型作業のテンプレ化が効いた"
            className={`${inputClass} resize-y`}
          />
        </label>

        <label className="block text-xs font-medium">
          使ったプロンプト（任意）
          <textarea
            value={concretePrompt}
            onChange={(e) => setConcretePrompt(e.target.value)}
            rows={2}
            placeholder="例: 以下のログを週次報告の体裁にまとめて: ..."
            className={`${inputClass} resize-y`}
          />
        </label>

        <label className="block text-xs font-medium">
          定量効果（任意）
          <input
            value={quantitativeEffect}
            onChange={(e) => setQuantitativeEffect(e.target.value)}
            placeholder="例: 週 2h → 30min"
            className={inputClass}
          />
        </label>

        <label className="block text-xs font-medium">
          再現性: {reproducibility.toFixed(1)}
          <input
            type="range"
            min={0}
            max={1}
            step={0.1}
            value={reproducibility}
            onChange={(e) => setReproducibility(Number(e.target.value))}
            className="mt-1 w-full accent-[var(--color-primary)]"
          />
        </label>
      </div>

      {error && <p className="mt-3 text-xs text-[var(--color-destructive)]">{error}</p>}

      <div className="mt-4 flex justify-end gap-2">
        <Button variant="ghost" size="sm" onClick={() => setOpen(false)} disabled={submitting}>
          キャンセル
        </Button>
        <Button size="sm" onClick={() => void handleSubmit()} disabled={!canSubmit}>
          {submitting ? "登録しています…" : "登録する"}
        </Button>
      </div>
    </section>
  );
}
