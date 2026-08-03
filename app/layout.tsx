import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { headers } from "next/headers";
import "./globals.css";

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
    description: "V24：从GH7 ProRes RAW重建Kodak VISION 500T 5279乳剂、35mm颗粒频谱、2383放映与时期2K扫描。",
    openGraph: {
      title: "5279 Emulsion Project",
      description: "V24：35mm颗粒频谱、综合色分离、2383氙灯放映与时期2K扫描。",
      type: "website",
      locale: "zh_CN",
      images: [{ url: "/og-v24.jpg", width: 1659, height: 948, alt: "5279 Emulsion Project · V24 35mm Texture" }],
    },
    twitter: {
      card: "summary_large_image",
      title: "5279 Emulsion Project",
      description: "V24：35mm颗粒频谱、综合色分离、2383氙灯放映与时期2K扫描。",
      images: ["/og-v24.jpg"],
    },
  };
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="zh-CN"><body className={`${geistSans.variable} ${geistMono.variable}`}>{children}</body></html>;
}
