import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

async function render(path = "/") {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}-${path}`);
  const { default: worker } = await import(workerUrl.href);
  return worker.fetch(
    new Request(`http://localhost${path}`, { headers: { accept: "text/html" } }),
    { ASSETS: { fetch: async () => new Response("Not found", { status: 404 }) } },
    { waitUntil() {}, passThroughOnException() {} },
  );
}

test("server-renders the V26 project home page", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);
  const html = await response.text();
  assert.match(html, /5279 Emulsion Project/);
  assert.match(html, /当前基线 · V26/);
  assert.match(html, /v26-t020-projection/);
  assert.match(html, /v26-t020-projection-live-srgb\.mp4/);
  assert.doesNotMatch(html, /LIVE · 1s/);
  assert.match(html, /参数面板|PARAMETERS/);
  assert.doesNotMatch(html, /Your site is taking shape|codex-preview/);
});

test("server-renders the V26 archive, research and algorithm routes", async () => {
  const pages = await Promise.all(["/versions", "/research", "/algorithm"].map(render));
  for (const response of pages) assert.equal(response.status, 200);
  const [versions, research, algorithm] = await Promise.all(pages.map((page) => page.text()));
  assert.match(versions, /V4—V26/);
  assert.match(versions, /NJARAW_S001_S001_T032/);
  assert.match(research, /V24 · 35MM SPECTRAL SEPARATION/);
  assert.match(research, /Print Grain Index/);
  assert.match(research, /V25 RESULT · COLOUR PIPELINE \+ EXACT ACCELERATION/);
  assert.match(research, /Hourly审计/);
  assert.match(research, /ITU-R BT\.1886/);
  assert.match(research, /EXPOSURE-CONDITIONED GRAIN NPS/);
  assert.match(research, /v26-grain-nps\.png/);
  assert.match(algorithm, /CURRENT V26/);
  assert.match(algorithm, /193³/);
});

test("lightbox keeps gallery navigation and magnification controls", async () => {
  const source = await readFile(new URL("../app/components/InteractiveImage.tsx", import.meta.url), "utf8");
  assert.match(source, /aria-label="上一张图片"/);
  assert.match(source, /aria-label="下一张图片"/);
  assert.match(source, /放大图片，当前/);
  assert.match(source, /ArrowLeft/);
  assert.match(source, /ArrowRight/);
  assert.match(source, /value === 1 \? 2 : value === 2 \? 4 : 1/);
  assert.match(source, /onMouseEnter={startPreview}/);
  assert.match(source, /onMouseLeave={stopPreview}/);
  assert.doesNotMatch(source, /autoPlay/);
  assert.match(source, /pendingViewRef/);
  assert.match(source, /stage\.scrollLeft \+= saved\.x/);
  assert.match(source, /stage\.scrollTop \+= saved\.y/);
});

test("V26 web videos preserve the corrected Rec.709 to sRGB path", async () => {
  const data = await readFile(new URL("../app/data.ts", import.meta.url), "utf8");
  const styles = await readFile(new URL("../app/globals.css", import.meta.url), "utf8");
  const manifest = JSON.parse(await readFile(new URL("../public/versions/v26-live-preview-manifest.json", import.meta.url), "utf8"));
  assert.match(data, /sRGB IEC 61966-2-1/);
  assert.match(data, /网页首帧亮度误差/);
  assert.doesNotMatch(styles, /brightness\(1\.04\)/);
  assert.match(manifest.web, /sRGB IEC 61966-2-1/);
  assert.equal(manifest.first_frame_source_index, 12);
  assert.match(manifest.projection_source, /Rec\.709-D65 1-1-1/);
  assert.match(manifest.bluray_source, /BT\.1886 is the reference display EOTF/);
  for (const result of Object.values(manifest.verification)) {
    assert.ok(Math.max(...result.first_frame_channel_mae_rgb) <= 0.025);
    assert.ok(result.first_frame_median_luma_delta <= 0.01);
  }
});
