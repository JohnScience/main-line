import { JwtClaims } from "api-client/build/gen_shared_types";
import { checkRuntime, inferRuntimeEnvironment, RuntimeEnvironment } from "./runtime";
import { jwtDecode } from "jwt-decode";

export enum Cookies {
    ACCESS_TOKEN = "access_token",
}

const CookieMetadata = {
    [Cookies.ACCESS_TOKEN]: {
        kind: "jwt",
    }
};

type CookieTypeMap = {
    [Cookies.ACCESS_TOKEN]: JwtClaims;
}

export function getWrappedTypedCookie<
    C extends Cookies,
    R extends RuntimeEnvironment | undefined
>(
    cookie: C,
    runtime?: R
):
    R extends undefined ? {
        runtime: "browser";
        value: CookieTypeMap[typeof cookie] | undefined
    } | {
        runtime: "frontend-server";
        value: Promise<CookieTypeMap[typeof cookie] | undefined>
    }
    :
    R extends "browser" ? {
        value: CookieTypeMap[typeof cookie] | undefined
    }
    : R extends "frontend-server" ? {
        value: Promise<CookieTypeMap[typeof cookie] | undefined>
    }
    : never {
    // The runtime is checked by getCookieStr
    const wrappedStrCookie = getWrappedStrCookie(cookie, runtime);

    let wrappedTypedCookie: CookieTypeMap[typeof cookie] | undefined | Promise<CookieTypeMap[typeof cookie] | undefined>;

    switch (CookieMetadata[cookie].kind) {
        case "jwt": {
            if (wrappedStrCookie.value === undefined) {
                wrappedTypedCookie = undefined;
                break;
            }
            if (wrappedStrCookie.value instanceof Promise) {
                const fn = async () => {
                    const strCookie: string | undefined = await wrappedStrCookie.value;
                    if (strCookie === undefined) { return undefined; }
                    const claims = jwtDecode<CookieTypeMap[typeof cookie]>(strCookie);
                    return claims;
                };
                wrappedTypedCookie = fn();
                break;
            }

            if (typeof wrappedStrCookie.value !== "string") {
                throw new Error("Inconsistent state: expected string value for cookie");
            }

            wrappedTypedCookie = jwtDecode<CookieTypeMap[typeof cookie]>(wrappedStrCookie.value);
        }
    }

    if (runtime === undefined) {
        return {
            runtime: (wrappedStrCookie as ReturnType<typeof getWrappedStrCookie<undefined>>).runtime,
            value: wrappedTypedCookie as ReturnType<typeof getWrappedStrCookie<undefined>>["value"]
        } as any;
    } else {
        return { value: wrappedTypedCookie } as any;
    }
}

function getClientSideCookieStr(name: string): string | undefined {
    const cookieValue = document.cookie
        .split('; ')
        .find((row) => row.startsWith(`${name}=`))
        ?.split('=')[1];

    return cookieValue;
};

function getWrappedStrCookie<R extends RuntimeEnvironment | undefined>(
    name: string,
    runtime?: R
): R extends undefined
    ? {
        runtime: "browser";
        value: string | undefined
    } | {
        runtime: "frontend-server";
        value: Promise<string | undefined>
    }
    : R extends "browser"
    ? {
        value: string | undefined;
    }
    : R extends "frontend-server"
    ? {
        value: Promise<string | undefined>
    }
    : never {

    if (runtime !== undefined) {
        checkRuntime(runtime);
    }

    const knownRuntime: RuntimeEnvironment = runtime ?? inferRuntimeEnvironment();

    switch (knownRuntime) {
        case "browser": {
            const value = getClientSideCookieStr(name);
            return runtime === undefined
                ? ({ runtime: knownRuntime, value } as any)
                : ({ value } as any);
        }
        case "frontend-server": {
            const value = (async () => {
                const { cookies } = await import("next/headers");
                const cookieStore = await cookies();
                return cookieStore.get(name)?.value;
            })();
            return runtime === undefined
                ? ({ runtime: knownRuntime, value } as any)
                : ({ value } as any);
        }
        case "web-worker":
            throw new Error("Cookie access not supported in web workers");
        default:
            throw new Error(`Unsupported runtime environment: ${knownRuntime}`);
    }
}
