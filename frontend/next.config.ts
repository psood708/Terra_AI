import path from 'path';
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // This Next.js app lives in a subdirectory (frontend/) of the larger
  // Terra_API repo, not at the repo root - Next's file tracer otherwise
  // treats `frontend/` itself as the tracing root and can misbehave on
  // platforms (like Vercel) that check out the whole repo. Point it at the
  // actual repo root explicitly. https://nextjs.org/docs/.../output#caveats
  outputFileTracingRoot: path.join(__dirname, '..'),
  // Standalone output is for the self-hosted frontend/Dockerfile path only.
  // Vercel has its own build/file-tracing pipeline and conflicts with it
  // (fails with "ENOENT ... next-server.js.nft.json"), so skip it there —
  // Vercel sets VERCEL=1 during its own builds.
  ...(process.env.VERCEL ? {} : { output: 'standalone' as const }),
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
