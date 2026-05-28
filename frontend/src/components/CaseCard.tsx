import { Copy, Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import type { CaseDetail } from "@/types/api";

interface CaseCardProps {
  caseDetail: CaseDetail;
  rank?: number;
  onCopy?: () => void;
}

export function CaseCard({ caseDetail, rank, onCopy }: CaseCardProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-2">
            {typeof rank === "number" && (
              <Badge variant="muted" className="w-7 justify-center">
                {rank}
              </Badge>
            )}
            <CardTitle>{caseDetail.owner_label}の事例</CardTitle>
          </div>
          {caseDetail.score > 0 && (
            <Badge variant="outline" className="shrink-0">
              スコア {caseDetail.score.toFixed(2)}
            </Badge>
          )}
        </div>
        <div className="flex flex-wrap gap-1.5">
          <Badge variant="secondary">{caseDetail.business_type}</Badge>
          {caseDetail.quantitative_effect && (
            <Badge variant="default" className="bg-[var(--color-primary)]/15 text-[var(--color-primary)]">
              <Sparkles className="mr-1 h-3 w-3" />
              {caseDetail.quantitative_effect}
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="flex flex-col gap-3">
        <p className="text-sm leading-relaxed">{caseDetail.what_worked}</p>

        <div className="rounded-md border border-[var(--color-border)] bg-[var(--color-muted)] p-3">
          <div className="mb-1.5 text-[11px] font-semibold uppercase tracking-wider text-[var(--color-muted-foreground)]">
            使えるプロンプト
          </div>
          <p className="whitespace-pre-wrap text-xs leading-relaxed text-[var(--color-foreground)]">
            {caseDetail.concrete_prompt || "(プロンプト未登録)"}
          </p>
        </div>

        <p className="text-xs leading-relaxed text-[var(--color-muted-foreground)]">
          なぜ機能した: {caseDetail.why_worked}
        </p>
      </CardContent>

      <CardFooter>
        <Button
          variant="outline"
          size="sm"
          onClick={onCopy}
          disabled={!caseDetail.concrete_prompt}
        >
          <Copy className="h-3.5 w-3.5" />
          プロンプトをコピー
        </Button>
      </CardFooter>
    </Card>
  );
}
