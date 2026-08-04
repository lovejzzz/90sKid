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
    description: "V27：以完整中性曝光尺度修正时期2K扫描灰轴，同时锁定Rec.709亮度、黑位、Gamma与V26乳剂的5.7K 12-bit双母版。",
    openGraph: {
      title: "5279 Emulsion Project",
      description: "V27：35mm 5279乳剂、2383放映与完整灰轴校准的时期2K扫描双观察链。",
      type: "website",
      locale: "zh_CN",
      images: [{ url: "/versions/v27-t020-projection.jpg", width: 2560, height: 1920, alt: "5279 Emulsion Project · V27 2383 Projection Monitor Reference" }],
    },
    twitter: {
      card: "summary_large_image",
      title: "5279 Emulsion Project",
      description: "V27：35mm 5279乳剂、2383放映与完整灰轴校准的时期2K扫描双观察链。",
      images: ["/versions/v27-t020-projection.jpg"],
    },
  };
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="zh-CN"><body className={`${geistSans.variable} ${geistMono.variable}`}><LanguageProvider>{children}</LanguageProvider></body></html>;
}
