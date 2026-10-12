import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // A self-contained server in .next/standalone, so the runtime image needs
  // no node_modules install.
  output: "standalone",
  experimental: {
    // Uploads go browser -> server action -> API, which accepts files up to
    // 10 MiB (MAX_UPLOAD_BYTES). Both limits sit just above that, leaving room
    // for multipart overhead. The proxy's matters most: past its limit it
    // doesn't reject the body, it silently truncates it.
    serverActions: { bodySizeLimit: "11mb" },
    proxyClientMaxBodySize: "11mb",
  },
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
