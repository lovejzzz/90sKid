import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

async function render(path = "/") {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}-${path}`);
  const { default: worker } = await import(workerUrl.href);
  return worker.fetch(
    new Request(`http://localhost${path}`, {
      headers: { accept: "text/html" },
    }),
    {
      ASSETS: { fetch: async () => new Response("Not found", { status: 404 }) },
    },
    { waitUntil() {}, passThroughOnException() {} },
  );
}

test("server-renders the bilingual V32 project home page", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);
  const html = await response.text();
  assert.match(html, /5279 Emulsion Project/);
  assert.match(html, /CURRENT BASELINE[\s\S]{0,50}V32/);
  assert.match(html, /Grain is not an overlay[\s\S]{0,30}Grain is the image/);
  assert.match(html, /v32-t007-projection/);
  assert.match(html, /v32-t007-projection-live-srgb\.mp4/);
  assert.match(html, /v32-t007-camera/);
  assert.match(html, /https:\/\/lovejzzz\.github\.io\/90sKid\/versions\/v32-t007-projection/);
  assert.match(html, /中文/);
  assert.match(html, />EN</);
  assert.doesNotMatch(html, /LIVE · 1s/);
  assert.match(html, /参数面板|PARAMETERS/);
  assert.doesNotMatch(html, /Your site is taking shape|codex-preview/);
});

test("server-renders the V32 archive, research and algorithm routes", async () => {
  const pages = await Promise.all(
    ["/versions", "/research", "/algorithm"].map(render),
  );
  for (const response of pages) assert.equal(response.status, 200);
  const [versions, research, algorithm] = await Promise.all(
    pages.map((page) => page.text()),
  );
  assert.match(versions, /V4—[\s\S]{0,30}V32/);
  assert.match(versions, /NJARAW_S001_S001_T031/);
  assert.match(research, /V24 · 35 MM SPECTRAL SEPARATION/);
  assert.match(research, /Print Grain Index/);
  assert.match(research, /V25 · OUTPUT STANDARD/);
  assert.match(research, /Ten hourly notes/);
  assert.match(research, /ITU-R BT\.1886/);
  assert.match(research, /EXPOSURE-CONDITIONED GRAIN NPS/);
  assert.match(research, /v26-grain-nps\.png/);
  assert.match(research, /PERIOD-SCAN NEUTRAL SCALE/);
  assert.match(research, /v27-scan-neutral-axis\.png/);
  assert.match(research, /EVIDENCE AUDIT · 10 NOTES/);
  assert.match(research, /The document branch did drift/);
  assert.match(research, /assigned by Thomson to Dolby/);
  assert.match(research, /public JVT mail evidence stops in 2002/);
  assert.match(research, /V29 · FULL-MOTION VALIDATION/);
  assert.match(research, /V30 · THREE-SCENE COLOUR EVIDENCE/);
  assert.match(research, /V31 · NORMAL-PROCESS CHROMA \/ TONE/);
  assert.match(research, /V32 · MEASUREMENT-FIRST GENERALIZATION/);
  assert.match(research, /SMPTE ST 428-1/);
  assert.match(algorithm, /CURRENT V32/);
  assert.match(algorithm, /V32 · MEASUREMENT \/ DELIVERY CONTRACT/);
  assert.match(algorithm, /V28 · RAW INPUT CONTRACT/);
  assert.match(algorithm, /V27 · SCAN GRAY AXIS/);
  assert.match(algorithm, /193³/);
});

test("lightbox keeps gallery navigation and magnification controls", async () => {
  const source = await readFile(
    new URL("../app/components/InteractiveImage.tsx", import.meta.url),
    "utf8",
  );
  assert.match(source, /上一张图片/);
  assert.match(source, /下一张图片/);
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
  const data = await readFile(
    new URL("../app/data.ts", import.meta.url),
    "utf8",
  );
  const styles = await readFile(
    new URL("../app/globals.css", import.meta.url),
    "utf8",
  );
  const manifest = JSON.parse(
    await readFile(
      new URL(
        "../public/versions/v26-live-preview-manifest.json",
        import.meta.url,
      ),
      "utf8",
    ),
  );
  assert.match(data, /sRGB IEC 61966-2-1/);
  assert.match(data, /网页首帧亮度误差/);
  assert.doesNotMatch(styles, /brightness\(1\.04\)/);
  assert.match(manifest.web, /sRGB IEC 61966-2-1/);
  assert.equal(manifest.first_frame_source_index, 12);
  assert.match(manifest.projection_source, /Rec\.709-D65 1-1-1/);
  assert.match(
    manifest.bluray_source,
    /BT\.1886 is the reference display EOTF/,
  );
  for (const result of Object.values(manifest.verification)) {
    assert.ok(Math.max(...result.first_frame_channel_mae_rgb) <= 0.025);
    assert.ok(result.first_frame_median_luma_delta <= 0.01);
  }
});

