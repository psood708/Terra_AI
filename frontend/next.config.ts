import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // Standalone output for a minimal production Docker image (see frontend/Dockerfile)
  output: 'standalone',
  // Allow the Next.js dev server to proxy API calls to the FastAPI backend
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
