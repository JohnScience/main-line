"use server";

import { z } from "zod/v4";
import { MAX_CHESS_DOT_COM_USERNAME_LENGTH, MAX_LICHESS_USERNAME_LENGTH, MAX_PASSWORD_LENGTH, MAX_USERNAME_LENGTH, MIN_CHESS_DOT_COM_USERNAME_LENGTH, MIN_LICHESS_USERNAME_LENGTH, MIN_PASSWORD_LENGTH, MIN_USERNAME_LENGTH } from "./config";
import { LoginInfo } from "./LoginForm";
import { LoginError } from "./shared";

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
        chessDotComUsername: z.string().min(MIN_CHESS_DOT_COM_USERNAME_LENGTH).max(MAX_CHESS_DOT_COM_USERNAME_LENGTH),
        lichessUsername: z.string().min(MIN_LICHESS_USERNAME_LENGTH).max(MAX_LICHESS_USERNAME_LENGTH),
    })
]) satisfies z.ZodType<LoginInfo>;

export async function handleLogin(loginFormData: FormData) {
    // TODO: add error handling
    const loginInfoRes: z.ZodSafeParseResult<LoginInfo> = loginInfoSchema.safeParse(loginFormData);

    if (!loginInfoRes.success) {
        throw new Error(LoginError.ILLFORMED_CREDENTIALS);
    }

    // redirect(`/login?token=${jwt}`)
}
