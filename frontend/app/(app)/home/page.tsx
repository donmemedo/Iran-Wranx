"use client";
import { ArrowRight, Clock, Flame, Lock, Play, Trophy } from "lucide-react";
import { motion } from "motion/react";
import Link from "next/link";
import {
  BADGE_HUES, BADGE_ICONS, Bar, Bars, Card, Num, Ring, TRACK_ICONS, bouncy, cx, spot, weekdayLabels,
} from "@/components/ui";
import { useApi, useMe, type Track } from "@/lib/api";
import type { Key } from "@/lib/i18n";
import { usePrefs } from "@/lib/prefs";

export default function Home() {
  const { me } = useMe();
  const { t, tn, tl, n, locale } = usePrefs();
  const { data: tracks } = useApi<Track[]>("/tracks");
  const goal = me.today_xp / me.daily_goal;
  const date = new Intl.DateTimeFormat(locale, { weekday: "long", day: "numeric", month: "long" }).format(new Date());

  return (
    <div className="space-y-5">
      <motion.header initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
        <p className="text-sm text-muted">{date}</p>
        <h1 className="display text-3xl md:text-[2.75rem]">
          {t("hi")} {tl(me.name).split(" ")[0]} <motion.span className="inline-block origin-[70%_70%]" animate={{ rotate: [0, 16, -8, 14, 0] }} transition={{ duration: 1.4, delay: 0.4 }}>👋</motion.span>
        </h1>
      </motion.header>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="relative overflow-hidden lg:col-span-2">
          <div className="absolute -top-24 size-72 rounded-full bg-[#ff4f8b] opacity-25 blur-3xl ltr:-right-16 rtl:-left-16" aria-hidden />
          <div className="relative flex flex-col items-center gap-6 sm:flex-row">
            <Ring value={goal} size={168} stroke={16}>
              <div>
                <div className="display text-4xl">
                  <Num value={Math.min(goal, 1)} format={{ style: "percent" }} />
                </div>
                <div className="text-xs text-muted">{t("h_goal")}</div>
              </div>
            </Ring>
            <div className="flex-1 space-y-4 text-center sm:text-start">
              <div>
                <h2 className="display text-2xl">{goal >= 1 ? t("h_done") : t("h_start")}</h2>
                <p className="mt-1 text-muted">
                  {me.due ? tn("h_due", me.due) : t("h_fresh")} · {n(me.today_xp)}/{n(me.daily_goal)} {t("xp")}
                </p>
              </div>
              <Link href="/learn" className="press btn-grad inline-flex h-14 items-center gap-3 rounded-full ps-3 pe-6 text-lg font-bold">
                <span className="grid size-9 place-items-center rounded-full bg-white/25">
                  <Play className="size-4 fill-current rtl:rotate-180" />
                </span>
                {t("h_start")}
              </Link>
            </div>
          </div>
        </Card>

        <Card delay={0.05} className="flex flex-col gap-5">
          <div className="flex items-center gap-4">
            <motion.div
              className="grid size-16 place-items-center rounded-2xl bg-gradient-to-br from-[#ffb020] to-[#ff4f8b] text-white shadow-[0_12px_30px_-10px_#ff6a3d]"
              initial={{ scale: 0.6, rotate: -12 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ ...bouncy, delay: 0.2 }}
            >
              <Flame className="size-8 fill-white/30" />
            </motion.div>
            <div>
              <div className="display text-4xl"><Num value={me.streak} /></div>
              <div className="text-sm text-muted">{t("day_streak")}</div>
            </div>
          </div>
          <div>
            <div className="mb-2 flex justify-between text-sm">
              <span className="font-bold">{t("h_level")} {n(me.level)}</span>
              <span className="text-muted">{tn("h_to_next", Math.round(me.level_xp * (1 - me.level_progress)))}</span>
            </div>
            <Bar value={me.level_progress} className="h-2.5" />
          </div>
          <Link href="/leaderboard" className="press lift mt-auto flex items-center gap-3 rounded-2xl bg-fg/[.04] p-3">
            <Trophy className="size-5 text-warn" />
            <span className="flex-1 text-sm">{t("h_rank")}</span>
            <span className="font-bold">#{n(me.rank)}</span>
            <span className="text-xs text-muted">{tn("h_of", me.rank_of)}</span>
          </Link>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card delay={0.1}>
          <div className="mb-3 flex items-baseline justify-between">
            <h3 className="font-bold">{t("h_week")}</h3>
            <span className="text-sm text-muted">{n(me.week.reduce((a, b) => a + b, 0))} {t("xp")}</span>
          </div>
          <Bars values={me.week} labels={weekdayLabels(locale)} goal={me.daily_goal} />
        </Card>
        <Card delay={0.15} className="lg:col-span-2">
          <h3 className="mb-4 font-bold">{t("h_badges")}</h3>
          <div className="no-scrollbar -mx-1 flex gap-3 overflow-x-auto px-1 pb-1">
            {me.badges.map((b, i) => {
              const Icon = BADGE_ICONS[b.code as keyof typeof BADGE_ICONS];
              const hue = BADGE_HUES[b.code as keyof typeof BADGE_HUES];
              return (
                <motion.div
                  key={b.code}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ ...bouncy, delay: 0.25 + i * 0.06 }}
                  className={cx("flex w-32 shrink-0 flex-col items-center gap-2 rounded-2xl p-3 text-center", b.day ? "bg-fg/[.04]" : "opacity-45")}
                >
                  <div
                    className="relative grid size-14 place-items-center rounded-full text-white"
                    style={{ background: b.day ? `linear-gradient(135deg, ${hue}, color-mix(in srgb, ${hue} 55%, #fff))` : "var(--line)", boxShadow: b.day ? `0 10px 24px -10px ${hue}` : undefined }}
                  >
                    {b.day ? <Icon className="size-6" /> : <Lock className="size-5 text-muted" />}
                  </div>
                  <div className="text-sm leading-tight font-bold">{t(`b_${b.code}` as Key)}</div>
                  <div className="text-[11px] leading-snug text-muted">{t(`b_${b.code}_d` as Key)}</div>
                </motion.div>
              );
            })}
          </div>
        </Card>
      </div>

      <section>
        <h2 className="mb-3 text-xl font-bold">{t("h_tracks")}</h2>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {(tracks ?? Array(4).fill(null)).map((tr: Track | null, i) =>
            tr ? <TrackCard key={tr.id} tr={tr} i={i} /> : <div key={i} className="h-56 animate-pulse rounded-[28px] bg-fg/[.05]" />,
          )}
        </div>
      </section>
    </div>
  );
}

