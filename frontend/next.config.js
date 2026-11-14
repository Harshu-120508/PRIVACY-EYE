/** @type {import('next').NextConfig} */
// Adaptive deployment target:
// 1. Docker: OUTPUT_STANDALONE=true -> 'standalone'
// 2. Vercel: VERCEL=1 -> native Next.js serverless with rewrites & headers
// 3. Cloudflare Pages: default -> static HTML export ('out' directory)
const isStandalone = process.env.OUTPUT_STANDALONE === 'true';
const isVercel = process.env.VERCEL === '1';
const isExport = !isStandalone && !isVercel;

const nextConfig = {
  ...(isStandalone ? { output: 'standalone' } : isExport ? { output: 'export' } : {}),
  reactStrictMode: true,
  images: {
    unoptimized: isExport,
    domains: ['localhost'],
  },
  ...(!isExport ? {
    async headers() {
      return [
        {
          source: '/(.*)',
          headers: [
            { key: 'X-Frame-Options',        value: 'DENY' },
            { key: 'X-Content-Type-Options', value: 'nosniff' },
            { key: 'Referrer-Policy',        value: 'strict-origin-when-cross-origin' },
            { key: 'X-XSS-Protection',       value: '1; mode=block' },
            { key: 'Permissions-Policy',     value: 'camera=(self), microphone=(self), geolocation=()' },
          ],
        },
      ];
    },
    async rewrites() {
      let rawBackend = process.env.BACKEND_API_URL;
      if (!rawBackend && process.env.NEXT_PUBLIC_API_URL && process.env.NEXT_PUBLIC_API_URL.startsWith('http')) {
        rawBackend = process.env.NEXT_PUBLIC_API_URL;
      }
      if (!rawBackend) {
        rawBackend = 'http://127.0.0.1:8000';
      }
      const backendUrl = rawBackend.replace(/\/api\/v1\/?$/, '').replace(/\/+$/, '');
      return [
        {
          source: '/api/v1/:path*',
          destination: `${backendUrl}/api/v1/:path*`,
        },
        {
          source: '/docs',
          destination: `${backendUrl}/docs`,
        },
        {
          source: '/openapi.json',
          destination: `${backendUrl}/openapi.json`,
        },
      ];
    },
  } : {}),
};

module.exports = nextConfig;
