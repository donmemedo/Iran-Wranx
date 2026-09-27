"use client";
import {
  Crown, Flame, HeartHandshake, Languages, Moon, Rocket, Scale, ShieldCheck, Star, Sun, TrendingUp, Zap,
} from "lucide-react";
import { animate, motion, useInView } from "motion/react";
import { useEffect, useId, useRef, useState } from "react";
import { usePrefs } from "@/lib/prefs";

// Apple-style springs: critically damped by default, bounce only for momentum/celebration.
export const spring = { type: "spring", bounce: 0, duration: 0.45 } as const;
export const bouncy = { type: "spring", bounce: 0.35, duration: 0.6 } as const;

export const cx = (...c: (string | false | null | undefined)[]) => c.filter(Boolean).join(" ");

export const TRACK_ICONS = { "trending-up": TrendingUp, "heart-handshake": HeartHandshake, "shield-check": ShieldCheck, scale: Scale };
export const BADGE_ICONS = { first_steps: Rocket, streak_3: Flame, streak_7: Zap, xp_500: Star, track_master: Crown };
export const BADGE_HUES = { first_steps: "#5b46ff", streak_3: "#ff7a1a", streak_7: "#ff4f8b", xp_500: "#ffb020", track_master: "#12b8e0" };

/** Pointer-follow spotlight for `.spot` cards. */
export function spot(e: React.PointerEvent<HTMLElement>) {
  const r = e.currentTarget.getBoundingClientRect();
  e.currentTarget.style.setProperty("--x", `${e.clientX - r.left}px`);
  e.currentTarget.style.setProperty("--y", `${e.clientY - r.top}px`);
}

export function Mark({ size = 30 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden className="shrink-0">
      <defs>
        <linearGradient id="rx-mark" x1="0" y1="1" x2="1" y2="0">
          <stop stopColor="#5b46ff" />
          <stop offset=".55" stopColor="#ff4f8b" />
          <stop offset="1" stopColor="#ffb020" />
        </linearGradient>
      </defs>
      <rect width="32" height="32" rx="9.5" fill="url(#rx-mark)" />
      <rect x="7" y="17" width="4.6" height="8" rx="2.3" fill="#fff" opacity=".7" />
      <rect x="13.7" y="12" width="4.6" height="13" rx="2.3" fill="#fff" opacity=".88" />
      <rect x="20.4" y="7" width="4.6" height="18" rx="2.3" fill="#fff" />
    </svg>
  );
}

export function Logo() {
  const { t } = usePrefs();
  return (
    <span className="inline-flex items-center gap-2.5 text-lg font-extrabold">
      <Mark />
      {t("brand")}
    </span>
  );
}

export function Card({ className, children, delay = 0, as = "section" }: { className?: string; children: React.ReactNode; delay?: number; as?: "section" | "div" }) {
  const C = as === "div" ? motion.div : motion.section;
  return (
    <C
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ ...spring, delay }}
      className={cx("glass rounded-[28px] p-5", className)}
    >
      {children}
    </C>
  );
}

/** Animated number that counts up when scrolled into view, formatted for the active locale. */
export function Num({ value, format, className }: { value: number; format?: Intl.NumberFormatOptions; className?: string }) {
  const { n } = usePrefs();
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true });
  const from = useRef(0);
  useEffect(() => {
    if (!inView) return;
    const fmt = (v: number) => n(format?.style === "percent" ? v : Math.round(v), format);
    const c = animate(from.current, value, {
      duration: 1.1,
      ease: [0.2, 0.8, 0.2, 1],
      onUpdate: (v) => ref.current && (ref.current.textContent = fmt(v)),
    });
    from.current = value;
    return () => c.stop();
  }, [value, inView, n, format]);
  return (
    <span ref={ref} className={cx("tabular-nums", className)}>
      {n(0, format)}
    </span>
  );
}

