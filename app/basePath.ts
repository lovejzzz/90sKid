export const siteBasePath = process.env.NEXT_PUBLIC_BASE_PATH ?? "";
export const archiveMediaOrigin = "https://cdn.jsdelivr.net/gh/lovejzzz/90sKid@e85c07cf32ff732bffd97495b308a46120ee1c8b/public";
const v26HoverOrigin = "https://cdn.jsdelivr.net/gh/lovejzzz/90sKid@16d14d8909d8e48ad11499f309844dda1ab3954c/public";
const v27HoverOrigin = "https://cdn.jsdelivr.net/gh/lovejzzz/90sKid@a23540fbf1ad47060cf8b9677c85d148b1b7ad48/public";

export function withBasePath(path: string) {
  // The growing, immutable version archive is served from a commit-pinned CDN
  // mirror. Keeping one canonical byte copy prevents Sites
  // deployment bundles from duplicating hundreds of megabytes of lossless
  // stills and grain-tuned hover videos; no proxy is recompressed here.
  if (path.startsWith("/versions/v46-") || path.startsWith("/versions/v45-") || path.startsWith("/versions/v44-")) {
    return siteBasePath ? `${siteBasePath}${path}` : path;
  }
  // V26/V27 hover movies were intentionally removed before the later archive
  // commit. Pin those two generations to the immutable release trees that
  // actually contain them; their stills remain present in the common archive.
  if (path.startsWith("/versions/v26-") && path.endsWith(".mp4")) {
    return `${v26HoverOrigin}${path}`;
  }
  if (path.startsWith("/versions/v27-") && path.endsWith(".mp4")) {
    return `${v27HoverOrigin}${path}`;
  }
  if (path.startsWith("/versions/")) return `${archiveMediaOrigin}${path}`;
  if (!path.startsWith("/") || !siteBasePath) return path;
  return `${siteBasePath}${path}`;
}
