import type { NextConfig } from "next";

const backend = process.env.BACKEND_URL || "http://localhost:8300";

export default {
  output: "standalone",
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${backend}/api/:path*` }];
  },
} satisfies NextConfig;
