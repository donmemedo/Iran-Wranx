import "@fontsource-variable/vazirmatn";
import "./globals.css";
import type { Metadata, Viewport } from "next";
import { cookies } from "next/headers";
import { Prefs } from "@/lib/prefs";

export const metadata: Metadata = {
  title: "رنکسیار | Ranksyar",
  description: "یادگیری ۵ دقیقه‌ای، تکرار فاصله‌دار و بازی‌وارسازی برای تیم‌های سازمانی — Five-minute microlearning for teams.",
};

export const viewport: Viewport = {
  viewportFit: "cover",
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f2f2f7" },
    { media: "(prefers-color-scheme: dark)", color: "#05050b" },
  ],
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const c = await cookies();
  const lang = c.get("lang")?.value === "en" ? "en" : "fa";
  const saved = c.get("theme")?.value;
  const theme = saved === "light" || saved === "dark" ? saved : undefined;
  return (
    <html lang={lang} dir={lang === "fa" ? "rtl" : "ltr"} data-theme={theme} suppressHydrationWarning>
      <body>
        <div className="aurora" aria-hidden>
          <i />
          <i />
          <i />
        </div>
        <Prefs lang={lang} theme={theme ?? "system"}>
          {children}
        </Prefs>
      </body>
    </html>
  );
}
