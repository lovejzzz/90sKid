import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { headers } from "next/headers";
import "./globals.css";
import { LanguageProvider } from "./i18n";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export async function generateMetadata(): Promise<Metadata> {
  const requestHeaders = await headers();
  const host = requestHeaders.get("x-forwarded-host") ?? requestHeaders.get("host") ?? "localhost:3001";
  const forwardedProtocol = requestHeaders.get("x-forwarded-proto");
  const protocol = forwardedProtocol ?? (host.startsWith("localhost") ? "http" : "https");

  return {
    metadataBase: new URL(`${protocol}://${host}`),
    title: { default: "5279 Emulsion Project", template: "%s · 5279 Emulsion Project" },
    description: "V29：用完整165帧GH7 ProRes RAW验证5279有限位点乳剂、2383放映与时期2K扫描；5.7K 12-bit双母版保留原音和时间码。",
    openGraph: {
      title: "5279 Emulsion Project",
      description: "V29：完整165帧35mm 5279乳剂运动验证、2383放映与时期2K扫描双观察链。",
      type: "website",
      locale: "zh_CN",
      images: [{ url: "/og-v29.png", width: 1733, height: 908, alt: "5279 Emulsion Project · V29 Full-Motion Validation" }],
    },
    twitter: {
      card: "summary_large_image",
      title: "5279 Emulsion Project",
      description: "V29：完整165帧35mm 5279乳剂运动验证、2383放映与时期2K扫描双观察链。",
      images: ["/og-v29.png"],
    },
  };
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="zh-CN"><body className={`${geistSans.variable} ${geistMono.variable}`}><LanguageProvider>{children}</LanguageProvider></body></html>;
}
