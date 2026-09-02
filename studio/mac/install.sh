#!/bin/bash
# Install "5279 Studio.app" into ~/Applications on macOS.
#
#   curl -fsSL https://raw.githubusercontent.com/lovejzzz/90sKid/claude/film-texture-video-app-axqm4s/studio/mac/install.sh | bash
#
# The script fetches only the studio/ directory of the repository, assembles
# the app bundle, builds its icon and opens it. The app installs its Python
# dependencies on first launch.

set -euo pipefail

REPO="lovejzzz/90sKid"
BRANCH="${FILM5279_BRANCH:-claude/film-texture-video-app-axqm4s}"
APP_DIR="$HOME/Applications"
APP="$APP_DIR/5279 Studio.app"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "▸ 5279 Studio installer"
echo "  repository: $REPO  branch: $BRANCH"

fetch_with_git() {
  command -v git >/dev/null 2>&1 || return 1
  git clone -q --depth 1 --filter=blob:none --sparse -b "$BRANCH" "https://github.com/$REPO.git" "$TMP/src" 2>/dev/null || return 1
  (cd "$TMP/src" && git sparse-checkout set studio -q 2>/dev/null) || return 1
  [ -f "$TMP/src/studio/app.py" ]
}

fetch_with_tarball() {
  local url="https://codeload.github.com/$REPO/tar.gz/refs/heads/$BRANCH"
  echo "  downloading source archive…"
  curl -fsSL "$url" -o "$TMP/src.tgz"
  mkdir -p "$TMP/src"
  tar -xzf "$TMP/src.tgz" -C "$TMP/src" --strip-components=1 '*/studio/*' '*/studio' 2>/dev/null \
    || tar -xzf "$TMP/src.tgz" -C "$TMP/src" --strip-components=1
  [ -f "$TMP/src/studio/app.py" ]
}

if fetch_with_git; then
  echo "  fetched with git (sparse)"
elif fetch_with_tarball; then
  echo "  fetched archive"
else
  echo "✗ could not download the studio sources" >&2
  exit 1
fi

SRC="$TMP/src/studio"
mkdir -p "$APP_DIR"
rm -rf "$APP"
cp -R "$SRC/mac/app-template" "$APP"
mkdir -p "$APP/Contents/Resources"
cp -R "$SRC" "$APP/Contents/Resources/studio"
rm -rf "$APP/Contents/Resources/studio/cache" "$APP/Contents/Resources/studio/work"
chmod +x "$APP/Contents/MacOS/5279Studio"

# Icon: PNG -> .icns with the system tools.
ICONSET="$TMP/AppIcon.iconset"
mkdir -p "$ICONSET"
for size in 16 32 64 128 256 512 1024; do
  sips -z "$size" "$size" "$SRC/mac/icon.png" --out "$ICONSET/icon_${size}x${size}.png" >/dev/null 2>&1 || true
done
cp "$ICONSET/icon_32x32.png" "$ICONSET/icon_16x16@2x.png" 2>/dev/null || true
cp "$ICONSET/icon_64x64.png" "$ICONSET/icon_32x32@2x.png" 2>/dev/null || true
cp "$ICONSET/icon_256x256.png" "$ICONSET/icon_128x128@2x.png" 2>/dev/null || true
cp "$ICONSET/icon_512x512.png" "$ICONSET/icon_256x256@2x.png" 2>/dev/null || true
cp "$ICONSET/icon_1024x1024.png" "$ICONSET/icon_512x512@2x.png" 2>/dev/null || true
rm -f "$ICONSET/icon_64x64.png" "$ICONSET/icon_1024x1024.png"
iconutil -c icns "$ICONSET" -o "$APP/Contents/Resources/AppIcon.icns" 2>/dev/null || cp "$SRC/mac/icon.png" "$APP/Contents/Resources/AppIcon.png"

xattr -dr com.apple.quarantine "$APP" 2>/dev/null || true
touch "$APP"
# A previous, interrupted setup must not make the launcher think it already failed.
rm -f "$HOME/Library/Application Support/5279 Studio/setup-attempted"

echo "✓ installed: $APP"
echo "  首次打开会在终端里安装依赖，然后自动启动。以后在“应用程序”里双击 5279 Studio 即可。"
echo "  The first launch installs dependencies in a Terminal window and then opens the app."
open "$APP"
