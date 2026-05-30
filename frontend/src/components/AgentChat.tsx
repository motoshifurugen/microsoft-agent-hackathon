// ホームの主役。困りごとを話すと Orchestrator (Foundry Agent) が
// 似た事例の検索・提案・保存確認を自律的に行い、応答をストリーミング表示する。
// 旧 PainInput (固定検索) を置き換える「AIに相談」チャット。
import { useEffect, useRef, useState } from "react";
import { ArrowUp, Sparkles } from "lucide-react";
import { SectionLabel } from "@/components/SectionLabel";
import { Button } from "@/components/ui/button";
import { streamAgentChat } from "@/lib/api";

type Role = "user" | "agent";

interface ChatMessage {
  id: string;
  role: Role;
  text: string;
}

const MAX_LEN = 2000;
const SUGGESTIONS = ["議事録の要約に時間がかかる", "提案書の下書きを作りたい", "アンケートの集計が大変"];

let messageSeq = 0;
const nextId = () => `m${messageSeq++}`;

interface AgentChatProps {
  clientId: string;
  /** FollowUpCard 等から外部供給される自動送信メッセージ。null で何もしない。 */
  pendingMessage?: string | null;
  /** pendingMessage を送信したら呼ぶ（親側で null に戻すため）。 */
  onPendingConsumed?: () => void;
}

export function AgentChat({ clientId, pendingMessage, onPendingConsumed }: AgentChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  // send を effect 依存に入れると毎レンダーで再実行されるため ref 経由で最新版を参照する。
  const sendRef = useRef<(raw: string) => Promise<void>>(async () => {});

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  useEffect(() => () => abortRef.current?.abort(), []);

  const appendToAgent = (token: string) => {
    setMessages((prev) => {
      const next = [...prev];
      const last = next[next.length - 1];
      if (last && last.role === "agent") {
        next[next.length - 1] = { ...last, text: last.text + token };
      }
      return next;
    });
  };

  const send = async (raw: string) => {
    const message = raw.trim();
    if (!message || streaming) return;

    setError(null);
    setInput("");
    const agentId = nextId();
    setMessages((prev) => [
      ...prev,
      { id: nextId(), role: "user", text: message },
      { id: agentId, role: "agent", text: "" },
    ]);
    setStreaming(true);

    const controller = new AbortController();
    abortRef.current = controller;

    await streamAgentChat(
      { message, client_id: clientId },
      {
        onToken: appendToAgent,
        onDone: () => setStreaming(false),
        onError: (msg) => {
          setError(msg);
          setStreaming(false);
        },
      },
      controller.signal,
    );
  };

  // send は毎レンダー再生成されるため、最新版を ref に保持する（effect 依存の churn 回避）。
  useEffect(() => {
    sendRef.current = send;
  });

  // 外部供給メッセージ（FollowUpCard の「共有する」）を、ストリーミング中でなければ自動送信する。
  useEffect(() => {
    if (!pendingMessage || streaming) return;
    void sendRef.current(pendingMessage);
    onPendingConsumed?.();
  }, [pendingMessage, streaming, onPendingConsumed]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void send(input);
    }
  };

  const isEmpty = messages.length === 0;

  return (
    <section className="flex flex-col rounded-2xl border border-[var(--color-border)] bg-[var(--color-card)] p-5 shadow-card">
      <SectionLabel icon={<Sparkles className="h-3.5 w-3.5" />}>AIに相談</SectionLabel>

      <div
        ref={scrollRef}
        className="mt-3 flex max-h-[420px] min-h-[120px] flex-col gap-3 overflow-y-auto"
      >
        {isEmpty ? (
          <div className="flex flex-1 flex-col items-center justify-center gap-3 py-6 text-center">
            <p className="text-sm text-[var(--color-muted-foreground)]">
              困りごとを話すと、AI が社内の似た事例を探して提案します。
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => void send(s)}
                  className="rounded-full bg-[var(--color-muted)] px-3 py-1 text-xs text-[var(--color-secondary-foreground)] transition-colors hover:bg-[var(--color-accent)] hover:text-[var(--color-accent-foreground)]"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((m) => <ChatBubble key={m.id} message={m} streaming={streaming} />)
        )}
      </div>

      {error && <p className="mt-2 text-xs text-[var(--color-destructive)]">{error}</p>}

      <div className="mt-3 flex items-end gap-2">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value.slice(0, MAX_LEN))}
          onKeyDown={handleKeyDown}
          rows={2}
          maxLength={MAX_LEN}
          placeholder="例: 毎月の月次レポート作成に時間がかかって困っている…"
          className="w-full resize-none rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-2 text-sm outline-none transition-colors focus:border-[var(--color-primary)] focus:ring-2 focus:ring-[var(--color-primary)]/20"
        />
        <Button
          size="icon"
          onClick={() => void send(input)}
          disabled={streaming || input.trim().length === 0}
          aria-label="送信"
        >
          <ArrowUp className="h-4 w-4" />
        </Button>
      </div>
    </section>
  );
}

function ChatBubble({ message, streaming }: { message: ChatMessage; streaming: boolean }) {
  const isUser = message.role === "user";
  const isPending = message.role === "agent" && message.text === "" && streaming;

  return (
    <div className={isUser ? "flex justify-end" : "flex justify-start"}>
      <div
        className={
          isUser
            ? "max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-br-sm bg-[var(--color-primary)] px-3.5 py-2 text-sm text-[var(--color-primary-foreground)]"
            : "max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-bl-sm bg-[var(--color-muted)] px-3.5 py-2 text-sm text-[var(--color-foreground)]"
        }
      >
        {isPending ? (
          <span className="text-[var(--color-muted-foreground)]">考えています…</span>
        ) : (
          message.text
        )}
      </div>
    </div>
  );
}
