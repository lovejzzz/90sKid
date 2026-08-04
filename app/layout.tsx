import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { LanguageProvider } from "./i18n";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export function generateMetadata(): Metadata {
  const isGitHubPages = process.env.GITHUB_PAGES === "true";
  const siteUrl = isGitHubPages ? "https://lovejzzz.github.io/90sKid/" : "https://emulsion-5279.skylab.chatgpt.site/";
  const socialImageUrl = new URL("og-v30.png", siteUrl).toString();
  return {
    metadataBase: new URL(siteUrl),
    title: { default: "5279 Emulsion Project", template: "%s · 5279 Emulsion Project" },
    description: "V30 corrects the 2383 projection colour with Kodak's official LAD aims and compares three GH7 ProRes RAW scenes through camera, projection and period-scan baselines.",
    openGraph: {
      title: "5279 Emulsion Project",
      description: "Three native-resolution GH7 scenes compare an official camera baseline with 5279→2383 projection and period 2K scan viewing chains.",
      type: "website",
      locale: "en_US",
      images: [{ url: socialImageUrl, width: 1733, height: 908, alt: "5279 Emulsion Project · V30 Three-Scene Colour Evidence" }],
    },
    twitter: {
      card: "summary_large_image",
      title: "5279 Emulsion Project",
      description: "Official Kodak LAD aims, three GH7 scenes and matched camera / projection / period-scan baselines.",
      images: [socialImageUrl],
    },
  };
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body className={`${geistSans.variable} ${geistMono.variable}`}><LanguageProvider>{children}</LanguageProvider></body></html>;
}
