import { Copy, Sparkles, ThumbsUp } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { CaseDetail } from "@/types/api";

interface CaseCardProps {
  caseDetail: CaseDetail;
  feedback?: "good" | "soso";
  onCopy: () => void;
  onFeedback: (value: "good" | "soso") => void;
}

export function CaseCard({ caseDetail, feedback, onCopy, onFeedback }: CaseCardProps) {
  return (
    <article className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-4 shadow-sm">
      <header className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-semibold leading-tight">
            {caseDetail.owner_label}の事例
          </div>
          {caseDetail.quantitative_effect && (
            <div className="mt-1 inline-flex items-center gap-1 text-[11px] text-[var(--color-primary)]">
              <Sparkles className="h-3 w-3" />
              {caseDetail.quantitative_effect}
            </div>
          )}
        </div>
        <Badge variant="muted" className="shrink-0 text-[10px]">
          {caseDetail.business_type}
        </Badge>
      </header>

      <p className="mt-3 text-sm leading-relaxed">{caseDetail.what_worked}</p>

      {caseDetail.concrete_prompt && (
        <div className="mt-3 rounded-lg border border-[var(--color-border)] bg-[var(--color-muted)] p-3">
          <div className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-[var(--color-muted-foreground)]">
            使えるプロンプト
          </div>
          <p className="whitespace-pre-wrap text-xs leading-relaxed">
            {caseDetail.concrete_prompt}
          </p>
        </div>
      )}

      <footer className="mt-3 flex items-center justify-between gap-2">
        <Button variant="outline" size="sm" onClick={onCopy} disabled={!caseDetail.concrete_prompt}>
          <Copy className="h-3.5 w-3.5" />
          コピーして試す
        </Button>
        <div className="flex items-center gap-1.5 text-xs text-[var(--color-muted-foreground)]">
          <span>役立ちましたか？</span>
          <FeedbackButton
            label="役立った"
            active={feedback === "good"}
            onClick={() => onFeedback("good")}
          >
            <ThumbsUp className="h-3.5 w-3.5" />
          </FeedbackButton>
          <FeedbackButton
            label="もう少し"
            active={feedback === "soso"}
            onClick={() => onFeedback("soso")}
          >
            🤔
          </FeedbackButton>
        </div>
      </footer>
    </article>
  );
}

function FeedbackButton({
  label,
  active,
  onClick,
  children,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      title={label}
      className={cn(
        "flex h-6 w-6 items-center justify-center rounded-full border text-xs transition-colors",
        active
          ? "border-[var(--color-primary)] bg-[var(--color-primary)] text-[var(--color-primary-foreground)]"
          : "border-[var(--color-border)] hover:bg-[var(--color-accent)]",
      )}
    >
      {children}
    </button>
  );
}
