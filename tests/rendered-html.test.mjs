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

test("server-renders the bilingual V45 spectral-observer revision over the V42 image baseline", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);
  const html = await response.text();
  assert.match(html, /5279 Emulsion Project/);
  const currentSection = html.match(/<section class="current-section wrap">([\s\S]*?)<\/section>/)?.[1] ?? "";
  assert.match(currentSection, /CURRENT SPECTRAL OBSERVER REVISION[\s\S]{0,120}V45/);
  assert.match(currentSection, /V42 IMAGE BASELINE/);
  assert.match(html, /Grain is not an overlay[\s\S]{0,30}Grain is the image/);
  assert.match(html, /v45-t020-projection/);
  assert.match(html, /v45-t020-projection-live-srgb\.mp4/);
  assert.match(html, /v43h-t020-fsd-live-srgb\.mp4/);
  assert.match(html, /v43h-t020-camera-live-srgb\.mp4/);
  assert.match(html, /中文/);
  assert.match(html, />EN</);
  assert.doesNotMatch(html, /LIVE · 1s/);
  assert.match(html, /参数面板|PARAMETERS/);
  assert.doesNotMatch(html, /Your site is taking shape|codex-preview/);
});

test("server-renders the V45 archive, research and algorithm routes", async () => {
  const pages = await Promise.all(
    ["/versions", "/research", "/algorithm"].map(render),
  );
  for (const response of pages) assert.equal(response.status, 200);
  const [versions, research, algorithm] = await Promise.all(
    pages.map((page) => page.text()),
  );
  assert.match(versions, /V4—[\s\S]{0,30}V45/);
  assert.match(versions, /OFFICIAL OBSERVER/);
  assert.match(versions, /OBSERVER INTEGRITY/);
  assert.match(versions, /HYPOTHESIS EDITION/);
  assert.match(versions, /NJARAW_S001_S001_T020/);
  assert.match(versions, /NJARAW_S001_S001_T032/);
  assert.match(versions, /NJARAW_S001_S001_T007/);
  assert.match(versions, /NJARAW_S001_S001_T031/);
  assert.match(versions, /CONTROLLED PIPELINE COMPARISON/);
  assert.match(versions, /V41 PHYSICAL 5279/);
  assert.match(versions, /FSD FINITE-SITE DENSITY/);
  assert.match(versions, /DETERMINISTIC NO-GRAIN/);
  assert.match(versions, /v41-t031-fsd-live-srgb\.mp4/);
  assert.match(versions, /v41-t031-deterministic-live-srgb\.mp4/);
  assert.match(
    versions,
    /16d14d8909d8e48ad11499f309844dda1ab3954c\/public\/versions\/v26-t020-projection-live-srgb\.mp4/,
  );
  assert.match(
    versions,
    /a23540fbf1ad47060cf8b9677c85d148b1b7ad48\/public\/versions\/v27-t020-projection-live-srgb\.mp4/,
  );
  assert.match(
    versions,
    /e85c07cf32ff732bffd97495b308a46120ee1c8b\/public\/versions\/v28-t020-projection-live-srgb\.mp4/,
  );
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
  assert.match(research, /V33 · CAMERA INPUT \/ BLACK BOUNDARY/);
  assert.match(research, /V34 · PROCESSED MTF \/ SINGLE GENERATION/);
  assert.match(research, /V35 · AUDITABLE PRODUCTION GRAPH/);
  assert.match(research, /V37 · INDEPENDENT SITES \/ STABLE INTEGRATION/);
  assert.match(research, /V38 · REFERENCE-DISPLAY DELIVERY/);
  assert.match(research, /V39 · DENSITY-FORMATION RECONSTRUCTION/);
  assert.match(research, /V40 · COLOUR-GRAIN COVARIANCE REPAIR/);
  assert.match(research, /V40 · THREE-PIPELINE CONTROL/);
  assert.match(research, /V41 · TWO-CHART-BOUNDED COLOUR TRANSPORT/);
  assert.match(research, /V42 · RESEARCH-CONFORMANT ENGINE/);
  assert.match(research, /V42 · DATA-LOSS INCIDENT \/ PREVENTION/);
  assert.match(research, /V43H · HYPOTHESIS EDITION/);
  assert.match(research, /V44 · OBSERVER INTEGRITY \/ SCALE-HONEST REVIEW/);
  assert.match(research, /V45 · OFFICIAL CIE OBSERVER \/ 1 NM SPECTRAL INTEGRATION/);
  assert.match(research, /214 authored files|214个作者文件/);
  assert.match(research, /deletion trigger|删除触发器/);
  assert.match(research, /12\.5% retained/);
  assert.match(research, /T003 · CHART INPUT AUDIT/);
  assert.match(research, /R\/G=1\.175/);
  assert.match(research, /DGK Color Tools/);
  assert.match(research, /printed title strip/);
  assert.match(research, /L\*=23/);
  assert.match(research, /N=176/);
  assert.match(research, /NEUTRAL TRANSPORT THROUGH V40/);
  assert.match(research, /0\.002530/);
  assert.doesNotMatch(research, /N=128/);
  assert.match(research, /V36 · MATCHED FRAME \/ 35 MM STRUCTURE/);
  assert.match(research, /SMPTE ST 428-1/);
  assert.match(algorithm, /V45 OFFICIAL CIE OBSERVER \/ V42 IMAGE BASELINE/);
  assert.match(algorithm, /OFFICIAL CIE 1931 2° · 1 NM/);
  assert.match(algorithm, /GATED OBSERVERS · SCALE-DECLARED REVIEW/);
  assert.match(algorithm, /HYPOTHESIS EDITION · ISOLATED \/ REVERSIBLE/);
  assert.match(algorithm, /RESEARCH-CONFORMANT ENGINE · ONE PICTURE AUTHORITY/);
  assert.match(algorithm, /T003 FIT · T005 HOLDOUT · LUMINANCE PRESERVED/);
  assert.match(algorithm, /ONE MASTER LIGHT · TWO EXPLICIT DELIVERIES/);
  assert.match(algorithm, /INDEPENDENT SITES · STABLE INTEGRATION/);
  assert.match(algorithm, /AUDITABLE PRODUCTION GRAPH/);
  assert.match(algorithm, /PROCESSED MTF · SINGLE GENERATION/);
  assert.match(algorithm, /V33 · INPUT \/ TONE \/ DELIVERY CONTRACT/);
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

test("V33 As Shot witnesses are 0-stop, native and web-colour verified", async () => {
  const manifest = JSON.parse(
    await readFile(
      new URL(
        "../public/versions/v33-live-preview-manifest.json",
        import.meta.url,
      ),
      "utf8",
    ),
  );
  assert.equal(manifest.camera_exposure_stops, 0);
  assert.equal(manifest.film_virtual_exposure_stops, 0.45);
  assert.equal(manifest.technical_neutral_enabled, false);
  assert.equal(manifest.representative_frame, 12);
  assert.equal(Object.keys(manifest.verification).length, 3);
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

test("V34 film previews are one-second native 12-bit masters with frozen camera witnesses", async () => {
  const manifest = JSON.parse(
    await readFile(
      new URL(
        "../public/versions/v34-live-preview-manifest.json",
        import.meta.url,
      ),
      "utf8",
    ),
  );
  assert.equal(manifest.frames, 24);
  assert.equal(manifest.representative_frame, 12);
  assert.equal(Object.keys(manifest.verification).length, 9);
  assert.match(manifest.film_pipeline, /one-generation 12-bit Rec\.709/);
  for (const [key, result] of Object.entries(manifest.verification)) {
    if (!key.endsWith("camera-reuse")) {
      assert.equal(result.master_metadata.width, 5760);
      assert.equal(result.master_metadata.height, 4320);
      assert.equal(result.master_metadata.pix_fmt, "yuv444p12le");
      assert.equal(result.master_metadata.bits_per_raw_sample, "12");
      assert.equal(result.master_metadata.nb_frames, "24");
    }
    assert.ok(Math.max(...result.first_frame_channel_mae_rgb) <= 0.025);
    assert.ok(result.first_frame_median_luma_delta <= 0.01);
  }
});

test("V35 film previews are one-second native 12-bit masters with frozen camera witnesses", async () => {
  const manifest = JSON.parse(
    await readFile(
      new URL(
        "../public/versions/v35-live-preview-manifest.json",
        import.meta.url,
      ),
      "utf8",
    ),
  );
  assert.equal(manifest.frames, 24);
  assert.equal(manifest.representative_frame, 12);
  assert.equal(Object.keys(manifest.verification).length, 9);
  assert.match(manifest.film_pipeline, /Philox-u32\/Metal/);
  for (const [key, result] of Object.entries(manifest.verification)) {
    if (!key.endsWith("camera-reuse")) {
      assert.equal(result.master_metadata.width, 5760);
      assert.equal(result.master_metadata.height, 4320);
      assert.equal(result.master_metadata.pix_fmt, "yuv444p12le");
      assert.equal(result.master_metadata.bits_per_raw_sample, "12");
      assert.equal(result.master_metadata.nb_frames, "24");
    }
    assert.ok(Math.max(...result.first_frame_channel_mae_rgb) <= 0.025);
    assert.ok(result.first_frame_median_luma_delta <= 0.01);
  }
});

test("V36 locks absolute source frames and preserves the native 35 mm image model", async () => {
  const manifest = JSON.parse(
    await readFile(
      new URL(
        "../public/versions/v36-live-preview-manifest.json",
        import.meta.url,
      ),
      "utf8",
    ),
  );
  assert.equal(manifest.frames, 24);
  assert.equal(manifest.representative_frame, 12);
  assert.deepEqual(manifest.absolute_source_frame_contract, {
    t002: [0, 23],
    t007: [276, 299],
    t031: [132, 155],
  });
  assert.equal(Object.keys(manifest.verification).length, 9);
  assert.match(manifest.film_pipeline, /no retune/);
  assert.match(manifest.proxy_encoding, /closed 6-frame GOP/);
  for (const [key, result] of Object.entries(manifest.verification)) {
    if (!key.endsWith("camera-reuse")) {
      assert.equal(result.master_metadata.width, 5760);
      assert.equal(result.master_metadata.height, 4320);
      assert.equal(result.master_metadata.pix_fmt, "yuv444p12le");
      assert.equal(result.master_metadata.bits_per_raw_sample, "12");
      assert.equal(result.master_metadata.nb_frames, "24");
    }
    assert.ok(Math.max(...result.first_frame_channel_mae_rgb) <= 0.025);
    assert.ok(Math.abs(result.first_frame_median_luma_delta) <= 0.01);
  }
});

test("V37 renews grain sites under one stable-balanced integration operator", async () => {
  const manifest = JSON.parse(
    await readFile(
      new URL(
        "../public/versions/v37-live-preview-manifest.json",
        import.meta.url,
      ),
      "utf8",
    ),
  );
  assert.equal(manifest.frames, 24);
  assert.equal(manifest.representative_frame, 12);
  assert.deepEqual(manifest.absolute_source_frame_contract, {
    t002: [0, 23],
    t007: [276, 299],
    t031: [132, 155],
  });
  assert.equal(Object.keys(manifest.verification).length, 9);
  assert.match(manifest.film_pipeline, /30-degree stable-balanced/);
  assert.match(manifest.proxy_encoding, /closed 6-frame GOP/);
  for (const [key, result] of Object.entries(manifest.verification)) {
    if (!key.endsWith("camera-reuse")) {
      assert.equal(result.master_metadata.width, 5760);
      assert.equal(result.master_metadata.height, 4320);
      assert.equal(result.master_metadata.pix_fmt, "yuv444p12le");
      assert.equal(result.master_metadata.bits_per_raw_sample, "12");
      assert.equal(result.master_metadata.nb_frames, "24");
    }
    assert.ok(Math.max(...result.first_frame_channel_mae_rgb) <= 0.025);
    assert.ok(Math.abs(result.first_frame_median_luma_delta) <= 0.01);
  }
});

test("V38 derives web media only from the sRGB 12-bit companion", async () => {
  const manifest = JSON.parse(
    await readFile(
      new URL(
        "../public/versions/v38-live-preview-manifest.json",
        import.meta.url,
      ),
      "utf8",
    ),
  );
  assert.equal(manifest.frames, 24);
  assert.equal(manifest.representative_frame, 12);
  assert.deepEqual(manifest.absolute_source_frame_contract, {
    t002: [0, 23],
    t007: [276, 299],
    t031: [132, 155],
  });
  assert.equal(Object.keys(manifest.verification).length, 6);
  assert.match(manifest.film_pipeline, /V37 frozen/);
  assert.match(manifest.professional_master, /inverse BT\.1886/);
  assert.match(manifest.quicktime_companion, /IEC sRGB transfer/);
  assert.match(manifest.web, /sRGB companion/);
  for (const result of Object.values(manifest.verification)) {
    assert.equal(result.companion_metadata.width, 5760);
    assert.equal(result.companion_metadata.height, 4320);
    assert.equal(result.companion_metadata.pix_fmt, "yuv444p12le");
    assert.equal(result.companion_metadata.bits_per_raw_sample, "12");
    assert.equal(result.companion_metadata.nb_frames, "24");
    assert.equal(result.companion_metadata.color_transfer, "iec61966-2-1");
    assert.ok(Math.max(...result.first_frame_channel_mae_rgb) <= 0.018);
    assert.ok(Math.max(...result.luma_p05_p50_p95_absolute_delta) <= 0.01);
  }
});

test("V39 keeps density formation and every delivery exit auditable", async () => {
  const manifest = JSON.parse(
    await readFile(
      new URL(
        "../public/versions/v39-live-preview-manifest.json",
        import.meta.url,
      ),
      "utf8",
    ),
  );
  assert.equal(manifest.frames, 24);
  assert.equal(manifest.representative_frame, 12);
  assert.deepEqual(manifest.absolute_source_frame_contract, {
    t002: [0, 23],
    t007: [276, 299],
    t031: [132, 155],
  });
  assert.equal(Object.keys(manifest.verification).length, 6);
  assert.match(manifest.film_pipeline, /processed 5279 density MTF/);
  assert.match(manifest.film_pipeline, /Status-A density/);
  assert.match(manifest.raw_record_boundary, /signed film-basis/);
  assert.equal(manifest.artistic_grade.startsWith("none"), true);
  assert.match(manifest.quicktime_companion, /master-derived/);
  assert.match(manifest.quicktime_companion, /4444 XQ/);
  assert.doesNotMatch(JSON.stringify(manifest), /\/Users\/tianxing/);
  assert.match(manifest.web, /hover frame zero/);
  assert.equal(Object.keys(manifest.timing).length, 3);
  for (const result of Object.values(manifest.verification)) {
    assert.equal(result.companion_metadata.width, 5760);
    assert.equal(result.companion_metadata.height, 4320);
    assert.equal(result.companion_metadata.pix_fmt, "yuv444p12le");
    assert.equal(result.companion_metadata.bits_per_raw_sample, "12");
    assert.equal(result.companion_metadata.nb_frames, "24");
    assert.equal(result.companion_metadata.color_transfer, "iec61966-2-1");
    assert.equal(result.companion_metadata.profile, "XQ");
    assert.ok(Math.max(...result.first_frame_channel_mae_rgb) <= 0.018);
    assert.ok(Math.max(...result.luma_p05_p50_p95_absolute_delta) <= 0.01);
  }
});

test("V40 publishes only master-derived XQ media after the colour-tail repair", async () => {
  const manifest = JSON.parse(
    await readFile(
      new URL(
        "../public/versions/v40-live-preview-manifest.json",
        import.meta.url,
      ),
      "utf8",
    ),
  );
  assert.equal(manifest.frames, 24);
  assert.equal(manifest.representative_frame, 12);
  assert.deepEqual(manifest.absolute_source_frame_contract, {
    t002: [0, 23],
    t007: [276, 299],
    t031: [132, 155],
  });
  assert.equal(Object.keys(manifest.verification).length, 6);
  assert.match(manifest.film_pipeline, /formed 5279 density/);
  assert.match(manifest.colour_grain_boundary, /does not re-add/);
  assert.match(manifest.professional_master, /12-bit ProRes 4444 XQ/);
  assert.match(manifest.quicktime_companion, /derived from the encoded master/);
  assert.equal(manifest.artistic_grade.startsWith("none"), true);
  assert.doesNotMatch(JSON.stringify(manifest), /\/Users\/tianxing/);
  for (const result of Object.values(manifest.verification)) {
    assert.equal(result.companion_metadata.width, 5760);
    assert.equal(result.companion_metadata.height, 4320);
    assert.equal(result.companion_metadata.pix_fmt, "yuv444p12le");
    assert.equal(result.companion_metadata.bits_per_raw_sample, "12");
    assert.equal(result.companion_metadata.nb_frames, "24");
    assert.equal(result.companion_metadata.color_transfer, "iec61966-2-1");
    assert.equal(result.companion_metadata.profile, "XQ");
    assert.ok(Math.max(...result.first_frame_channel_mae_rgb) <= 0.018);
    assert.ok(Math.max(...result.luma_p05_p50_p95_absolute_delta) <= 0.01);
  }
});

test("V40 FSD comparison contains exactly the two new 12-bit controls", async () => {
  const manifest = JSON.parse(
    await readFile(
      new URL(
        "../public/versions/v40-fsd-comparator-manifest.json",
        import.meta.url,
      ),
      "utf8",
    ),
  );
  assert.equal(manifest.frames, 24);
  assert.equal(manifest.representative_frame, 12);
  assert.equal(manifest.fsd.site_count, 176);
  assert.equal(manifest.fsd.correlation_sigma_native_pixels, 0.597);
  assert.match(manifest.fsd.status, /independent comparator/);
  assert.equal(Object.keys(manifest.verification).length, 6);
  for (const result of Object.values(manifest.verification)) {
    assert.equal(result.companion_metadata.width, 5760);
    assert.equal(result.companion_metadata.height, 4320);
    assert.equal(result.companion_metadata.pix_fmt, "yuv444p12le");
    assert.equal(result.companion_metadata.bits_per_raw_sample, "12");
    assert.equal(result.companion_metadata.nb_frames, "24");
    assert.equal(result.companion_metadata.color_transfer, "iec61966-2-1");
    assert.equal(result.companion_metadata.profile, "XQ");
    assert.ok(Math.max(...result.first_frame_channel_mae_rgb) <= 0.018);
    assert.ok(Math.max(...result.luma_p05_p50_p95_absolute_delta) <= 0.01);
  }
});

test("V41 publishes four-view media from chart-bounded native 12-bit sources", async () => {
  const manifest = JSON.parse(
    await readFile(
      new URL(
        "../public/versions/v41-live-preview-manifest.json",
        import.meta.url,
      ),
      "utf8",
    ),
  );
  assert.equal(manifest.frames, 24);
  assert.equal(manifest.representative_frame, 12);
  assert.deepEqual(manifest.absolute_source_frame_contract, {
    t002: [0, 23],
    t007: [276, 299],
    t031: [132, 155],
  });
  assert.equal(manifest.colour_evidence.strength, 0.125);
  assert.match(manifest.colour_evidence.independent_holdout, /T005/);
  assert.match(manifest.record_boundary, /all combined 5279 record exposures are non-negative/);
  assert.match(manifest.pipelines.physical, /V41 shared colour input/);
  assert.match(manifest.pipelines.fsd, /N=176/);
  assert.equal(Object.keys(manifest.verification).length, 12);
  assert.doesNotMatch(JSON.stringify(manifest), /\/Users\/tianxing/);
  for (const result of Object.values(manifest.verification)) {
    assert.equal(result.companion_metadata.width, 5760);
    assert.equal(result.companion_metadata.height, 4320);
    assert.equal(result.companion_metadata.pix_fmt, "yuv444p12le");
    assert.equal(result.companion_metadata.bits_per_raw_sample, "12");
    assert.equal(result.companion_metadata.nb_frames, "24");
    assert.equal(result.companion_metadata.color_transfer, "iec61966-2-1");
    assert.equal(result.companion_metadata.profile, "XQ");
    assert.ok(Math.max(...result.first_frame_channel_mae_rgb) <= 0.018);
    assert.ok(Math.max(...result.luma_p05_p50_p95_absolute_delta) <= 0.01);
  }
});

test("V43H publishes three four-view hypothesis trials from native 12-bit authorities", async () => {
  const manifest = JSON.parse(
    await readFile(
      new URL(
        "../public/versions/v43h-live-preview-manifest.json",
        import.meta.url,
      ),
      "utf8",
    ),
  );
  assert.equal(manifest.release, "V43H Hypothesis Edition");
  assert.equal(manifest.release_class, "hypothesis_not_measurement");
  assert.equal(manifest.frames, 24);
  assert.equal(manifest.representative_frame, 12);
  assert.deepEqual(manifest.absolute_source_frame_contract, {
    t020: [0, 23],
    t032: [0, 23],
    t007: [276, 299],
  });
  assert.match(manifest.pipelines.projection, /2383 xenon/);
  assert.match(manifest.pipelines.scan, /same V43H negative/);
  assert.match(manifest.pipelines.fsd, /independent/);
  assert.match(manifest.pipelines.camera, /no film pipeline/);
  assert.equal(Object.keys(manifest.verification).length, 12);
  assert.doesNotMatch(JSON.stringify(manifest), /\/Users\/tianxing/);
  for (const result of Object.values(manifest.verification)) {
    assert.equal(result.release_class, "hypothesis_not_measurement");
    assert.equal(result.companion_metadata.width, 5760);
    assert.equal(result.companion_metadata.height, 4320);
    assert.equal(result.companion_metadata.pix_fmt, "yuv444p12le");
    assert.equal(result.companion_metadata.bits_per_raw_sample, "12");
    assert.equal(result.companion_metadata.nb_frames, "24");
    assert.equal(result.companion_metadata.color_transfer, "iec61966-2-1");
    assert.equal(result.companion_metadata.profile, "XQ");
    assert.ok(Math.max(...result.first_frame_channel_mae_rgb) <= 0.018);
    assert.ok(Math.max(...result.luma_p05_p50_p95_absolute_delta) <= 0.01);
  }
});

test("V44 publishes a gated scale-integrated review from encoded 12-bit authorities", async () => {
  const manifest = JSON.parse(
    await readFile(
      new URL(
        "../public/versions/v44-live-preview-manifest.json",
        import.meta.url,
      ),
      "utf8",
    ),
  );
  assert.equal(manifest.release_class, "evidence_boundary_revision");
  assert.equal(manifest.frames, 24);
  assert.equal(manifest.representative_frame, 12);
  assert.deepEqual(manifest.dimensions, [1280, 960]);
  assert.match(manifest.display_review, /pixel-area integration/);
  assert.match(manifest.projection_colour, /V31 normal-process monitor boundary/);
  assert.equal(manifest.native_release_audit.all_gates_pass, true);
  assert.equal(Object.keys(manifest.verification).length, 2);
  assert.doesNotMatch(JSON.stringify(manifest), /\/Users\/tianxing/);
  for (const result of Object.values(manifest.verification)) {
    assert.equal(result.review_metadata.width, 1920);
    assert.equal(result.review_metadata.height, 1440);
    assert.equal(result.review_metadata.pix_fmt, "yuv444p12le");
    assert.equal(result.review_metadata.bits_per_raw_sample, "12");
    assert.equal(result.review_metadata.nb_frames, "24");
    assert.equal(result.review_metadata.color_transfer, "iec61966-2-1");
    assert.equal(result.review_metadata.profile, "XQ");
    assert.ok(Math.max(...result.first_frame_channel_mae_rgb) <= 0.018);
    assert.ok(Math.max(...result.luma_p05_p50_p95_absolute_delta) <= 0.01);
  }
});

test("V45 publishes three official-observer trials from encoded review authorities", async () => {
  const manifest = JSON.parse(
    await readFile(
      new URL(
        "../public/versions/v45-live-preview-manifest.json",
        import.meta.url,
      ),
      "utf8",
    ),
  );
  assert.equal(manifest.release_class, "measured_observer_revision");
  assert.equal(manifest.frames, 24);
  assert.equal(manifest.representative_frame, 12);
  assert.deepEqual(manifest.dimensions, [1280, 960]);
  assert.match(manifest.only_image_change, /official CIE table/);
  assert.match(manifest.frozen, /black, contrast, gamma/);
  assert.equal(Object.keys(manifest.verification).length, 6);
  assert.deepEqual(Object.keys(manifest.timing).sort(), ["T007", "T020", "T032"]);
  assert.equal(manifest.same_negative_ablation.scan_is_bit_exact, true);
  assert.ok(manifest.same_negative_ablation.projection_delta.rms < 0.00004);
  assert.equal(manifest.native_release_audit.all_gates_pass, true);
  assert.equal(manifest.delivery_audit.pass, true);
  for (const scene of Object.values(manifest.native_release_audit.branch_pass)) {
    assert.equal(scene.projection, true);
    assert.equal(scene.scan, true);
  }
  assert.doesNotMatch(JSON.stringify(manifest), /\/Users\/tianxing/);
  for (const result of Object.values(manifest.verification)) {
    assert.equal(result.review_metadata.width, 1920);
    assert.equal(result.review_metadata.height, 1440);
    assert.equal(result.review_metadata.pix_fmt, "yuv444p12le");
    assert.equal(result.review_metadata.bits_per_raw_sample, "12");
    assert.equal(result.review_metadata.nb_frames, "24");
    assert.equal(result.review_metadata.color_transfer, "iec61966-2-1");
    assert.equal(result.review_metadata.profile, "XQ");
    assert.ok(Math.max(...result.first_frame_channel_mae_rgb) <= 0.018);
    assert.ok(Math.max(...result.luma_p05_p50_p95_absolute_delta) <= 0.01);
  }
});
