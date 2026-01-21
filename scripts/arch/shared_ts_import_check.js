import fs from "node:fs";

const forbidden = [
  "apps/backend",
  "apps/frontend",
  "core/",
  "trestle-dev-tools_legacy_backend",
  "trestle-roundhouse-frontend_legacy",
];

const files = process.argv.slice(2);

for (const file of files) {
  const content = fs.readFileSync(file, "utf8");
  for (const bad of forbidden) {
    if (content.includes(bad)) {
      console.error(`[ARCH VIOLATION] ${file} imports forbidden module: ${bad}`);
      process.exit(1);
    }
  }
}
