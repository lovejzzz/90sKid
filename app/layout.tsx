import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { LanguageProvider } from "./i18n";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export function generateMetadata(): Metadata {
  const isGitHubPages = process.env.GITHUB_PAGES === "true";
  const siteUrl = isGitHubPages ? "https://lovejzzz.github.io/90sKid/" : "https://emulsion-5279.skylab.chatgpt.site/";
  const socialImageUrl = new URL("og-v29.png", siteUrl).toString();
  return {
    metadataBase: new URL(siteUrl),
    title: { default: "5279 Emulsion Project", template: "%s · 5279 Emulsion Project" },
    description: "V29 validates the 5279 finite-site emulsion model across all 165 GH7 ProRes RAW frames, delivering native 5.7K 12-bit projection and period-scan masters.",
    openGraph: {
      title: "5279 Emulsion Project",
      description: "A complete 165-frame validation of the 35 mm 5279 emulsion model, with 2383 projection and period 2K scan viewing chains.",
      type: "website",
      locale: "en_US",
      images: [{ url: socialImageUrl, width: 1733, height: 908, alt: "5279 Emulsion Project · V29 Full-Motion Validation" }],
    },
    twitter: {
      card: "summary_large_image",
      title: "5279 Emulsion Project",
      description: "A complete 165-frame validation of the 35 mm 5279 emulsion model, with 2383 projection and period 2K scan viewing chains.",
      images: [socialImageUrl],
    },
  };
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body className={`${geistSans.variable} ${geistMono.variable}`}><LanguageProvider>{children}</LanguageProvider></body></html>;
}
