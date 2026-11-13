import type { NextConfig } from "next";

// Absolute site URL for Open Graph / Twitter cards. On Vercel this resolves to the
// production domain automatically; set NEXT_PUBLIC_SITE_URL to override (custom domain).
const siteUrl =
  process.env.NEXT_PUBLIC_SITE_URL ??
  (process.env.VERCEL_PROJECT_PRODUCTION_URL ? `https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}` : "http://localhost:3000");

const config: NextConfig = {
  env: { NEXT_PUBLIC_SITE_URL: siteUrl },
};

export default config;
