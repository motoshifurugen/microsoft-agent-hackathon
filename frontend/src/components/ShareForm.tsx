import { useEffect, useState } from "react";
import { Send, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { createCase, fetchCategoryMaster } from "@/lib/api";
import type { CaseDetail } from "@/types/api";

interface ShareFormProps {
  clientId: string;
  onCreated: (created: CaseDetail) => void;
}

// マスタ外を自由入力させるための select 用センチネル値。
const OTHER = "__other__";
const REQUIRED_COUNT = 3;

const inputClass =
  "mt-1 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-2 text-sm outline-none transition-colors focus:border-[var(--color-primary)] focus:ring-2 focus:ring-[var(--color-primary)]/20";

function RequiredMark() {
  return <span className="text-[var(--color-destructive)]">*</span>;
}

// ユーザーが自分の成功事例をその場で登録するフォーム。
// 必須: owner_label / business_type / what_worked。残りは任意。
export function ShareForm({ clientId, onCreated }: ShareFormProps) {
  const [categoryOptions, setCategoryOptions] = useState<string[]>([]);
  const [ownerLabel, setOwnerLabel] = useState("");
  // category は select 値 (マスタ値 / OTHER / 空)、customCategory は その他 選択時の自由入力。
  const [category, setCategory] = useState("");
  const [customCategory, setCustomCategory] = useState("");
  const [whatWorked, setWhatWorked] = useState("");
  const [whyWorked, setWhyWorked] = useState("");
  const [concretePrompt, setConcretePrompt] = useState("");
  const [quantitativeEffect, setQuantitativeEffect] = useState("");
  const [reproducibility, setReproducibility] = useState(0.5);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  useEffect(() => {
    fetchCategoryMaster()
      .then(setCategoryOptions)
      .catch(() => setCategoryOptions([]));
  }, []);

  const businessType = category === OTHER ? customCategory : category;

  const filledRequired =
    (ownerLabel.trim() ? 1 : 0) +
    (businessType.trim() ? 1 : 0) +
    (whatWorked.trim() ? 1 : 0);
  const canSubmit = filledRequired === REQUIRED_COUNT && !submitting;

  const reset = () => {
    setOwnerLabel("");
    setCategory("");
    setCustomCategory("");
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
      setTimeout(() => setDone(false), 4000);
    } catch {
      setError("登録に失敗しました。時間をおいて再度お試しください。");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-card)] p-6 shadow-card">
      <div className="flex items-center gap-1.5 text-sm font-semibold">
        <Sparkles className="h-4 w-4 text-[var(--color-primary)]" />
        成功事例を共有する
      </div>
      <p className="mt-1 text-xs text-[var(--color-muted-foreground)]">
        登録した事例はカテゴリ一覧や検索の対象になり、社内で再利用されます。
      </p>

      {done && (
        <p className="mt-3 rounded-lg bg-[var(--color-success-subtle)] px-3 py-2 text-xs text-[var(--color-success)]">
          成功事例を登録しました。次の誰かの力になります。
        </p>
      )}

      <div className="mt-4 rounded-lg bg-[var(--color-muted)] p-3">
        <div className="flex items-center justify-between text-[11px] font-semibold">
          <span className="text-[var(--color-muted-foreground)]">必須項目の入力状況</span>
          <span className="text-[var(--color-primary)]">
            {filledRequired} / {REQUIRED_COUNT}
          </span>
        </div>
        <div className="mt-1.5 h-1 overflow-hidden rounded-full bg-[var(--color-border)]">
          <div
            className="h-full rounded-full bg-[var(--color-primary)] transition-all"
            style={{ width: `${(filledRequired / REQUIRED_COUNT) * 100}%` }}
          />
        </div>
      </div>

      <div className="mt-4 grid gap-3">
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="block text-xs font-medium">
            表示名 <RequiredMark />
            <input
              value={ownerLabel}
              onChange={(e) => setOwnerLabel(e.target.value)}
              placeholder="例: 営業部 サンプルさん"
              className={inputClass}
            />
          </label>

          <label className="block text-xs font-medium">
            業務カテゴリ <RequiredMark />
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className={inputClass}
            >
              <option value="" disabled>
                選択してください
              </option>
              {categoryOptions.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
              <option value={OTHER}>その他（自由入力）</option>
            </select>
          </label>
        </div>

        {category === OTHER && (
          <label className="block text-xs font-medium">
            カテゴリ名（自由入力） <RequiredMark />
            <input
              value={customCategory}
              onChange={(e) => setCustomCategory(e.target.value)}
              placeholder="例: 週次報告作成"
              className={inputClass}
            />
          </label>
        )}

        <label className="block text-xs font-medium">
          うまくいったこと <RequiredMark />
          <textarea
            value={whatWorked}
            onChange={(e) => setWhatWorked(e.target.value)}
            rows={2}
            placeholder="例: Copilot で前週ログから下書きを生成した"
            className={`${inputClass} resize-y`}
          />
        </label>

        <div className="text-[11px] font-semibold uppercase tracking-wider text-[var(--color-muted-foreground)]">
          詳細（任意）
        </div>

        <label className="block text-xs font-medium">
          なぜ効いたか
          <textarea
            value={whyWorked}
            onChange={(e) => setWhyWorked(e.target.value)}
            rows={2}
            placeholder="例: 定型作業のテンプレ化が効いた"
            className={`${inputClass} resize-y`}
          />
        </label>

        <label className="block text-xs font-medium">
          使ったプロンプト
          <textarea
            value={concretePrompt}
            onChange={(e) => setConcretePrompt(e.target.value)}
            rows={2}
            placeholder="例: 以下のログを週次報告の体裁にまとめて: ..."
            className={`${inputClass} resize-y font-mono`}
          />
        </label>

        <label className="block text-xs font-medium">
          定量効果
          <input
            value={quantitativeEffect}
            onChange={(e) => setQuantitativeEffect(e.target.value)}
            placeholder="例: 週 2h → 30min"
            className={inputClass}
          />
        </label>

        <div className="text-xs font-medium">
          再現性: {reproducibility.toFixed(1)} / 1.0
          <input
            type="range"
            min={0}
            max={1}
            step={0.1}
            value={reproducibility}
            onChange={(e) => setReproducibility(Number(e.target.value))}
            className="mt-1 w-full accent-[var(--color-primary)]"
          />
          <div className="flex justify-between text-[10px] text-[var(--color-muted-foreground)]">
            <span>再現が難しい</span>
            <span>誰でも再現できる</span>
          </div>
        </div>
      </div>

      {error && <p className="mt-3 text-xs text-[var(--color-destructive)]">{error}</p>}

      <div className="mt-5 flex justify-end gap-2">
        <Button variant="ghost" size="sm" onClick={reset} disabled={submitting}>
          クリア
        </Button>
        <Button size="sm" onClick={() => void handleSubmit()} disabled={!canSubmit}>
          <Send className="h-3.5 w-3.5" />
          {submitting ? "登録しています…" : "事例を登録する"}
        </Button>
      </div>
    </section>
  );
}
