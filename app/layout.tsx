import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { LanguageProvider } from "./i18n";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export function generateMetadata(): Metadata {
  const isGitHubPages = process.env.GITHUB_PAGES === "true";
  const siteUrl = isGitHubPages ? "https://lovejzzz.github.io/90sKid/" : "https://emulsion-5279.skylab.chatgpt.site/";
  const socialImageUrl = new URL("versions/v34-t031-projection.jpg", siteUrl).toString();
  return {
    metadataBase: new URL(siteUrl),
    title: { default: "5279 Emulsion Project", template: "%s · 5279 Emulsion Project" },
    description: "V34 audits the complete 5279 pipeline: processed-stock MTF owns developer adjacency once and each 12-bit master receives one ProRes generation.",
    openGraph: {
      title: "5279 Emulsion Project",
      description: "Processed-stock 5279 MTF, single-generation 12-bit delivery, and a documented colour/grain evidence boundary.",
      type: "website",
      locale: "en_US",
      images: [{ url: socialImageUrl, width: 2560, height: 1920, alt: "5279 Emulsion Project · V34 processed-MTF baseline" }],
    },
    twitter: {
      card: "summary_large_image",
      title: "5279 Emulsion Project",
      description: "V34 gives processed-stock MTF and delivery encoding one authoritative pass each.",
      images: [socialImageUrl],
    },
  };
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body className={`${geistSans.variable} ${geistMono.variable}`}><LanguageProvider>{children}</LanguageProvider></body></html>;
}
