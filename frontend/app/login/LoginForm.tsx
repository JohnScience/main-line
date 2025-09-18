"use client";

import { z } from "zod/v4";
import { FormEvent, startTransition, useActionState, useEffect, useState } from "react";
import Form from "next/form";
import { handleLogin } from "./actions";
import { Toaster, toast } from "sonner";
import { MAX_CHESS_DOT_COM_USERNAME_LENGTH, MAX_LICHESS_USERNAME_LENGTH, MAX_PASSWORD_LENGTH, MAX_USERNAME_LENGTH, MIN_CHESS_DOT_COM_USERNAME_LENGTH, MIN_LICHESS_USERNAME_LENGTH, MIN_PASSWORD_LENGTH, MIN_USERNAME_LENGTH } from "./config";
import { LoginError } from "./shared";
import argon2, { Argon2BrowserHashOptions, Argon2BrowserHashResult } from "argon2-browser";
import { postSalt } from "api-client";
import { OptionalKeys, OptionalProps } from "../_util/types";

type PasswordFragment<T extends "client" | "server"> = T extends "client" ? { password: string } : { password_hash: string };

type BaseLoginInfo<T extends "client" | "server"> = {
    username: string;
} & PasswordFragment<T>;

interface OptionalSignupFields {
    chessDotComUsername?: string;
    lichessUsername?: string;
}

export type LoginTab = "signIn" | "signUp";

export type LoginInfo<T extends "client" | "server"> = BaseLoginInfo<T> & (
    {
        tab: "signIn"
    } | {
        tab: "signUp"
    } & OptionalSignupFields
);

const loginErrorSchema: z.ZodEnum<typeof LoginError> = z.enum(LoginError);

const argon2Opts: Omit<Argon2BrowserHashOptions, "pass" | "salt"> = {
    time: 1,
    mem: 1_048_576, // 100 MB
    hashLen: 32,
    parallelism: 1,
    type: argon2.ArgonType.Argon2id,
};

// Based on <https://stackoverflow.com/a/31376894/8341513>
function disableEmptyInputs(event: FormEvent<HTMLFormElement>) {
    const controls = event.currentTarget.elements;
    for (let i = 0, iLen = controls.length; i < iLen; i++) {
        const el = controls[i] as HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement;
        if ("type" in el && el["type"] === "text" && "name" in el && 'value' in el && el.value == "") {
            el.disabled = true;
        }
    }
}

async function onSignInSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    disableEmptyInputs(event);
    const formData = new FormData(event.currentTarget);
    const entries: Extract<LoginInfo<"client">, { tab: "signIn" }> = Object.fromEntries(formData.entries()) as any;

    const saltResp = await postSalt({
        body: { username: entries.username }
    });

    if (saltResp.kind != "Success") {
        toast.error(`Failed to obtain the salt for user ${entries.username}. Error: ${saltResp.kind}`);
        return false;
    }

    const hashResult: Argon2BrowserHashResult = await argon2.hash({
        ...argon2Opts,
        pass: entries.password,
        salt: saltResp.salt,
    });

    const modifiedEntries: Extract<LoginInfo<"server">, { tab: "signIn" }> = {
        tab: entries.tab,
        username: entries.username,
        password_hash: hashResult.encoded,
    };

    const modifiedFormData = new FormData();

    for (const [key, value] of Object.entries(modifiedEntries)) {
        modifiedFormData.append(key, value);
    }

    return modifiedFormData;
}


function makeSignUpSubmit(handleLoginAction: (formData: FormData) => Promise<any>) {
    return async function onSignUpSubmit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        disableEmptyInputs(event);
        const formData = new FormData(event.currentTarget);
        const entries: Extract<LoginInfo<"client">, { tab: "signUp" }> = Object.fromEntries(formData.entries()) as any;

        const res: Argon2BrowserHashResult = await argon2.hash({
            ...argon2Opts,
            pass: entries.password,
            salt: crypto.getRandomValues(new Uint8Array(16))
        });

        const modifiedEntries: Extract<LoginInfo<"server">, { tab: "signUp" }> = {
            tab: entries.tab,
            username: entries.username,
            password_hash: res.encoded,
        };

        const optionalKeys: OptionalKeys<Extract<LoginInfo<"server">, { tab: "signUp" }>>[] =
            ["chessDotComUsername", "lichessUsername"];

        for (const key of optionalKeys) {
            if (entries[key]) {
                modifiedEntries[key] = entries[key];
            }
        }

        const modifiedFormData = new FormData();
        for (const [key, value] of Object.entries(modifiedEntries)) {
            if (value !== undefined) {
                modifiedFormData.append(key, value);
            }
        }
        startTransition(() => {
            handleLoginAction(modifiedFormData);
        });
    };
}

