"use server";

import { z } from "zod/v4";
import { MAX_CHESS_DOT_COM_USERNAME_LENGTH, MAX_LICHESS_USERNAME_LENGTH, MAX_PASSWORD_LENGTH, MAX_USERNAME_LENGTH, MIN_CHESS_DOT_COM_USERNAME_LENGTH, MIN_LICHESS_USERNAME_LENGTH, MIN_PASSWORD_LENGTH, MIN_USERNAME_LENGTH } from "./config";
import { LoginInfo } from "./LoginForm";
import { LoginError } from "./shared";
import { postLogin, postRegister } from "api-client";
import { JwtClaims, JwtString } from "api-client/build/gen_shared_types";
import { cookies } from "next/headers";
import { jwtDecode } from "jwt-decode";
import { redirect } from "next/navigation";

// This function creates a Zod refinement function that checks the length of an optional field
// submitted through a form. Sadly, Next.js's `<Form>` component submits empty optional fields as empty strings.
//
// This function exists because the trick described in
// <https://stackoverflow.com/questions/31376217/how-to-not-pass-empty-input-fields-in-html-form/31376397>
// doesn't work with `onSubmit` field of Next.js's `<Form>` component.
function makeOptionalFieldLengthCheckRefinement(
    fieldName: string,
    min: number,
    max: number,
): (val: string, ctx: z.RefinementCtx) => void {
    return (val: string, ctx: z.RefinementCtx) => {
        // If the field is an empty string, it means the user didn't fill it out
        // and since it's optional, we don't need to validate it
        if (val.length === 0) {
            return;
        }

        if (val.length < min) {
            ctx.addIssue({
                code: "too_small",
                minimum: min,
                type: "string",
                inclusive: true,
                message: `Field '${fieldName}' must be at least ${min} characters long`,
                origin: "custom",
            });
        }

        if (val.length > max) {
            ctx.addIssue({
                code: "too_big",
                maximum: max,
                type: "string",
                inclusive: true,
                message: `Field '${fieldName}' must be at most ${max} characters long`,
                origin: "custom",
            });
        }
    }
}

const loginInfoSchema = z.union([
    z.object({
        tab: z.literal("signIn"),
        username: z.string().min(MIN_USERNAME_LENGTH).max(MAX_USERNAME_LENGTH),
        password_hash: z.string(),
    }),
    z.object({
        tab: z.literal("signUp"),
        username: z.string().min(MIN_USERNAME_LENGTH).max(MAX_USERNAME_LENGTH),
        password_hash: z.string(),
        chessDotComUsername: z.string().superRefine(makeOptionalFieldLengthCheckRefinement(
            "chessDotComUsername",
            MIN_CHESS_DOT_COM_USERNAME_LENGTH,
            MAX_CHESS_DOT_COM_USERNAME_LENGTH,
        )).optional(),
        lichessUsername: z.string().superRefine(makeOptionalFieldLengthCheckRefinement(
            "lichessUsername",
            MIN_LICHESS_USERNAME_LENGTH,
            MAX_LICHESS_USERNAME_LENGTH,
        )).optional(),
    })
]) satisfies z.ZodType<LoginInfo<"server">>;

export type LoginOutcome = {
    kind: "Success";
    jwt: JwtString;
} | {
    kind: "Error";
    error: LoginError;
}

async function handleSuccessfulLogin(
    jwt: JwtString,
): Promise<{ kind: "Success"; jwt: JwtString; }> {
    const ret = { kind: "Success", jwt } as const;
    const claims = jwtDecode<JwtClaims>(jwt);
    let exp: number | undefined = undefined;
    if (BigInt(Number.MAX_SAFE_INTEGER) > BigInt(claims.exp as any)) {
        exp = Number(claims.exp);
    } else {
        console.warn("JWT exp claim is too large to be represented as a JavaScript number.");
    }
    (await cookies()).set("access_token", jwt, {
        expires: new Date().setUTCMilliseconds(exp ?? 0)
    });
    return ret;
}

async function performServerLoginAttempt(loginInfo: LoginInfo<"server">): Promise<LoginOutcome> {
    const res = await postLogin({
        body: {
            username: loginInfo.username,
            password_hash: loginInfo.password_hash,
        }
    });
    switch (res.kind) {
        case "Success": return handleSuccessfulLogin(res.jwt);
        case "InvalidCredentials": {
            if (loginInfo.tab === "signUp") {
                console.error("Just registered user, but got invalid credentials when trying to log in.");
            }
            return { kind: "Error", error: LoginError.INVALID_CREDENTIALS };
        };
        case "InternalServerError": return { kind: "Error", error: LoginError.INTERNAL_SERVER_ERROR };
    };
}

// Handles both signing in and signing up.
export async function handleClientLoginAttempt(previousState: unknown, loginFormData: FormData): Promise<LoginOutcome> {
    const formObj = Object.fromEntries(loginFormData.entries());
    const loginInfoRes: z.ZodSafeParseResult<LoginInfo<"server">> = loginInfoSchema.safeParse(formObj);

    if (!loginInfoRes.success) {
        console.error(loginInfoRes.error.issues);
        return { kind: "Error", error: LoginError.INVALID_FORM_OBJECT };
    }

    if ((await cookies()).get("access_token")?.value) {
        const ret = { kind: "Error", error: LoginError.ALREADY_LOGGED_IN };
        console.error(`User ${loginInfoRes.data.username} is already logged in.`);
        // TODO: navigate to their page
        redirect("/")
    }

    switch (loginInfoRes.data.tab) {
        case "signUp": {
            const registrationResult = await postRegister({
                body: {
                    username: loginInfoRes.data.username,
                    password_hash: loginInfoRes.data.password_hash,
                }
            });

            switch (registrationResult) {
                case "Success":
                    break;
                case "AlreadyExists":
                    return { kind: "Error", error: LoginError.USER_ALREADY_EXISTS };
                case "InternalServerError":
                    return { kind: "Error", error: LoginError.INTERNAL_SERVER_ERROR };
            }

            return performServerLoginAttempt(loginInfoRes.data);
        }
        case "signIn": return performServerLoginAttempt(loginInfoRes.data);
    };
}
