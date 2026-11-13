import release from "@/data/release.json";

export const VERSION = release.version;
export const ZIP_NAME = release.zipName;
export const ZIP_SIZE = release.zipSize;

export const REPO = "https://github.com/KissuChaudhary/radius-mono";
export const REPO_SLUG = "KissuChaudhary/radius-mono";

/** Direct download of the release zip, served by GitHub on any host. */
export const DOWNLOAD = `${REPO}/releases/download/v${VERSION}/${ZIP_NAME}`;

export const TITLE = "Radius Mono";
export const DESCRIPTION =
  "Radius Mono is a free, open-source coding font: JetBrains Mono with a roundness axis from crisp (0) to fully round (100), in 8 weights with italics and 153 ligatures.";

/** Syntax-highlighted sample for the before / after editor. */
export type Token = [cls: "k" | "s" | "n" | "c" | "f" | "t" | null, text: string];
export const CODE: Token[][] = [
  [["c", "// fillet.ts: round every visible corner, keep every join"]],
  [["k", "type"], [null, " "], ["t", "Corner"], [null, " = { x: "], ["t", "number"], [null, "; y: "], ["t", "number"], [null, "; turn: "], ["t", "number"], [null, "; hidden?: "], ["t", "boolean"], [null, " };"]],
  [],
  [["k", "export function"], [null, " "], ["f", "fillet"], [null, "(c: "], ["t", "Corner"], [null, ", stem: "], ["t", "number"], [null, ", rond = "], ["n", "100"], [null, ") {"]],
  [[null, "  "], ["k", "if"], [null, " (rond <= "], ["n", "0"], [null, " || c.hidden) "], ["k", "return"], [null, " "], ["n", "0"], [null, ";   "], ["c", "// sharp, as drawn"]],
  [[null, "  "], ["k", "const"], [null, " r = (rond / "], ["n", "100"], [null, ") * stem / "], ["n", "2"], [null, ";      "], ["c", "// a round pen"]],
  [[null, "  "], ["k", "return"], [null, " c.turn >= Math.PI ? r : r * Math."], ["f", "tan"], [null, "(c.turn / "], ["n", "2"], [null, ");"]],
  [[null, "}"]],
  [],
  [["k", "const"], [null, " soft = corners."], ["f", "filter"], [null, "((c) => c.hidden !== "], ["k", "true"], [null, ");"]],
  [[null, "console."], ["f", "log"], [null, "("], ["s", "`${soft.length} corners -> rounded`"], [null, ");   "], ["c", "// 9728"]],
];
