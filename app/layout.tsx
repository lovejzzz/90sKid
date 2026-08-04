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
    description: "V26：曝光相关的5279快/中/慢乳剂颗粒频谱，锁定Rec.709色彩、黑位与Gamma的5.7K 12-bit双母版。",
    openGraph: {
      title: "5279 Emulsion Project",
      description: "V26：35mm 5279曝光相关颗粒频谱与标准化Rec.709双观察链。",
      type: "website",
      locale: "zh_CN",
      images: [{ url: "/versions/v26-t020-projection.jpg", width: 2560, height: 1920, alt: "5279 Emulsion Project · V26 2383 Projection Monitor Reference" }],
    },
    twitter: {
      card: "summary_large_image",
      title: "5279 Emulsion Project",
      description: "V26：35mm 5279曝光相关颗粒频谱与标准化Rec.709双观察链。",
      images: ["/versions/v26-t020-projection.jpg"],
    },
  };
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="zh-CN"><body className={`${geistSans.variable} ${geistMono.variable}`}>{children}</body></html>;
}