export function Ring({ value, size = 120, stroke = 12, color, children }: { value: number; size?: number; stroke?: number; color?: string; children?: React.ReactNode }) {
  const id = useId();
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  return (
    <div className="relative grid shrink-0 place-items-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90" aria-hidden>
        <defs>
          <linearGradient id={id} x1="0" y1="0" x2="1" y2="1">
            <stop stopColor="#5b46ff" />
            <stop offset=".5" stopColor="#ff4f8b" />
            <stop offset="1" stopColor="#ffb020" />
          </linearGradient>
        </defs>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--line)" strokeWidth={stroke} />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color ?? `url(#${id})`}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={c}
          initial={{ strokeDashoffset: c }}
          animate={{ strokeDashoffset: c * (1 - Math.min(Math.max(value, 0), 1)) }}
          transition={{ type: "spring", bounce: 0, duration: 1.4 }}
        />
      </svg>
      <div className="absolute inset-0 grid place-items-center text-center">{children}</div>
    </div>
  );
}

export function Bar({ value, color, className }: { value: number; color?: string; className?: string }) {
  return (
    <div className={cx("h-2 overflow-hidden rounded-full bg-line", className)}>
      <motion.div
        className="h-full rounded-full"
        style={{ background: color ?? "var(--grad)" }}
        initial={{ width: 0 }}
        whileInView={{ width: `${Math.min(value, 1) * 100}%` }}
        viewport={{ once: true }}
        transition={{ type: "spring", bounce: 0, duration: 1.1 }}
      />
    </div>
  );
}

export function Segmented<T extends string>({ value, onChange, options, id }: {
  value: T; onChange: (v: T) => void; options: { value: T; label: React.ReactNode }[]; id: string;
}) {
  return (
    <div role="tablist" className="glass inline-flex gap-1 rounded-full p-1">
      {options.map((o) => (
        <button
          key={o.value}
          role="tab"
          aria-selected={value === o.value}
          onClick={() => onChange(o.value)}
          className="press relative rounded-full px-4 py-1.5 text-sm font-semibold"
        >
          {value === o.value && <motion.span layoutId={id} className="absolute inset-0 rounded-full bg-fg" transition={spring} />}
          <span className={cx("relative transition-colors", value === o.value ? "text-bg" : "text-muted")}>{o.label}</span>
        </button>
      ))}
    </div>
  );
}

export function Avatar({ name, id, size = 40 }: { name: string; id: number; size?: number }) {
  const { lang } = usePrefs();
  const hue = (id * 47) % 360;
  const words = name.split(" ");
  const initials = lang === "fa" ? words[0][0] : words.map((w) => w[0]).slice(0, 2).join("");
  return (
    <span
      aria-hidden
      className="grid shrink-0 place-items-center rounded-full font-bold text-white shadow-[inset_0_1px_0_rgb(255_255_255/.4)]"
      style={{
        width: size,
        height: size,
        fontSize: size * 0.38,
        background: `linear-gradient(135deg, hsl(${hue} 90% 64%), hsl(${hue + 50} 85% 52%))`,
      }}
    >
      {initials}
    </span>
  );
}

export function ThemeToggle() {
  const { toggleTheme, t } = usePrefs();
  return (
    <button
      aria-label={t("theme_toggle")}
      title={t("theme_toggle")}
      onClick={(e) => toggleTheme(e.clientX, e.clientY)}
      className="press glass grid size-10 place-items-center rounded-full"
    >
      <Sun className="only-dark size-[18px]" />
      <Moon className="only-light size-[18px]" />
    </button>
  );
}

export function LangToggle() {
  const { lang, setLang, t } = usePrefs();
  return (
    <button
      onClick={() => setLang(lang === "fa" ? "en" : "fa")}
      lang={lang === "fa" ? "en" : "fa"}
      className="press glass inline-flex h-10 items-center gap-1.5 rounded-full px-3.5 text-sm font-semibold"
    >
      <Languages className="size-4" />
      {t("lang_switch")}
    </button>
  );
}

/** 7-day XP bars; bars that hit the goal glow with the brand gradient. */
export function Bars({ values, labels, goal }: { values: number[]; labels: string[]; goal: number }) {
  const { n } = usePrefs();
  const max = Math.max(goal, ...values, 1);
  return (
    <div className="flex h-36 items-stretch gap-2">
      {values.map((v, i) => (
        <div key={i} className="flex flex-1 flex-col items-center gap-1.5">
          <span className="text-[11px] font-semibold text-muted tabular-nums">{v ? n(v) : ""}</span>
          <div className="flex w-full flex-1 items-end">
            <motion.div
              className="w-full rounded-[10px]"
              style={{ background: v >= goal ? "var(--grad)" : "color-mix(in srgb, var(--brand) 28%, transparent)" }}
              initial={{ height: 0 }}
              animate={{ height: `${Math.max((v / max) * 100, v ? 6 : 3)}%` }}
              transition={{ ...spring, delay: 0.15 + i * 0.05 }}
            />
          </div>
          <span className={cx("text-xs", i === values.length - 1 ? "font-bold" : "text-muted")}>{labels[i]}</span>
        </div>
      ))}
    </div>
  );
}

