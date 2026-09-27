"use client";
import { MotionConfig } from "motion/react";
import { createContext, useCallback, useContext, useMemo, useState } from "react";
import { flushSync } from "react-dom";
import { dict, type Key, type Lang } from "./i18n";

export type Theme = "light" | "dark" | "system";
export type Loc = { fa: string; en: string };

function usePrefsValue(lang0: Lang, theme0: Theme) {
  const [lang, setLangState] = useState(lang0);
  const [theme, setThemeState] = useState(theme0);

  const setLang = useCallback((l: Lang) => {
    document.cookie = `lang=${l};path=/;max-age=31536000;samesite=lax`;
    const apply = () => {
      flushSync(() => setLangState(l));
      document.documentElement.lang = l;
      document.documentElement.dir = l === "fa" ? "rtl" : "ltr";
    };
    if (document.startViewTransition) document.startViewTransition(apply);
    else apply();
  }, []);

  // Theme changes reveal as a circle growing from the pointer (View Transitions); instant fallback otherwise.
  const setTheme = useCallback((next: Theme, x = innerWidth / 2, y = 0) => {
    const h = document.documentElement;
    document.cookie = `theme=${next};path=/;max-age=31536000;samesite=lax`;
    const apply = () => {
      flushSync(() => setThemeState(next));
      if (next === "system") delete h.dataset.theme;
      else h.dataset.theme = next;
    };
    if (!document.startViewTransition || matchMedia("(prefers-reduced-motion: reduce)").matches) return apply();
    h.classList.add("vt-theme");
    const r = Math.hypot(Math.max(x, innerWidth - x), Math.max(y, innerHeight - y));
    const vt = document.startViewTransition(apply);
    vt.ready.then(() =>
      h.animate(
        { clipPath: [`circle(0px at ${x}px ${y}px)`, `circle(${r}px at ${x}px ${y}px)`] },
        { duration: 650, easing: "cubic-bezier(.2,.8,.2,1)", pseudoElement: "::view-transition-new(root)" },
      ),
    );
    vt.finished.finally(() => h.classList.remove("vt-theme"));
  }, []);

  const toggleTheme = useCallback(
    (x?: number, y?: number) => {
      const dark = document.documentElement.dataset.theme
        ? document.documentElement.dataset.theme === "dark"
        : matchMedia("(prefers-color-scheme: dark)").matches;
      setTheme(dark ? "light" : "dark", x, y);
    },
    [setTheme],
  );

  return useMemo(() => {
    const nf = new Intl.NumberFormat(lang === "fa" ? "fa-IR" : "en-US");
    return {
      lang,
      dir: lang === "fa" ? "rtl" : "ltr",
      theme,
      setLang,
      setTheme,
      toggleTheme,
      t: (k: Key) => dict[lang][k],
      /** template with a number: "{n} cards" */
      tn: (k: Key, v: number | string) => dict[lang][k].replace("{n}", typeof v === "number" ? nf.format(v) : v),
      tl: (o: Loc) => o[lang],
      n: (v: number, o?: Intl.NumberFormatOptions) =>
        o ? new Intl.NumberFormat(lang === "fa" ? "fa-IR" : "en-US", o).format(v) : nf.format(v),
      locale: lang === "fa" ? "fa-IR-u-ca-persian" : "en-US",
    };
  }, [lang, theme, setLang, setTheme, toggleTheme]);
}

const Ctx = createContext<ReturnType<typeof usePrefsValue> | null>(null);

export function Prefs({ lang, theme, children }: { lang: Lang; theme: Theme; children: React.ReactNode }) {
  return (
    <Ctx.Provider value={usePrefsValue(lang, theme)}>
      <MotionConfig reducedMotion="user">{children}</MotionConfig>
    </Ctx.Provider>
  );
}

export const usePrefs = () => useContext(Ctx)!;
