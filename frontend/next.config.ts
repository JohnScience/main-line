import type { NextConfig } from "next";
import CopyWebpackPlugin from "copy-webpack-plugin";

const nextConfig: NextConfig = {
  distDir: "build",
  webpack: (config, { isServer }) => {
    // Equivalent of noParse: don't let webpack try to parse wasm
    config.module.noParse = /\.wasm$/;

    // Add loader for wasm files
    config.module.rules.push({
      test: /\.wasm$/,
      loader: 'base64-loader',
      type: 'javascript/auto', // override default wasm handling
    });

    // Avoid polyfills for Node built-ins
    config.resolve.fallback = {
      ...(config.resolve.fallback || {}),
      path: false,
      fs: false,
      Buffer: false,
      process: false,
    };

    config.plugins.push(
      new CopyWebpackPlugin({
        patterns: [
          {
            from: "node_modules/argon2-browser/dist/argon2.wasm",
            to: "static/chunks/argon2.wasm",
          },
        ],
      })
    );

    return config;
  },
};

export default nextConfig;