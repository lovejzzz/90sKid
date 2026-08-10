export const siteBasePath = process.env.NEXT_PUBLIC_BASE_PATH ?? "";
export const archiveMediaOrigin = "https://cdn.jsdelivr.net/gh/lovejzzz/90sKid@e85c07cf32ff732bffd97495b308a46120ee1c8b/public";

export function withBasePath(path: string) {
  // The growing, immutable version archive is served from a commit-pinned CDN
  // mirror. Keeping one canonical byte copy prevents Sites
  // deployment bundles from duplicating hundreds of megabytes of lossless
  // stills and grain-tuned hover videos; no proxy is recompressed here.
  if (path.startsWith("/versions/v44-")) {
    return siteBasePath ? `${siteBasePath}${path}` : path;
  }
  if (path.startsWith("/versions/")) return `${archiveMediaOrigin}${path}`;
  if (!path.startsWith("/") || !siteBasePath) return path;
  return `${siteBasePath}${path}`;
}
