import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { LanguageProvider } from "./i18n";
import { archiveMediaOrigin } from "./basePath";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export function generateMetadata(): Metadata {
  const isGitHubPages = process.env.GITHUB_PAGES === "true";
  const siteUrl = isGitHubPages ? "https://lovejzzz.github.io/90sKid/" : "https://emulsion-5279.skylab.chatgpt.site/";
  const socialImageUrl = new URL("versions/v41-t031-projection.jpg", `${archiveMediaOrigin}/`).toString();
  return {
    metadataBase: new URL(siteUrl),
    title: { default: "5279 Emulsion Project", template: "%s · 5279 Emulsion Project" },
    description: "V41 applies a two-chart-bounded chroma transport while freezing the V40 density, grain, black, contrast and gamma model.",
    openGraph: {
      title: "5279 Emulsion Project",
      description: "A quality-first 5279 reconstruction with auditable finite-site identities and display-consistent native 12-bit delivery.",
      type: "website",
      locale: "en_US",
      images: [{ url: socialImageUrl, width: 2560, height: 1920, alt: "5279 Emulsion Project · V41 chart-bounded colour transport" }],
    },
    twitter: {
      card: "summary_large_image",
      title: "5279 Emulsion Project",
      description: "V41 moves a repeated chart residual only 12.5%, preserves luminance, and keeps the film model free of creative grading.",
      images: [socialImageUrl],
    },
  };
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body className={`${geistSans.variable} ${geistMono.variable}`}><LanguageProvider>{children}</LanguageProvider></body></html>;
}
