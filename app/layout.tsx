import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { LanguageProvider } from "./i18n";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export function generateMetadata(): Metadata {
  const isGitHubPages = process.env.GITHUB_PAGES === "true";
  const siteUrl = isGitHubPages ? "https://lovejzzz.github.io/90sKid/" : "https://emulsion-5279.skylab.chatgpt.site/";
  const socialImageUrl = new URL("og-v33.png", siteUrl).toString();
  return {
    metadataBase: new URL(siteUrl),
    title: { default: "5279 Emulsion Project", template: "%s · 5279 Emulsion Project" },
    description: "V33 freezes the accepted 5279 image while separating As Shot 0 stop from virtual film EI and adding black, toe, gamma, timecode and memory-safety gates.",
    openGraph: {
      title: "5279 Emulsion Project",
      description: "The accepted 5279→2383 image, frozen while camera exposure, black, toe, gamma and delivery boundaries become measurable.",
      type: "website",
      locale: "en_US",
      images: [{ url: socialImageUrl, width: 1536, height: 1024, alt: "5279 Emulsion Project · V33 Input and Tone Boundary" }],
    },
    twitter: {
      card: "summary_large_image",
      title: "5279 Emulsion Project",
      description: "V33 freezes the accepted 5279 image and measures camera exposure, black, toe, gamma and delivery boundaries.",
      images: [socialImageUrl],
    },
  };
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body className={`${geistSans.variable} ${geistMono.variable}`}><LanguageProvider>{children}</LanguageProvider></body></html>;
}