function TrackCard({ tr, i }: { tr: Track; i: number }) {
  const { t, tl, n } = usePrefs();
  const Icon = TRACK_ICONS[tr.icon as keyof typeof TRACK_ICONS];
  return (
    <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ type: "spring", bounce: 0, duration: 0.5, delay: 0.2 + i * 0.06 }}>
      <Link
        href={`/learn?track=${tr.id}`}
        onPointerMove={spot}
        style={{ "--spot": tr.color } as React.CSSProperties}
        className="spot lift glass press group flex h-full flex-col gap-4 rounded-[28px] p-5"
      >
        <div className="flex items-start justify-between">
          <div className="grid size-12 place-items-center rounded-2xl text-white" style={{ background: tr.color, boxShadow: `0 12px 28px -12px ${tr.color}` }}>
            <Icon className="size-6" />
          </div>
          <Ring value={tr.mastery} size={48} stroke={5} color={tr.color}>
            <span className="text-[11px] font-bold">{n(Math.round(tr.mastery * 100))}</span>
          </Ring>
        </div>
        <div className="flex-1">
          <h3 className="text-lg leading-snug font-bold">{tl(tr.title)}</h3>
          <p className="mt-1 text-sm text-muted">{tl(tr.descr)}</p>
        </div>
        <div className="flex items-center gap-3 text-xs text-muted">
          <span>{n(tr.lessons)} {t("lessons")}</span>
          <span className="inline-flex items-center gap-1"><Clock className="size-3.5" />{n(tr.minutes)} {t("minutes")}</span>
          <ArrowRight className="ms-auto size-4 transition-transform group-hover:translate-x-1 rtl:rotate-180 rtl:group-hover:-translate-x-1" style={{ color: tr.color }} />
        </div>
      </Link>
    </motion.div>
  );
}
