import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { LanguageProvider } from "./i18n";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export function generateMetadata(): Metadata {
  const isGitHubPages = process.env.GITHUB_PAGES === "true";
  const siteUrl = isGitHubPages ? "https://lovejzzz.github.io/90sKid/" : "https://emulsion-5279.skylab.chatgpt.site/";
  const socialImageUrl = new URL("og-v31.png", siteUrl).toString();
  return {
    metadataBase: new URL(siteUrl),
    title: { default: "5279 Emulsion Project", template: "%s · 5279 Emulsion Project" },
    description: "V31 corrects the chroma/lightness coupling in the normal-process 5279-to-2383 observer while retaining the accepted film texture, black, gamma and official Kodak LAD calibration.",
    openGraph: {
      title: "5279 Emulsion Project",
      description: "Normal ECN-2/ECP-2D colour, three native-resolution GH7 scenes and a 5279→2383 observer without an accidental retained-silver signature.",
      type: "website",
      locale: "en_US",
      images: [{ url: socialImageUrl, width: 1536, height: 1024, alt: "5279 Emulsion Project · V31 Normal-Process Colour" }],
    },
    twitter: {
      card: "summary_large_image",
      title: "5279 Emulsion Project",
      description: "Normal-process colour without an accidental retained-silver signature; Kodak LAD and organic 5279 texture retained.",
      images: [socialImageUrl],
    },
  };
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body className={`${geistSans.variable} ${geistMono.variable}`}><LanguageProvider>{children}</LanguageProvider></body></html>;
}