export default function LoginForm() {
    const [loginInfo, setLoginInfo] = useState<Partial<LoginInfo<"client">> & { tab: LoginTab }>({
        tab: "signIn",
    });
    const [loginOutcome, handleLoginAction, isLoginPending] = useActionState(handleLogin, undefined);
    useEffect(() => {
        if (loginOutcome !== undefined) {
            console.log('loginOutcome:', loginOutcome);
            // Handle the login outcome (success or error)
            if (loginOutcome.kind === "success") {
                toast.success("Login successful!");
            } else {
                toast.error(`Login failed: ${loginOutcome.error}`);
            }
        }
    }, [loginOutcome]);

    return (
        <>
            <Toaster position="top-right" />

            <div className="w-full max-w-2xl bg-white shadow-md rounded-lg p-6">
                {/* Tabs */}
                <div className="flex mb-6 border-b border-gray-200">
                    <button
                        type="button"
                        className={`flex-1 py-2 text-center ${loginInfo.tab === "signIn"
                            ? "border-b-2 border-blue-500 font-semibold"
                            : "text-gray-500"
                            }`}
                        onClick={() => setLoginInfo({ ...loginInfo, tab: "signIn" })}
                    >
                        Sign In
                    </button>
                    <button
                        type="button"
                        className={`flex-1 py-2 text-center ${loginInfo.tab === "signUp"
                            ? "border-b-2 border-blue-500 font-semibold"
                            : "text-gray-500"
                            }`}
                        onClick={() => setLoginInfo({ ...loginInfo, tab: "signUp" })}
                    >
                        Sign Up
                    </button>
                </div>

                {/* Forms */}
                {loginInfo.tab === "signIn" ? (
                    <Form
                        action={handleLoginAction}
                        className="flex flex-col gap-4"
                        onSubmit={onSignInSubmit}
                    >
                        <input type="hidden" name="tab" value={loginInfo.tab} />
                        <input
                            type="text"
                            placeholder="Username"
                            className="border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            name="username"
                            minLength={MIN_USERNAME_LENGTH}
                            maxLength={MAX_USERNAME_LENGTH}
                            required
                        />
                        <input
                            type="password"
                            placeholder="Password"
                            className="border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            name="password"
                            autoComplete="current-password"
                            minLength={MIN_PASSWORD_LENGTH}
                            maxLength={MAX_PASSWORD_LENGTH}
                            required
                        />
                        <button
                            type="submit"
                            className="bg-blue-500 text-white py-2 rounded hover:bg-blue-600 transition"
                        >
                            Sign In
                        </button>
                    </Form>
                ) : (
                    <>
                        {/* TODO: find a way to avoid sending empty strings for optional fields */}
                        <Form
                            action={handleLoginAction}
                            className="flex flex-col gap-4"
                            onSubmit={makeSignUpSubmit(async (formData) => await handleLoginAction(formData))}
                        >
                            <input type="hidden" name="tab" value={loginInfo.tab} />
                            <input
                                type="text"
                                placeholder="Username"
                                className="border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                name="username"
                                minLength={MIN_USERNAME_LENGTH}
                                maxLength={MAX_USERNAME_LENGTH}
                                required
                            />
                            <input
                                type="password"
                                placeholder="Password"
                                className="border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                name="password"
                                autoComplete="new-password"
                                minLength={MIN_PASSWORD_LENGTH}
                                maxLength={MAX_PASSWORD_LENGTH}
                                required
                            />
                            <input
                                type="text"
                                placeholder="Chess.com Username (optional)"
                                className="border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                name="chessDotComUsername"
                                minLength={MIN_CHESS_DOT_COM_USERNAME_LENGTH}
                                maxLength={MAX_CHESS_DOT_COM_USERNAME_LENGTH}
                            />
                            <input
                                type="text"
                                placeholder="Lichess.org Username (optional)"
                                className="border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                name="lichessDotOrgUsername"
                                minLength={MIN_LICHESS_USERNAME_LENGTH}
                                maxLength={MAX_LICHESS_USERNAME_LENGTH}
                            />
                            <button
                                type="submit"
                                className="bg-green-500 text-white py-2 rounded hover:bg-green-600 transition"
                            >
                                Sign Up
                            </button>
                        </Form>
                    </>
                )}
            </div>
        </>
    );
}
