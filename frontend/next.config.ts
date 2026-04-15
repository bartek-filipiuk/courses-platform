import type { NextConfig } from "next";

const securityHeaders = [
	{
		key: "X-Frame-Options",
		value: "DENY",
	},
	{
		key: "X-Content-Type-Options",
		value: "nosniff",
	},
	{
		key: "Referrer-Policy",
		value: "strict-origin-when-cross-origin",
	},
	{
		key: "X-DNS-Prefetch-Control",
		value: "on",
	},
	{
		key: "Content-Security-Policy",
		value: [
			"default-src 'self'",
			"script-src 'self' 'unsafe-inline' 'unsafe-eval'",
			"style-src 'self' 'unsafe-inline'",
			"img-src 'self' data: https:",
			"font-src 'self' https://fonts.gstatic.com",
			"connect-src 'self' http://localhost:8000 http://localhost:8001",
			"frame-ancestors 'none'",
		].join("; "),
	},
];

const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const nextConfig: NextConfig = {
	async headers() {
		return [
			{
				source: "/:path*",
				headers: securityHeaders,
			},
		];
	},
	async rewrites() {
		return [
			{
				source: "/api/backend/:path*",
				destination: `${apiUrl}/api/:path*`,
			},
		];
	},
};

export default nextConfig;
