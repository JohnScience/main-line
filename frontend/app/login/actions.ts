"use server";

import { z } from "zod/v4";
import { MAX_CHESS_DOT_COM_USERNAME_LENGTH, MAX_LICHESS_USERNAME_LENGTH, MAX_PASSWORD_LENGTH, MAX_USERNAME_LENGTH, MIN_CHESS_DOT_COM_USERNAME_LENGTH, MIN_LICHESS_USERNAME_LENGTH, MIN_PASSWORD_LENGTH, MIN_USERNAME_LENGTH } from "./config";
import { LoginInfo } from "./LoginForm";
import { LoginError } from "./shared";
import { postRegister } from "api-client";

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
        password: z.string().min(MIN_PASSWORD_LENGTH).max(MAX_PASSWORD_LENGTH),
    }),
    z.object({
        tab: z.literal("signUp"),
        username: z.string().min(MIN_USERNAME_LENGTH).max(MAX_USERNAME_LENGTH),
        password: z.string().min(MIN_PASSWORD_LENGTH).max(MAX_PASSWORD_LENGTH),
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
]) satisfies z.ZodType<LoginInfo>;

export type LoginOutcome = {
    kind: "success";
} | {
    kind: "error";
    error: LoginError;
}

// Handles both signing in and signing up.
export async function handleLogin(previousState: unknown, loginFormData: FormData): Promise<LoginOutcome> {
    const formObj = Object.fromEntries(loginFormData.entries());
    const loginInfoRes: z.ZodSafeParseResult<LoginInfo> = loginInfoSchema.safeParse(formObj);

    if (!loginInfoRes.success) {
        console.error(loginInfoRes.error.issues);
        return { kind: "error", error: LoginError.INVALID_FORM_OBJECT };
    }

    if (loginInfoRes.data.tab === "signUp") {
        const res = await postRegister({
            body: {
                username: loginInfoRes.data.username,
                password_hash: loginInfoRes.data.password, // TODO: hash the password
            }
        });

        console.log('postRegister result:', res);

        switch (res) {
            case "Success":
                return { kind: "success" };
            case "AlreadyExists":
                return { kind: "error", error: LoginError.USER_ALREADY_EXISTS };
            case "InternalServerError":
                return { kind: "error", error: LoginError.INTERNAL_SERVER_ERROR };
        }
    } else {
        // TODO: handle sign in
        return { kind: "error", error: LoginError.INTERNAL_SERVER_ERROR }
    }
}
