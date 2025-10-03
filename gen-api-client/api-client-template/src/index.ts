import {
    GetSupportedImgFormatsErrors,
    GetSupportedImgFormatsResponses,
    PostLoginErrors,
    PostLoginResponses,
    PostRegisterErrors, PostRegisterResponses,
    PostSaltErrors, PostSaltResponses,
} from "./gen-client";
import { Config, createClient as createClientInner } from "./gen-client/client";
import {
    postRegister as postRegisterInner,
    postSalt as postSaltInner,
    postLogin as postLoginInner,
    getSupportedImgFormats as getSupportedImgFormatsInner,
} from "./gen-client/sdk.gen";
import { LikelyResponse, PostLoginResponse, PostRegisterResponse, PostSaltResponse } from "./gen_shared_types";

export * as "gen_shared_types" from "./gen_shared_types";

export function createClient(config: Config = {}): ReturnType<typeof createClientInner> {
    if (!config.baseUrl) {
        config.baseUrl = process.env.BASE_API_URL || "http://localhost:3000";
    }
    return createClientInner(config);
}

export async function postRegister(options: NonNullable<Parameters<typeof postRegisterInner>[0]>): Promise<PostRegisterResponse> {
    if (!options.client) {
        options.client = createClient();
    }
    const result = await postRegisterInner(options);
    const statusCode = result.response.status as keyof PostRegisterResponses | keyof PostRegisterErrors;
    switch (statusCode) {
        case 200: return "Success";
        case 409: return "AlreadyExists";
        case 500: return "InternalServerError";
    }
}

export async function postSalt(options: NonNullable<Parameters<typeof postSaltInner>[0]>): Promise<PostSaltResponse> {
    if (!options.client) {
        options.client = createClient();
    }
    const result = await postSaltInner(options);
    const statusCode = result.response.status as keyof PostSaltResponses | keyof PostSaltErrors;
    switch (statusCode) {
        case 200: {
            const saltResponseSuccess: PostSaltResponses[200] = result.data!;
            return { "kind": "Success", "salt": saltResponseSuccess.salt };
        }
        case 404: return { "kind": "UserNotFound" };
        case 500: return { "kind": "InternalServerError" };
    };
}

export async function postLogin(options: NonNullable<Parameters<typeof postLoginInner>[0]>): Promise<PostLoginResponse> {
    if (!options.client) {
        options.client = createClient();
    }
    const result = await postLoginInner(options);
    const statusCode = result.response.status as keyof PostLoginResponses | keyof PostLoginErrors;
    switch (statusCode) {
        case 200: {
            const loginResponseSuccess: PostLoginResponses[200] = result.data!;
            return { "kind": "Success", "jwt": loginResponseSuccess.jwt };
        }
        case 401: return { "kind": "InvalidCredentials" };
        case 500: return { "kind": "InternalServerError" };
    }
}

export async function getSupportedImgFormats(
    options: NonNullable<Parameters<typeof getSupportedImgFormatsInner>[0]>
): Promise<LikelyResponse<string>> {
    if (!options.client) {
        options.client = createClient();
    }
    const result = await getSupportedImgFormatsInner(options);
    const statusCode = result.response.status as keyof GetSupportedImgFormatsResponses | keyof GetSupportedImgFormatsErrors;
    switch (statusCode) {
        case 200: {
            const responseSuccess: GetSupportedImgFormatsResponses[200] = result.data!;
            return { "kind": "Success", "value": responseSuccess };
        }
        case 500: return { "kind": "InternalServerError" };
    }
}
