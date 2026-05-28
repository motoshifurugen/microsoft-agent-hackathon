// localStorage に JSON を読み書きする hook。
// 「最近試したもの」「フィードバック」など、サーバー側を介さず保存したい値に使う。
import { useCallback, useState } from "react";

function readJsonRecord(key: string): Record<string, string> {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return {};
    const parsed = JSON.parse(raw) as unknown;
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
      return parsed as Record<string, string>;
    }
  } catch {
    // localStorage が無効 / JSON 不正など。ignore して空 record を返す。
  }
  return {};
}

function writeJsonRecord(key: string, value: Record<string, string>) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // localStorage 書き込み禁止環境 (シークレットモード等) は黙って失敗
  }
}

export interface LocalStorageJsonHandle {
  value: Record<string, string>;
  set: (key: string, v: string) => void;
  /** key を渡すと toggle: 同じ値なら削除、別の値なら上書き */
  toggle: (key: string, v: string) => void;
  remove: (key: string) => void;
  clear: () => void;
}

export function useLocalStorageJson(storageKey: string): LocalStorageJsonHandle {
  const [value, setValue] = useState<Record<string, string>>(() => readJsonRecord(storageKey));

  const set = useCallback(
    (key: string, v: string) => {
      const next = { ...readJsonRecord(storageKey), [key]: v };
      setValue(next);
      writeJsonRecord(storageKey, next);
    },
    [storageKey],
  );

  const toggle = useCallback(
    (key: string, v: string) => {
      const current = readJsonRecord(storageKey);
      const next =
        current[key] === v
          ? Object.fromEntries(Object.entries(current).filter(([k]) => k !== key))
          : { ...current, [key]: v };
      setValue(next);
      writeJsonRecord(storageKey, next);
    },
    [storageKey],
  );

  const remove = useCallback(
    (key: string) => {
      const next = Object.fromEntries(
        Object.entries(readJsonRecord(storageKey)).filter(([k]) => k !== key),
      );
      setValue(next);
      writeJsonRecord(storageKey, next);
    },
    [storageKey],
  );

  const clear = useCallback(() => {
    setValue({});
    writeJsonRecord(storageKey, {});
  }, [storageKey]);

  return { value, set, toggle, remove, clear };
}
