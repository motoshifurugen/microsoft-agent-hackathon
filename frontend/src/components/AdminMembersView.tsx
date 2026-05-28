import { useEffect, useState } from "react";
import { ChevronRight, Loader2, Sparkles, Users } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CaseCard } from "@/components/CaseCard";
import { StrategyDialog } from "@/components/StrategyDialog";
import { fetchAdminUsers, fetchRecommendations } from "@/lib/api";
import { cn } from "@/lib/utils";
import type {
  RecommendationResponse,
  StrategyId,
  UserSummary,
} from "@/types/api";

interface AdminMembersViewProps {
  onCopy: (text: string) => void;
}

export function AdminMembersView({ onCopy }: AdminMembersViewProps) {
  const [users, setUsers] = useState<UserSummary[]>([]);
  const [selectedUser, setSelectedUser] = useState<string | null>(null);
  const [recommendation, setRecommendation] = useState<RecommendationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeStrategy, setActiveStrategy] = useState<{
    strategyId: StrategyId;
    caseId: string;
  } | null>(null);

  useEffect(() => {
    fetchAdminUsers()
      .then((u) => {
        setUsers(u);
        if (u.length > 0 && u[0]) setSelectedUser(u[0].user_id);
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : String(err)));
  }, []);

  // 選択ユーザー変更時に推薦事例を再取得。
  useEffect(() => {
    if (!selectedUser) return;
    setLoading(true);
    setRecommendation(null);
    fetchRecommendations(selectedUser)
      .then(setRecommendation)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  }, [selectedUser]);

  if (error) {
    return (
      <div className="rounded-md border border-[var(--color-destructive)] bg-[var(--color-destructive)]/10 p-4 text-sm">
        {error}
      </div>
    );
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[260px_1fr]">
      <Card className="h-fit">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Users className="h-4 w-4" />
            メンバー
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-1 p-2">
          {users.map((u) => (
            <button
              key={u.user_id}
              type="button"
              onClick={() => setSelectedUser(u.user_id)}
              className={cn(
                "flex w-full items-center justify-between gap-2 rounded-md px-2.5 py-1.5 text-sm transition-colors",
                selectedUser === u.user_id
                  ? "bg-[var(--color-primary)] text-[var(--color-primary-foreground)]"
                  : "hover:bg-[var(--color-accent)]",
              )}
            >
              <div className="flex flex-col text-left">
                <span className="font-medium">{u.owner_label}</span>
                <span className="text-[10px] opacity-80">{u.business_type}</span>
              </div>
              <ChevronRight className="h-3.5 w-3.5 opacity-70" />
            </button>
          ))}
        </CardContent>
      </Card>

      <div className="flex flex-col gap-5">
        {!selectedUser && (
          <div className="text-sm text-[var(--color-muted-foreground)]">
            左からメンバーを選んでください。
          </div>
        )}

        {loading && (
          <div className="flex items-center gap-2 text-sm text-[var(--color-muted-foreground)]">
            <Loader2 className="h-4 w-4 animate-spin" />
            推薦事例を計算中…
          </div>
        )}

        {recommendation && (
          <>
            <Card>
              <CardHeader>
                <div className="text-xs font-semibold uppercase tracking-wider text-[var(--color-muted-foreground)]">
                  選択中のメンバー
                </div>
                <CardTitle className="text-xl">{recommendation.target_owner_label}</CardTitle>
                <div className="flex flex-wrap gap-2">
                  <Badge variant="secondary">{recommendation.target_business_type}</Badge>
                </div>
              </CardHeader>
            </Card>

            <div>
              <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[var(--color-muted-foreground)]">
                <Sparkles className="h-3.5 w-3.5" />
                推薦事例 (上位 {recommendation.cases.length} 件)
              </div>
              <div className="grid gap-4">
                {recommendation.cases.map((c, idx) => (
                  <CaseCard
                    key={c.case_id}
                    rank={idx + 1}
                    caseDetail={c}
                    onCopy={() => onCopy(c.concrete_prompt)}
                  />
                ))}
              </div>
            </div>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">次のアクション</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-2 sm:grid-cols-2">
                  {recommendation.strategies.map((s) => (
                    <Button
                      key={s.id}
                      variant={s.id === "A" ? "default" : "outline"}
                      onClick={() => {
                        const firstCase = recommendation.cases[0];
                        if (!firstCase) return;
                        setActiveStrategy({
                          strategyId: s.id,
                          caseId: firstCase.case_id,
                        });
                      }}
                      className="h-auto justify-start whitespace-normal py-3 text-left"
                    >
                      <div className="flex flex-col gap-1">
                        <span className="font-semibold">戦略 {s.id}: {s.title}</span>
                        <span className="text-xs font-normal opacity-90">{s.description}</span>
                      </div>
                    </Button>
                  ))}
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </div>

      {activeStrategy && (
        <StrategyDialog
          open={!!activeStrategy}
          onOpenChange={(open) => {
            if (!open) setActiveStrategy(null);
          }}
          strategyId={activeStrategy.strategyId}
          targetUserId={selectedUser ?? ""}
          caseId={activeStrategy.caseId}
        />
      )}
    </div>
  );
}
