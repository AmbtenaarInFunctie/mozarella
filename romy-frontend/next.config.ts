import type { NextConfig } from "next";

const nextConfig: NextConfig = {
    /* config options here */
    sassOptions: {
        silenceDeprecations: ["legacy-js-api"],
    },
};

export default nextConfig;

module.exports = {
    pwa: {
        dest: "public",
        register: true,
        skipWaiting: true,
    },
    allowedDevOrigins: [
        "10.179.95.59",
        "local-origin.dev",
        "*.local-origin.dev",
    ],
    async headers() {
        return [
            {
                source: "/(.*)",
                headers: [
                    {
                        key: "X-Content-Type-Options",
                        value: "nosniff",
                    },
                    {
                        key: "X-Frame-Options",
                        value: "DENY",
                    },
                    {
                        key: "Referrer-Policy",
                        value: "strict-origin-when-cross-origin",
                    },
                ],
            },
            {
                source: "/sw.js",
                headers: [
                    {
                        key: "Content-Type",
                        value: "application/javascript; charset=utf-8",
                    },
                    {
                        key: "Cache-Control",
                        value: "no-cache, no-store, must-revalidate",
                    },
                    {
                        key: "Content-Security-Policy",
                        value: "default-src 'self'; script-src 'self'",
                    },
                ],
            },
        ];
    },
};
