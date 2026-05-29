// 認証が無いため、localStorage に生成・永続化したクライアント識別子で個人を区別する。
// 困りごと記録の user_id やブックマークの所有者キーとして使う。
import { useState } from "react";

const CLIENT_ID_KEY = "kodama-client-id";

function generateClientId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return `c-${crypto.randomUUID()}`;
  }
  return `c-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function readOrCreateClientId(): string {
  try {
    const existing = localStorage.getItem(CLIENT_ID_KEY);
    if (existing) return existing;
    const created = generateClientId();
    localStorage.setItem(CLIENT_ID_KEY, created);
    return created;
  } catch {
    // localStorage 不可環境ではセッション内のみ有効な ID を返す
    return generateClientId();
  }
}

export function useClientId(): string {
  const [clientId] = useState<string>(() => readOrCreateClientId());
  return clientId;
}
