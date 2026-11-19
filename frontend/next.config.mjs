export default {
  output: "standalone",
  devIndicators: false,
  experimental: { proxyTimeout: 3_600_000, proxyClientMaxBodySize: "201mb" },
  async rewrites() {
    return [
      { source: "/api/:path*", destination: "http://127.0.0.1:8000/:path*" },
    ];
  },
};
