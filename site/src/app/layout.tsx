import type { Metadata, Viewport } from "next";
import localFont from "next/font/local";
import { DESCRIPTION, REPO, SITE_URL, TITLE } from "@/lib/site";
import "./globals.css";

const radius = localFont({
  src: [
    { path: "./fonts/RadiusMono-Variable.woff2", weight: "100 800", style: "normal" },
    { path: "./fonts/RadiusMono-Italic-Variable.woff2", weight: "100 800", style: "italic" },
  ],
  variable: "--font-radius",
  display: "swap",
  adjustFontFallback: false,
  fallback: ["ui-monospace", "SFMono-Regular", "Menlo", "Consolas", "monospace"],
});

const ogTitle = `${TITLE}: JetBrains Mono, with a border-radius`;

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: { absolute: `${TITLE}: the coding font with a roundness axis` },
  description: DESCRIPTION,
  alternates: { canonical: "./" },
  openGraph: {
    type: "website",
    siteName: TITLE,
    url: "./",
    title: ogTitle,
    description: DESCRIPTION,
    images: [{ url: "og.png", width: 1200, height: 630, alt: "Radius Mono specimen" }],
  },
  twitter: { card: "summary_large_image", title: ogTitle, description: DESCRIPTION, images: ["og.png"] },
};

export const viewport: Viewport = { themeColor: "#000000", colorScheme: "dark", viewportFit: "cover" };

const jsonLd = {
  "@context": "https://schema.org",
  "@type": "SoftwareSourceCode",
  name: TITLE,
  description: DESCRIPTION,
  codeRepository: REPO,
  license: "https://openfontlicense.org",
  url: SITE_URL,
};

// Runs before first paint: the page starts sharp so the hero can round itself
// without a flash. With reduced motion (or no JS) it simply stays round.
const intro = `try{if(!matchMedia('(prefers-reduced-motion: reduce)').matches){document.documentElement.style.setProperty('--rond','0');document.documentElement.dataset.intro='1'}}catch(e){}`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={radius.variable} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: intro }} />
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c") }} />
      </head>
      <body>{children}</body>
    </html>
  );
}
