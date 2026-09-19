import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [{ source: "/api/:path*", destination: "http://127.0.0.1:8000/api/:path*" }];
  },
  experimental: {
    // Gioi han body cho proxy /api/* -> FastAPI. Phai la SO BYTE: Next so sanh
    // truc tiep so byte da doc voi gia tri nay, nen chuoi kieu "250mb" se khong
    // duoc parse va gioi han coi nhu khong co tac dung.
    // Dat cao hon MAX_VIDEO_SIZE_MB cua backend de backend tra ve 413 JSON ro
    // rang thay vi proxy cat body giua duong.
    proxyClientMaxBodySize: 5 * 1024 * 1024 * 1024,
    // Next dev proxy huy request sau 30 giay (mac dinh: `proxyTimeout || 30000`).
    // Video 4K hoac video dai can hang phut de MediaPipe xu ly -> nang len 30 phut.
    proxyTimeout: 30 * 60 * 1000,
  },
};

export default nextConfig;