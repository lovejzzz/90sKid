import type { NextConfig } from "next";

const isGitHubPages = process.env.GITHUB_PAGES === "true";
const basePath = isGitHubPages ? "/90sKid" : "";

const nextConfig: NextConfig = {
  output: isGitHubPages ? "export" : undefined,
  basePath,
  assetPrefix: basePath,
  trailingSlash: isGitHubPages,
  images: { unoptimized: true },
};

export default nextConfig;
