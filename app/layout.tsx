import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { LanguageProvider } from "./i18n";
import { withBasePath } from "./basePath";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export function generateMetadata(): Metadata {
  const isGitHubPages = process.env.GITHUB_PAGES === "true";
  const siteUrl = isGitHubPages ? "https://lovejzzz.github.io/90sKid/" : "https://emulsion-5279.skylab.chatgpt.site/";
  return {
    metadataBase: new URL(siteUrl),
    title: { default: "5279 Emulsion Project", template: "%s · 5279 Emulsion Project" },
    description: "V29：用完整165帧GH7 ProRes RAW验证5279有限位点乳剂、2383放映与时期2K扫描；5.7K 12-bit双母版保留原音和时间码。",
    openGraph: {
      title: "5279 Emulsion Project",
      description: "V29：完整165帧35mm 5279乳剂运动验证、2383放映与时期2K扫描双观察链。",
      type: "website",
      locale: "en_US",
      images: [{ url: withBasePath("/og-v29.png"), width: 1733, height: 908, alt: "5279 Emulsion Project · V29 Full-Motion Validation" }],
    },
    twitter: {
      card: "summary_large_image",
      title: "5279 Emulsion Project",
      description: "V29：完整165帧35mm 5279乳剂运动验证、2383放映与时期2K扫描双观察链。",
      images: [withBasePath("/og-v29.png")],
    },
  };
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body className={`${geistSans.variable} ${geistMono.variable}`}><LanguageProvider>{children}</LanguageProvider></body></html>;
}
