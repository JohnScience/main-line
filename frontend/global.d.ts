
declare module "*.wasm" {
    const path: string;
    export default path;
}

declare module "argon2-browser/dist/argon2-bundled.min.js" {
    const argon2: typeof import("argon2-browser");
    export default argon2;
}