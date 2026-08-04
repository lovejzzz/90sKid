export const siteBasePath = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

export function withBasePath(path: string) {
  if (!path.startsWith("/") || !siteBasePath) return path;
  return `${siteBasePath}${path}`;
}
