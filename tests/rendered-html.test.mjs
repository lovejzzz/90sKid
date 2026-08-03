import assert from "node:assert/strict";
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

test("server-renders the V23 project home page", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);
  const html = await response.text();
  assert.match(html, /5279 Emulsion Project/);
  assert.match(html, /当前基线 · V23/);
  assert.match(html, /v23-t020-projection/);
  assert.match(html, /参数面板|PARAMETERS/);
  assert.doesNotMatch(html, /Your site is taking shape|codex-preview/);
});

test("server-renders the V23 archive, research and algorithm routes", async () => {
  const pages = await Promise.all(["/versions", "/research", "/algorithm"].map(render));
  for (const response of pages) assert.equal(response.status, 200);
  const [versions, research, algorithm] = await Promise.all(pages.map((page) => page.text()));
  assert.match(versions, /V4—V23/);
  assert.match(versions, /NJARAW_S001_S001_T032/);
  assert.match(research, /V23 · ORGANIC DYE-CLOUD FIELD/);
  assert.match(research, /US 4,536,472/);
  assert.match(algorithm, /CURRENT V23/);
  assert.match(algorithm, /193³/);
});
