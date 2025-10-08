import { Config, createClient as createClientInner } from "./gen-client/client";
import { JwtString } from "./gen_shared_types";

export function createClient(config: Config = {}): ReturnType<typeof createClientInner> {
    if (!config.baseUrl) {
        config.baseUrl = process.env.BASE_API_PROXY_URL || process.env.BASE_API_URL || "http://localhost:3000";
    }
    return createClientInner(config);
}

// Worker thread is not really tested
export type RuntimeEnvironment = "browser" | "web-worker" | "frontend-server";

export function makeJwtAuthorizationBearerHeaderOptions(jwt: JwtString): { headers: { "Authorization": string } } {
    return {
        headers: {
            "Authorization": `Bearer ${jwt}`
        }
    };
}

function getClientSideCookie(name: string): string | undefined {
    const cookieValue = document.cookie
        .split('; ')
        .find((row) => row.startsWith(`${name}=`))
        ?.split('=')[1];

    return cookieValue;
};

export function modifyOptions<T extends {
    client?: any,
    headers?: HeadersInit | Record<string, unknown>
}>(options: T) {
    if (!options.client) {
        options.client = createClient();
    }

    let runtime: RuntimeEnvironment;

    if (typeof globalThis?.window !== "undefined" && typeof globalThis?.document !== "undefined") {
        runtime = "browser";
    } else if (typeof globalThis?.self !== "undefined" && typeof globalThis?.importScripts === "function") {
        runtime = "web-worker";
    } else {
        runtime = "frontend-server";
    };

    switch (runtime) {
        case "browser": {
            const accessToken: JwtString | undefined = getClientSideCookie("access_token");
            const referer: string = window.location.origin;
            options.headers = {
                ...options.headers,
                "Referer": referer,
                ...(accessToken ? { "Authorization": `Bearer ${accessToken}` } : {})
            };
        } break;
        case "frontend-server": break;
        case "web-worker": break;
    }
}

export type HttpMethodCallOptions<T extends (...args: any) => any> = NonNullable<Parameters<T>[0]>;
