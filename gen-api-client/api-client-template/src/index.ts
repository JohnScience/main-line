import { PostRegisterErrors, PostRegisterResponses } from "./gen-client";
import { Config, createClient as createClientInner } from "./gen-client/client";
import { postRegister as postRegisterInner } from "./gen-client/sdk.gen";
import { PostRegisterResponse } from "./gen_shared_types";

export function createClient(config: Config = {}): ReturnType<typeof createClientInner> {
    if (!config.baseUrl) {
        config.baseUrl = process.env.API_BASE_URL || "http://localhost:3000";
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
        case 200: "Success";
        case 409: return "AlreadyExists";
        case 500: return "InternalServerError";
    }
}

async function main() {
    const options: Parameters<typeof postRegisterInner>[0] = {
        body: {
            username: "testuser",
            password_hash: "testpassword",
        }
    };
    const response = await postRegister(options);
    console.log(response);
}

main();