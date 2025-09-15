/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: false,
  },
  eslint: {
    ignoreDuringBuilds: false,
  },
  // Avoid eval-based source maps to satisfy strict CSP
  webpack: (config, { dev }) => {
    if (dev) {
      config.devtool = 'source-map'
    }
    return config
  },
  async headers() {
    const isDev = process.env.NODE_ENV !== 'production'
    const cspParts = [
      // Scripts: Next.js uses small inline scripts for hydration. Allow inline always; eval only in dev.
      `script-src 'self' 'unsafe-inline' ${isDev ? "'unsafe-eval'" : ''} https://maps.googleapis.com https://maps.gstatic.com`.trim(),
      // Styles: allow inline for Tailwind/Next style tags
      "style-src 'self' 'unsafe-inline'",
      // Images from self, data URIs, and Google domains
      "img-src 'self' data: https://*.googleapis.com https://*.gstatic.com",
      // XHR/fetch to self and Google Maps APIs
      "connect-src 'self' https://maps.googleapis.com",
      // Disallow everything else by default
      "default-src 'self'",
    ]

    const csp = cspParts.join('; ')

    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'Content-Security-Policy',
            value: csp,
          },
        ],
      },
    ]
  },
}

module.exports = nextConfig
