import type { NextConfig } from "next";

import CopyPlugin from "copy-webpack-plugin";
import { WebpackManifestPlugin } from "webpack-manifest-plugin";

const nextConfig: NextConfig = {
  distDir: "build",
  webpack: (config) => {
    const customPlugins = [
      new WebpackManifestPlugin({
        fileName: 'static/webpack-manifest.json',
        publicPath: '/static/',
      }),
      new CopyPlugin({
        patterns: [
          {
            from: 'node_modules/cm-chessboard/assets',
            to: 'static/cm-chessboard/assets',
            globOptions: {
              ignore: ['**/*.css.map'], // avoid duplicate source maps
            },
          },
        ],
      }),
    ];

    config.plugins.push(...customPlugins);

    return config;
  },
  async rewrites() {
    return [
      {
        "source": "/backend-proxy/:path*",
        "destination": process.env.BACKEND_API_URL ? `${process.env.BACKEND_API_URL}/:path*` : "http://localhost:3000/:path*"
      }
    ]
  }
};

export default nextConfig;