test("V27 data records a luma-locked neutral-scale correction", async () => {
  const data = await readFile(
    new URL("../app/data.ts", import.meta.url),
    "utf8",
  );
  const english = await readFile(
    new URL("../app/versionEnglish.ts", import.meta.url),
    "utf8",
  );
  assert.match(data, /2049级中性曝光/);
  assert.match(data, /逐像素Rec\.709 Y严格保持/);
  assert.match(data, /0\.01820 → 0\.00236/);
  assert.match(data, /网站加入完整中英文切换/);
  assert.match(english, /Separating a scanner's green veil from film colour/);
});

test("V27 stills and hover videos share the verified sRGB path", async () => {
  const manifest = JSON.parse(
    await readFile(
      new URL(
        "../public/versions/v27-live-preview-manifest.json",
        import.meta.url,
      ),
      "utf8",
    ),
  );
  assert.equal(manifest.first_frame_source_index, 12);
  assert.equal(manifest.frames, 24);
  assert.match(manifest.web, /sRGB IEC 61966-2-1/);
  for (const result of Object.values(manifest.verification)) {
    assert.equal(result.master_metadata.pix_fmt, "yuv444p12le");
    assert.equal(result.master_metadata.color_transfer, "bt709");
    assert.ok(Math.max(...result.first_frame_channel_mae_rgb) <= 0.025);
    assert.ok(result.first_frame_median_luma_delta <= 0.01);
  }
});

test("V29 full-motion previews derive from verified 12-bit masters", async () => {
  const manifest = JSON.parse(
    await readFile(
      new URL(
        "../public/versions/v29-live-preview-manifest.json",
        import.meta.url,
      ),
      "utf8",
    ),
  );
  assert.deepEqual(manifest.source_frame_range, [70, 93]);
  assert.equal(manifest.first_frame_source_index, 82);
  assert.equal(manifest.frames, 24);
  assert.match(manifest.web, /sRGB IEC 61966-2-1/);
  for (const result of Object.values(manifest.verification)) {
    assert.equal(result.master_metadata.width, 5760);
    assert.equal(result.master_metadata.height, 4320);
    assert.equal(result.master_metadata.pix_fmt, "yuv444p12le");
    assert.equal(result.master_metadata.nb_frames, "165");
    assert.ok(Math.max(...result.first_frame_channel_mae_rgb) <= 0.025);
    assert.ok(result.first_frame_median_luma_delta <= 0.01);
  }
});

test("V30 camera, projection and scan previews are frame-matched", async () => {
  const manifest = JSON.parse(
    await readFile(
      new URL(
        "../public/versions/v30-live-preview-manifest.json",
        import.meta.url,
      ),
      "utf8",
    ),
  );
  assert.deepEqual(manifest.source_frame_range, [0, 23]);
  assert.equal(manifest.first_frame_source_index, 12);
  assert.equal(Object.keys(manifest.verification).length, 9);
  assert.match(manifest.camera_source, /Panasonic official V-Log to V-709/);
  for (const result of Object.values(manifest.verification)) {
    assert.equal(result.master_metadata.width, 5760);
    assert.equal(result.master_metadata.height, 4320);
    assert.equal(result.master_metadata.pix_fmt, "yuv444p12le");
    assert.equal(result.master_metadata.bits_per_raw_sample, "12");
    assert.equal(result.master_metadata.nb_frames, "24");
    assert.ok(Math.max(...result.first_frame_channel_mae_rgb) <= 0.025);
    assert.ok(result.first_frame_median_luma_delta <= 0.01);
  }
});

test("V31 normal-process previews are frame-matched and web-colour verified", async () => {
  const manifest = JSON.parse(
    await readFile(
      new URL(
        "../public/versions/v31-live-preview-manifest.json",
        import.meta.url,
      ),
      "utf8",
    ),
  );
  assert.deepEqual(manifest.source_frame_range, [0, 23]);
  assert.equal(manifest.first_frame_source_index, 12);
  assert.equal(Object.keys(manifest.verification).length, 9);
  for (const result of Object.values(manifest.verification)) {
    assert.equal(result.master_metadata.width, 5760);
    assert.equal(result.master_metadata.height, 4320);
    assert.equal(result.master_metadata.pix_fmt, "yuv444p12le");
    assert.equal(result.master_metadata.bits_per_raw_sample, "12");
    assert.equal(result.master_metadata.nb_frames, "24");
    assert.ok(Math.max(...result.first_frame_channel_mae_rgb) <= 0.025);
    assert.ok(result.first_frame_median_luma_delta <= 0.01);
  }
});

test("V32 independent-scene previews are frame-matched and web-colour verified", async () => {
  const manifest = JSON.parse(
    await readFile(
      new URL(
        "../public/versions/v32-live-preview-manifest.json",
        import.meta.url,
      ),
      "utf8",
    ),
  );
  assert.deepEqual(manifest.source_frame_range, {
    T007: [276, 299],
    T031: [132, 155],
  });
  assert.deepEqual(manifest.first_frame_source_index, {
    T007: 288,
    T031: 144,
  });
  assert.equal(Object.keys(manifest.verification).length, 6);
  for (const result of Object.values(manifest.verification)) {
    assert.equal(result.master_metadata.width, 5760);
    assert.equal(result.master_metadata.height, 4320);
    assert.equal(result.master_metadata.pix_fmt, "yuv444p12le");
    assert.equal(result.master_metadata.bits_per_raw_sample, "12");
    assert.equal(result.master_metadata.nb_frames, "24");
    assert.ok(Math.max(...result.first_frame_channel_mae_rgb) <= 0.025);
    assert.ok(result.first_frame_median_luma_delta <= 0.01);
  }
});
