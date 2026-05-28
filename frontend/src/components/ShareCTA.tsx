import { Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

interface ShareCTAProps {
  onClick: () => void;
}

export function ShareCTA({ onClick }: ShareCTAProps) {
  return (
    <section className="rounded-xl border border-dashed border-[var(--color-border)] bg-[var(--color-muted)] p-5 text-center">
      <p className="text-sm">あなたの成功事例を、次の誰かに届けませんか？</p>
      <button
        type="button"
        onClick={onClick}
        className={cn(
          "mt-3 inline-flex items-center gap-2 rounded-md bg-[var(--color-primary)] px-4 py-2 text-sm font-medium text-[var(--color-primary-foreground)]",
          "transition-opacity hover:opacity-90",
        )}
      >
        <Sparkles className="h-3.5 w-3.5" />
        自分の成功を共有する
      </button>
      <p className="mt-2 text-[11px] text-[var(--color-muted-foreground)]">
        (送信先: 社内 DX 推進部)
      </p>
    </section>
  );
}
