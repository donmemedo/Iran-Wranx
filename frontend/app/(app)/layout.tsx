"use client";
import { House, LayoutDashboard, Trophy, User } from "lucide-react";
import { motion } from "motion/react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect } from "react";
import { ErrorState, LangToggle, Loader, Logo, ThemeToggle, cx, spring } from "@/components/ui";
import { ApiError, MeCtx, useApi, type Me } from "@/lib/api";
import { usePrefs } from "@/lib/prefs";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { data: me, error, reload } = useApi<Me>("/me");
  const path = usePathname();
  const { t } = usePrefs();

  useEffect(() => {
    if (error instanceof ApiError && error.status === 401) location.replace("/login");
  }, [error]);

  if (error && !(error instanceof ApiError && error.status === 401)) return <ErrorState onRetry={reload} />;
  if (!me) return <Loader />;

  const nav = [
    { href: "/home", icon: House, label: t("nav_today") },
    { href: "/leaderboard", icon: Trophy, label: t("nav_board") },
    ...(me.role === "manager" ? [{ href: "/dashboard", icon: LayoutDashboard, label: t("nav_dash") }] : []),
    { href: "/profile", icon: User, label: t("nav_profile") },
  ];

  return (
    <MeCtx.Provider value={{ me, reload }}>
      {path.startsWith("/learn") ? (
        children
      ) : (
        <div className="md:flex">
          <aside className="sticky top-0 hidden h-dvh w-64 shrink-0 p-4 md:block">
            <div className="glass flex h-full flex-col rounded-[28px] p-4">
              <Link href="/" className="mb-6 px-2 pt-1">
                <Logo />
              </Link>
              <nav className="flex flex-col gap-1">
                {nav.map(({ href, icon: Icon, label }) => {
                  const on = path.startsWith(href);
                  return (
                    <Link key={href} href={href} className={cx("press relative flex items-center gap-3 rounded-2xl px-3 py-2.5 font-semibold", !on && "text-muted hover:text-fg")}>
                      {on && <motion.span layoutId="side-pill" className="absolute inset-0 rounded-2xl bg-fg/[.07]" transition={spring} />}
                      <Icon className={cx("relative size-5", on && "text-brand")} strokeWidth={on ? 2.4 : 2} />
                      <span className="relative">{label}</span>
                    </Link>
                  );
                })}
              </nav>
              <div className="mt-auto flex items-center gap-2">
                <ThemeToggle />
                <LangToggle />
              </div>
            </div>
          </aside>

          <header className="flex items-center justify-between px-4 pt-[max(1rem,env(safe-area-inset-top))] md:hidden">
            <Link href="/">
              <Logo />
            </Link>
            <div className="flex gap-2">
              <LangToggle />
              <ThemeToggle />
            </div>
          </header>

          <main className="mx-auto w-full max-w-6xl flex-1 px-4 pt-5 pb-32 md:px-8 md:pt-8 md:pb-12">{children}</main>

          <nav className="glass fixed inset-x-3 bottom-[max(.75rem,env(safe-area-inset-bottom))] z-40 flex rounded-[26px] p-1.5 md:hidden">
            {nav.map(({ href, icon: Icon, label }) => {
              const on = path.startsWith(href);
              return (
                <Link key={href} href={href} className={cx("press relative flex flex-1 flex-col items-center gap-0.5 rounded-[20px] py-2 text-[11px] font-semibold", !on && "text-muted")}>
                  {on && <motion.span layoutId="tab-pill" className="absolute inset-0 rounded-[20px] bg-fg/[.07]" transition={spring} />}
                  <Icon className={cx("relative size-[22px]", on && "text-brand")} strokeWidth={on ? 2.4 : 2} />
                  <span className="relative">{label}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      )}
    </MeCtx.Provider>
  );
}
