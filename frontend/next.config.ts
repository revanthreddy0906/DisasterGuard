import type { NextConfig } from "next";

const backendOrigin = (process.env.BACKEND_ORIGIN || "http://localhost:8000").replace(/\/$/, "");

const nextConfig: NextConfig = {
  turbopack: {
    root: process.cwd(),
  },
  async rewrites() {
    return [
      {
        source: "/api/health",
        destination: `${backendOrigin}/health`,
      },
      {
        source: "/api/:path*",
        destination: `${backendOrigin}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
