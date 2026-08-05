export const siteBasePath = process.env.NEXT_PUBLIC_BASE_PATH ?? "";
export const archiveMediaOrigin = "https://lovejzzz.github.io/90sKid";

export function withBasePath(path: string) {
  // The growing, immutable version archive is served from the public GitHub
  // Pages release mirror. Keeping one canonical byte copy prevents Sites
  // deployment bundles from duplicating hundreds of megabytes of lossless
  // stills and grain-tuned hover videos; no proxy is recompressed here.
  if (path.startsWith("/versions/")) return `${archiveMediaOrigin}${path}`;
  if (!path.startsWith("/") || !siteBasePath) return path;
  return `${siteBasePath}${path}`;
}