/** Area chart with hover scrubbing. Time flows with reading direction (flipped in RTL). */
export function Area({ values, labels, format }: { values: number[]; labels: string[]; format: (v: number) => string }) {
  const { dir } = usePrefs();
  const [hover, setHover] = useState<number | null>(null);
  const id = useId();
  const W = 600, H = 180, max = Math.max(...values, 1) * 1.15;
  const pts = values.map((v, i) => [(i / (values.length - 1)) * W, H - (v / max) * H] as const);
  const line = pts.map(([x, y], i) => `${i ? "L" : "M"}${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
  const k = hover ?? values.length - 1;
  const at = (i: number) => `${(i / (values.length - 1)) * 100}%`;
  return (
    <div className="relative">
      <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" className="h-44 w-full overflow-visible" style={{ transform: dir === "rtl" ? "scaleX(-1)" : undefined }} aria-hidden>
        <defs>
          <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
            <stop stopColor="var(--brand)" stopOpacity=".45" />
            <stop offset="1" stopColor="var(--brand)" stopOpacity="0" />
          </linearGradient>
        </defs>
        <motion.path d={`${line} L${W},${H} L0,${H} Z`} fill={`url(#${id})`} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.8, delay: 0.3 }} />
        <motion.path d={line} fill="none" stroke="var(--brand)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" vectorEffect="non-scaling-stroke" initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 1.2, ease: [0.2, 0.8, 0.2, 1] }} />
      </svg>
      <div className="pointer-events-none absolute top-0 h-44 w-px bg-fg/20" style={{ insetInlineStart: at(k) }} />
      <div
        className="pointer-events-none absolute size-3.5 -translate-y-1/2 rounded-full border-[3px] border-bg bg-brand shadow-lg ltr:-translate-x-1/2 rtl:translate-x-1/2"
        style={{ insetInlineStart: at(k), top: `${(1 - values[k] / max) * 176}px` }}
      />
      <div className="glass pointer-events-none absolute -top-2 rounded-xl px-2.5 py-1 text-xs font-bold whitespace-nowrap ltr:-translate-x-1/2 rtl:translate-x-1/2" style={{ insetInlineStart: at(k) }}>
        {format(values[k])} · <span className="font-normal text-muted">{labels[k]}</span>
      </div>
      <div className="absolute inset-0 flex" onPointerLeave={() => setHover(null)}>
        {values.map((_, i) => (
          <div key={i} className="flex-1" onPointerEnter={() => setHover(i)} onPointerDown={() => setHover(i)} />
        ))}
      </div>
      <div className="mt-2 flex justify-between text-[11px] text-muted">
        <span>{labels[0]}</span>
        <span>{labels[Math.floor(labels.length / 2)]}</span>
        <span>{labels[labels.length - 1]}</span>
      </div>
    </div>
  );
}

export function Loader() {
  const { t } = usePrefs();
  return (
    <div className="grid min-h-[60dvh] place-items-center" role="status" aria-label={t("loading")}>
      <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1.1, ease: "linear" }}>
        <Mark size={40} />
      </motion.div>
    </div>
  );
}

export function ErrorState({ onRetry }: { onRetry: () => void }) {
  const { t } = usePrefs();
  return (
    <div className="grid min-h-[50dvh] place-items-center text-center">
      <div className="space-y-3">
        <p className="text-muted">{t("error")}</p>
        <button onClick={onRetry} className="press glass rounded-full px-5 py-2 font-semibold">{t("retry")}</button>
      </div>
    </div>
  );
}

/** Last-7-days narrow weekday labels in the active locale. */
export function weekdayLabels(locale: string, days = 7) {
  const f = new Intl.DateTimeFormat(locale, { weekday: "narrow" });
  return Array.from({ length: days }, (_, i) => f.format(new Date(Date.now() - (days - 1 - i) * 864e5)));
}
