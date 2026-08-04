import { access, cp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import type { Plugin } from "vite";

async function exists(path: string): Promise<boolean> {
  try {
    await access(path);
    return true;
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") {
      return false;
    }
    throw error;
  }
}

// Packages Sites metadata and migrations after Vite finishes compiling.
export function sites(): Plugin {
  let root = process.cwd();

  return {
    name: "sites",
    apply: "build",
    configResolved(config) {
      root = config.root;
    },
    async closeBundle() {
      const outputDirectory = resolve(root, "dist", ".openai");
      const hostingConfig = resolve(root, ".openai", "hosting.json");
      const drizzleSource = resolve(root, "drizzle");
      const workerConfig = resolve(root, "dist", "server", "wrangler.json");

      await rm(outputDirectory, { recursive: true, force: true });
      await mkdir(outputDirectory, { recursive: true });

      if (await exists(hostingConfig)) {
        await cp(hostingConfig, resolve(outputDirectory, "hosting.json"));
      }
      if (await exists(drizzleSource)) {
        await cp(drizzleSource, resolve(outputDirectory, "drizzle"), {
          recursive: true,
        });
      }

      // Sites made nodejs_compat implicit on 2026-08-04. The generated
      // Wrangler artifact still emits an empty compatibility_flags array;
      // remove the field entirely so the host does not treat it as an obsolete
      // explicit compatibility declaration.
      if (await exists(workerConfig)) {
        const parsed = JSON.parse(await readFile(workerConfig, "utf8"));
        if (Array.isArray(parsed.compatibility_flags) && parsed.compatibility_flags.length === 0) {
          delete parsed.compatibility_flags;
          await writeFile(workerConfig, JSON.stringify(parsed));
        }
      }
    },
  };
}
