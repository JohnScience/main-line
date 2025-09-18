import {
    PostRegisterErrors, PostRegisterResponses,
    PostSaltErrors, PostSaltResponses,
} from "./gen-client";
import { Config, createClient as createClientInner } from "./gen-client/client";
import {
    postRegister as postRegisterInner,
    postSalt as postSaltInner
} from "./gen-client/sdk.gen";
import { PostRegisterResponse, PostSaltResponse } from "./gen_shared_types";

export function createClient(config: Config = {}): ReturnType<typeof createClientInner> {
    if (!config.baseUrl) {
        config.baseUrl = process.env.BASE_API_URL || "http://localhost:3000";
    }
    return createClientInner(config);
}

export async function postRegister(options: Parameters<typeof postRegisterInner>[0]): Promise<PostRegisterResponse> {
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

export async function postSalt(options: Parameters<typeof postSaltInner>[0]): Promise<PostSaltResponse> {
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
