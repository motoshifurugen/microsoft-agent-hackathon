import { useEffect, useState } from "react";
import { History, Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

interface ExecutionEntry {
  execution_id: string;
  strategy_id: "A" | "B";
  target_user_id: string;
  case_id: string;
  message_preview: string;
  executed_at: string;
}

export function AdminHistoryView() {
  const [executions, setExecutions] = useState<ExecutionEntry[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/admin/executions")
      .then((res) => res.json())
      .then((data: ExecutionEntry[]) => setExecutions(data))
      .catch((err: unknown) => setError(err instanceof Error ? err.message : String(err)));
  }, []);

  if (error) {
    return (
      <div className="rounded-md border border-[var(--color-destructive)] bg-[var(--color-destructive)]/10 p-4 text-sm">
        {error}
      </div>
    );
  }

  if (!executions) {
    return (
      <div className="flex items-center gap-2 text-sm text-[var(--color-muted-foreground)]">
        <Loader2 className="h-4 w-4 animate-spin" />
        読み込み中…
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <History className="h-5 w-5" />
        <h2 className="text-xl font-semibold">戦略実行履歴</h2>
      </div>

      {executions.length === 0 ? (
        <Card>
          <CardContent className="py-8 text-center text-sm text-[var(--color-muted-foreground)]">
            まだ実行履歴がありません。「メンバー支援」から戦略を実行すると、ここに記録されます。
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-3">
          {executions.map((exe) => (
            <Card key={exe.execution_id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Badge>{exe.strategy_id}</Badge>
                    {exe.target_user_id}
                  </CardTitle>
                  <span className="text-[11px] text-[var(--color-muted-foreground)]">
                    {new Date(exe.executed_at).toLocaleString()}
                  </span>
                </div>
              </CardHeader>
              <Separator />
              <CardContent className="pt-3">
                <pre className="whitespace-pre-wrap text-xs leading-relaxed">
                  {exe.message_preview}
                </pre>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
