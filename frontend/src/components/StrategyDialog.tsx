import { useEffect, useState } from "react";
import { Check, Copy, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { executeStrategy } from "@/lib/api";
import type { StrategyExecuteResponse, StrategyId } from "@/types/api";

interface StrategyDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  strategyId: StrategyId | null;
  targetUserId: string;
  caseId: string;
}

export function StrategyDialog({
  open,
  onOpenChange,
  strategyId,
  targetUserId,
  caseId,
}: StrategyDialogProps) {
  const [result, setResult] = useState<StrategyExecuteResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // Dialog が開かれたタイミングで API 呼び出しと state リセットを行う。
  useEffect(() => {
    if (!open || !strategyId) return;
    setResult(null);
    setError(null);
    setCopied(false);
    executeStrategy(strategyId, targetUserId, caseId)
      .then(setResult)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : String(err)));
  }, [open, strategyId, targetUserId, caseId]);

  const handleCopy = async () => {
    if (!result) return;
    await navigator.clipboard.writeText(result.message_preview);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogHeader>
        <DialogTitle>
          戦略 {strategyId} のプレビュー
        </DialogTitle>
        <DialogDescription>
          以下のメッセージを Teams DM や メールで送ってみてください。
        </DialogDescription>
      </DialogHeader>

      <DialogContent>
        {error && (
          <div className="rounded-md border border-[var(--color-destructive)] bg-[var(--color-destructive)]/10 p-3 text-sm">
            {error}
          </div>
        )}

        {!result && !error && (
          <div className="flex items-center gap-2 text-sm text-[var(--color-muted-foreground)]">
            <Loader2 className="h-4 w-4 animate-spin" />
            生成中…
          </div>
        )}

        {result && (
          <pre className="max-h-[40vh] overflow-auto whitespace-pre-wrap rounded-md border border-[var(--color-border)] bg-[var(--color-muted)] p-3 text-xs leading-relaxed">
            {result.message_preview}
          </pre>
        )}
      </DialogContent>

      <DialogFooter>
        <Button variant="ghost" onClick={() => onOpenChange(false)}>
          閉じる
        </Button>
        <Button onClick={handleCopy} disabled={!result}>
          {copied ? (
            <>
              <Check className="h-3.5 w-3.5" />
              コピー済み
            </>
          ) : (
            <>
              <Copy className="h-3.5 w-3.5" />
              コピー
            </>
          )}
        </Button>
      </DialogFooter>
    </Dialog>
  );
}
