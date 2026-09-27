"use client";
import { createContext, useCallback, useContext, useEffect, useState } from "react";
import type { Loc } from "./prefs";

export type Me = {
  id: number; name: Loc; email: string; role: "learner" | "manager"; team: Loc | null;
  xp: number; level: number; level_progress: number; level_xp: number; streak: number;
  today_xp: number; daily_goal: number; week: number[]; due: number; rank: number; rank_of: number;
  badges: { code: string; day: string | null }[];
};
export type Track = {
  id: string; title: Loc; descr: Loc; color: string; icon: string;
  lessons: number; minutes: number; mastery: number; seen: number; total: number;
};
export type Item =
  | { type: "lesson"; id: number; track: string; title: Loc; body: Loc; minutes: number }
  | { type: "question"; id: number; track: string; prompt: Loc; choices: { fa: string[]; en: string[] }; review: boolean };
export type AnswerRes = { correct: boolean; answer: number; explain: Loc; xp: number; box: number; due_in: number; new_badges: string[] };

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

/** Same-origin fetch to the FastAPI backend (proxied by Next rewrites); auth rides on an httpOnly cookie. */
export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch("/api" + path, { ...init, headers: { "Content-Type": "application/json", ...init.headers } });
  if (!res.ok) throw new ApiError(res.status, await res.text());
  return res.json();
}

export const post = <T,>(path: string, body?: unknown) => api<T>(path, { method: "POST", body: JSON.stringify(body ?? {}) });

export function useApi<T>(path: string | null) {
  // data is tagged with its path: a reload keeps showing current data, a new path starts empty
  const [state, setState] = useState<{ path: string; data: T }>();
  const [error, setError] = useState<Error>();
  const load = useCallback(() => {
    if (!path) return;
    setError(undefined);
    api<T>(path).then((data) => setState({ path, data }), setError);
  }, [path]);
  useEffect(load, [load]);
  return { data: state?.path === path ? state.data : undefined, error, reload: load };
}

export const MeCtx = createContext<{ me: Me; reload: () => void } | null>(null);
export const useMe = () => useContext(MeCtx)!;
