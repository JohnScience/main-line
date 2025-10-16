// TODO: consider using
// 1. https://www.npmjs.com/package/runtime-info
// 2. https://github.com/environment-safe/runtime-context
// 3. https://github.com/sindresorhus/environment
// 4. Some other library

export type RuntimeEnvironment = "browser" | "web-worker" | "frontend-server";

export function inferRuntimeEnvironment(): RuntimeEnvironment {
    let runtime: RuntimeEnvironment;

    if (typeof globalThis?.window !== "undefined" && typeof globalThis?.document !== "undefined") {
        runtime = "browser";
    } else if (
        typeof globalThis?.self !== "undefined" &&
        typeof (globalThis as any).importScripts === "function"
    ) {
        runtime = "web-worker";
    } else {
        runtime = "frontend-server";
    };

    return runtime;
}

export function checkRuntime<R extends RuntimeEnvironment>(runtime: R): R {
    const inferred = inferRuntimeEnvironment();
    if (inferred !== runtime) {
        throw new Error(`Expected runtime: ${runtime}, but got: ${inferred}`);
    }
    return runtime;
}
