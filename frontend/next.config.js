/** @type {import('next').NextConfig} */
// Output static HTML export ('out' folder) for Cloudflare Pages by default,
// or 'standalone' when building containerized Docker images.
const isStandalone = process.env.OUTPUT_STANDALONE === 'true';

const nextConfig = {
  output: isStandalone ? 'standalone' : 'export',
  reactStrictMode: true,
  images: {
    unoptimized: !isStandalone,
    domains: ['localhost'],
  },
  ...(isStandalone ? {
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
      ]
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
      ]
    },
  } : {}),
}

module.exports = nextConfig
