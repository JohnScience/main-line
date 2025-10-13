import {
    GetSupportedImgFormatsErrors,
    GetSupportedImgFormatsResponses,
    GetUserPageDataErrors,
    GetUserPageDataResponses,
    PostLoginErrors,
    PostLoginResponses,
    PostRegisterErrors, PostRegisterResponses,
    PostSaltErrors, PostSaltResponses,
    PostUploadUserAvatarErrors,
    PostUploadUserAvatarResponses,
} from "./gen-client";
import {
    postRegister as postRegisterInner,
    postSalt as postSaltInner,
    postLogin as postLoginInner,
    getSupportedImgFormats as getSupportedImgFormatsInner,
    postUploadUserAvatar as postUploadUserAvatarInner,
    getUserPageData as getUserPageDataInner,
} from "./gen-client/sdk.gen";
import { GetUserPageDataResponse, JwtString, LikelyResponse, PostLoginResponse, PostRegisterResponse, PostSaltResponse, PostUploadUserAvatarResponse } from "./gen_shared_types";

export * as "gen_shared_types" from "./gen_shared_types";

import { HttpMethodCallOptions, modifyOptions, RuntimeEnvironment } from "./common";

export async function postRegister(
    options: HttpMethodCallOptions<typeof postRegisterInner>
): Promise<PostRegisterResponse> {
    modifyOptions(options);
    const result = await postRegisterInner(options);
    const statusCode = result.response.status as keyof PostRegisterResponses | keyof PostRegisterErrors;
    switch (statusCode) {
        case 200: return "Success";
        case 409: return "AlreadyExists";
        case 500: return "InternalServerError";
    }
}

export async function postSalt(
    options: HttpMethodCallOptions<typeof postSaltInner>
): Promise<PostSaltResponse> {
    modifyOptions(options);
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

export async function postLogin(
    options: HttpMethodCallOptions<typeof postLoginInner>
): Promise<PostLoginResponse> {
    modifyOptions(options);
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
    options: HttpMethodCallOptions<typeof getSupportedImgFormatsInner>
): Promise<LikelyResponse<string>> {
    modifyOptions(options);
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

type PostUploadUserAvatarResult =
    | { kind: "Success" }
    | { kind: "BadRequest"; detail: string }
    | { kind: "Unauthorized" }
    | { kind: "InternalServerError"; detail?: string };

export async function postUploadUserAvatar(
    options: HttpMethodCallOptions<typeof postUploadUserAvatarInner>
): Promise<PostUploadUserAvatarResponse> {
    modifyOptions(options);
    const result = await postUploadUserAvatarInner(options as any);
    const statusCode = result.response.status as keyof PostUploadUserAvatarResponses | keyof PostUploadUserAvatarErrors;
    switch (statusCode) {
        case 200: {
            const url: PostUploadUserAvatarResponses[200] = result.data!;
            return { "kind": "Success", url };
        }
        case 400: {
            const detail: PostUploadUserAvatarErrors[400] = result.error!;
            return { "kind": "BadRequest", detail };
        };
        case 401: {
            const detail: PostUploadUserAvatarErrors[401] = result.error!;
            return { "kind": "Unauthorized", detail };
        };
        case 500: {
            const detail: PostUploadUserAvatarErrors[500] = result.error!;
            return { "kind": "InternalServerError", ...{ detail } };
        };
    }
}

export async function getUserPageData(
    options: HttpMethodCallOptions<typeof getUserPageDataInner>
): Promise<GetUserPageDataResponse> {
    modifyOptions(options);
    const result = await getUserPageDataInner(options);
    const statusCode = result.response.status as keyof GetUserPageDataResponses | keyof GetUserPageDataErrors;
    switch (statusCode) {
        case 200: {
            const responseSuccess: GetUserPageDataResponses[200] = result.data!;
            return { "kind": "Success", ...responseSuccess };
        }
        case 404: return { "kind": "NotFound" };
        case 500: return { "kind": "InternalServerError" };
    }
}
