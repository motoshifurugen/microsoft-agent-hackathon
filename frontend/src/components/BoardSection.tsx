// 困りごと掲示板 (Q&A) セクション
//
// 最小機能:
// - 質問一覧 (新着順)
// - 質問カードをクリックで詳細展開
// - 詳細パネルで回答リスト + 回答投稿
// - フッター付近に「+ 質問する」ボタンで投稿フォームを開く
import { useCallback, useEffect, useState } from "react";
import { ChevronRight, MessageSquare, Plus, Send } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  createBoardAnswer,
  createBoardQuestion,
  fetchBoardQuestionDetail,
  fetchBoardQuestions,
} from "@/lib/api";
import { cn } from "@/lib/utils";
import type { BoardQuestion, BoardQuestionDetail } from "@/types/api";

interface BoardSectionProps {
  categories: string[];
}

export function BoardSection({ categories }: BoardSectionProps) {
  const [questions, setQuestions] = useState<BoardQuestion[]>([]);
  const [openId, setOpenId] = useState<string | null>(null);
  const [detail, setDetail] = useState<BoardQuestionDetail | null>(null);
  const [composing, setComposing] = useState(false);

  const reload = useCallback(async () => {
    try {
      const list = await fetchBoardQuestions();
      setQuestions(list);
    } catch {
      setQuestions([]);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  useEffect(() => {
    if (!openId) return;
    fetchBoardQuestionDetail(openId).then(setDetail).catch(() => setDetail(null));
  }, [openId]);

  const handleAfterPost = async () => {
    setComposing(false);
    await reload();
  };

  return (
    <section>
      <div className="flex items-center justify-between">
        <SectionLabel>
          <MessageSquare className="h-3.5 w-3.5" />
          困りごと掲示板 ({questions.length})
        </SectionLabel>
        <Button variant="outline" size="sm" onClick={() => setComposing(true)}>
          <Plus className="h-3.5 w-3.5" />
          質問する
        </Button>
      </div>

      <div className="mt-2 grid gap-2">
        {questions.map((q) => (
          <button
            key={q.id}
            type="button"
            onClick={() => setOpenId((current) => (current === q.id ? null : q.id))}
            className={cn(
              "rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] px-3 py-2 text-left transition-colors",
              "hover:bg-[var(--color-accent)]",
              openId === q.id && "border-[var(--color-primary)]",
            )}
          >
            <div className="flex items-start justify-between gap-2">
              <div>
                <div className="text-sm font-medium leading-snug">{q.title}</div>
                <div className="mt-0.5 flex flex-wrap items-center gap-2 text-[11px] text-[var(--color-muted-foreground)]">
                  <span>by {q.author}</span>
                  {q.business_category && <Badge variant="muted">{q.business_category}</Badge>}
                  <span>回答 {q.answer_count} 件</span>
                </div>
              </div>
              <ChevronRight
                className={cn(
                  "h-4 w-4 shrink-0 opacity-60 transition-transform",
                  openId === q.id && "rotate-90",
                )}
              />
            </div>

            {openId === q.id && detail && (
              <DetailPane
                detail={detail}
                onAnswered={async () => {
                  await reload();
                  if (openId) {
                    const d = await fetchBoardQuestionDetail(openId);
                    setDetail(d);
                  }
                }}
              />
            )}
          </button>
        ))}
        {questions.length === 0 && (
          <p className="text-sm text-[var(--color-muted-foreground)]">
            まだ質問はありません。最初の 1 件を投稿してみませんか？
          </p>
        )}
      </div>

      {composing && (
        <ComposeQuestion
          categories={categories}
          onCancel={() => setComposing(false)}
          onPosted={handleAfterPost}
        />
      )}
    </section>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-[var(--color-muted-foreground)]">
      {children}
    </div>
  );
}

function DetailPane({
  detail,
  onAnswered,
}: {
  detail: BoardQuestionDetail;
  onAnswered: () => void | Promise<void>;
}) {
  const [body, setBody] = useState("");
  const [author, setAuthor] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!body.trim()) return;
    setSubmitting(true);
    try {
      await createBoardAnswer(detail.id, { body, author: author || undefined });
      setBody("");
      setAuthor("");
      await onAnswered();
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      className="mt-3 rounded-lg bg-[var(--color-muted)] p-3"
      onClick={(e) => e.stopPropagation()}
    >
      <p className="whitespace-pre-wrap text-xs leading-relaxed">{detail.body}</p>

      <div className="mt-3 grid gap-2">
        {detail.answers.map((a) => (
          <div
            key={a.id}
            className="rounded-md border border-[var(--color-border)] bg-[var(--color-card)] px-3 py-2"
          >
            <div className="text-xs leading-relaxed whitespace-pre-wrap">{a.body}</div>
            <div className="mt-1 text-[10px] text-[var(--color-muted-foreground)]">— {a.author}</div>
          </div>
        ))}
      </div>

      <form className="mt-3 grid gap-2" onSubmit={handleSubmit}>
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          rows={3}
          placeholder="回答や知ってる事例を書いてみる…"
          className="w-full rounded-md border border-[var(--color-border)] bg-[var(--color-card)] p-2 text-xs"
        />
        <div className="flex items-center justify-between gap-2">
          <input
            type="text"
            value={author}
            onChange={(e) => setAuthor(e.target.value)}
            placeholder="お名前 (空欄なら匿名)"
            className="flex-1 rounded-md border border-[var(--color-border)] bg-[var(--color-card)] px-2 py-1 text-xs"
          />
          <Button type="submit" size="sm" disabled={submitting || !body.trim()}>
            <Send className="h-3.5 w-3.5" />
            回答する
          </Button>
        </div>
      </form>
    </div>
  );
}

function ComposeQuestion({
  categories,
  onCancel,
  onPosted,
}: {
  categories: string[];
  onCancel: () => void;
  onPosted: () => void | Promise<void>;
}) {
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [category, setCategory] = useState<string>("");
  const [author, setAuthor] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !body.trim()) return;
    setSubmitting(true);
    try {
      await createBoardQuestion({
        title,
        body,
        business_category: category || null,
        author: author || undefined,
      });
      await onPosted();
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form
      className="mt-4 grid gap-2 rounded-xl border border-[var(--color-primary)] bg-[var(--color-card)] p-3"
      onSubmit={handleSubmit}
    >
      <input
        type="text"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="質問のタイトル (例: 議事録要約が時間かかります)"
        className="rounded-md border border-[var(--color-border)] bg-[var(--color-background)] px-2 py-1.5 text-sm"
      />
      <textarea
        value={body}
        onChange={(e) => setBody(e.target.value)}
        rows={4}
        placeholder="どんな業務で、どう困っているか、もう少し詳しく書いてみてください"
        className="rounded-md border border-[var(--color-border)] bg-[var(--color-background)] p-2 text-xs"
      />
      <div className="flex flex-wrap items-center gap-2">
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="rounded-md border border-[var(--color-border)] bg-[var(--color-background)] px-2 py-1 text-xs"
        >
          <option value="">カテゴリなし</option>
          {categories.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
        <input
          type="text"
          value={author}
          onChange={(e) => setAuthor(e.target.value)}
          placeholder="お名前 (空欄なら匿名)"
          className="flex-1 rounded-md border border-[var(--color-border)] bg-[var(--color-background)] px-2 py-1 text-xs"
        />
      </div>
      <div className="flex justify-end gap-2">
        <Button type="button" variant="ghost" size="sm" onClick={onCancel}>
          キャンセル
        </Button>
        <Button type="submit" size="sm" disabled={submitting || !title.trim() || !body.trim()}>
          <Send className="h-3.5 w-3.5" />
          投稿する
        </Button>
      </div>
    </form>
  );
}
