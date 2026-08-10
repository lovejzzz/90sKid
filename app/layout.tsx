import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { LanguageProvider } from "./i18n";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export function generateMetadata(): Metadata {
  const isGitHubPages = process.env.GITHUB_PAGES === "true";
  const siteUrl = isGitHubPages ? "https://lovejzzz.github.io/90sKid/" : "https://emulsion-5279.skylab.chatgpt.site/";
  const socialImageUrl = new URL("og-v45.png", siteUrl).toString();
  return {
    metadataBase: new URL(siteUrl),
    title: { default: "5279 Emulsion Project", template: "%s · 5279 Emulsion Project" },
    description: "V45 integrates Kodak 2383 through the official CIE 1931 2-degree 1 nm observer while freezing the accepted V42 image model.",
    openGraph: {
      title: "5279 Emulsion Project",
      description: "An evidence-bounded 5279 reconstruction with official 1 nm spectral observation, scale-honest review and native 12-bit delivery.",
      type: "website",
      locale: "en_US",
      images: [{ url: socialImageUrl, width: 1731, height: 909, alt: "Grain is the image · V45 official CIE observer · V42 image baseline" }],
    },
    twitter: {
      card: "summary_large_image",
      title: "5279 Emulsion Project",
      description: "V45 replaces the analytical observer approximation with official CIE 1 nm data; V42 remains the image baseline.",
      images: [socialImageUrl],
    },
  };
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body className={`${geistSans.variable} ${geistMono.variable}`}><LanguageProvider>{children}</LanguageProvider></body></html>;
}
