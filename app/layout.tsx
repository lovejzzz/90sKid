import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { LanguageProvider } from "./i18n";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export function generateMetadata(): Metadata {
  const isGitHubPages = process.env.GITHUB_PAGES === "true";
  const siteUrl = isGitHubPages ? "https://lovejzzz.github.io/90sKid/" : "https://emulsion-5279.skylab.chatgpt.site/";
  const socialImageUrl = new URL("og-v48.png", siteUrl).toString();
  return {
    metadataBase: new URL(siteUrl),
    title: { default: "5279 Emulsion Project", template: "%s · 5279 Emulsion Project" },
    description: "An evidence-bounded Kodak 5279 reconstruction. V48 returns projection and scan to separate first-principles observer ownership.",
    openGraph: {
      title: "5279 Emulsion Project",
      description: "V48 is a first-principles Kodak 5279 / 2383 baseline with one negative and two explicit observers.",
      type: "website",
      locale: "en_US",
      images: [{ url: socialImageUrl, width: 1731, height: 909, alt: "Grain is the image · V48 first-principles Kodak baseline" }],
    },
    twitter: {
      card: "summary_large_image",
      title: "5279 Emulsion Project",
      description: "V48 is the current visual release: one 5279 negative, with explicit 2383 projection and Cineon scan observers.",
      images: [socialImageUrl],
    },
  };
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body className={`${geistSans.variable} ${geistMono.variable}`}><LanguageProvider>{children}</LanguageProvider></body></html>;
}
