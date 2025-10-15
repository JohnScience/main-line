"use client";

import Form from "next/form";

import { FormEvent, startTransition, useActionState, useEffect, useState } from "react";

import { Toaster, toast } from "sonner";
import type { Argon2BrowserHashOptions, Argon2BrowserHashResult } from "argon2-browser";
import argon2 from "argon2-browser/dist/argon2-bundled.min.js";
import { jwtDecode } from "jwt-decode";

import { postSalt } from "api-client";
import { JwtClaims } from "api-client/build/gen_shared_types";

import { OptionalKeys } from "@/app/_util/types";
import { base64ToUint8Array } from "@/app/_util/base64";

import { handleClientLoginAttempt } from "./actions";
import { MAX_CHESS_DOT_COM_USERNAME_LENGTH, MAX_LICHESS_USERNAME_LENGTH, MAX_PASSWORD_LENGTH, MAX_USERNAME_LENGTH, MIN_CHESS_DOT_COM_USERNAME_LENGTH, MIN_LICHESS_USERNAME_LENGTH, MIN_PASSWORD_LENGTH, MIN_USERNAME_LENGTH } from "./config";
import { LoadingSpinner } from "@/app/_components/LoadingSpinner";

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

function makeOnSignInSubmit(handleLoginAction: (formData: FormData) => Promise<any>) {
    return async function onSignInSubmit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        disableEmptyInputs(event);
        const formData = new FormData(event.currentTarget);
        const entries: Extract<LoginInfo<"client">, { tab: "signIn" }> = Object.fromEntries(formData.entries()) as any;

        const saltResp = await postSalt({
            body: { username: entries.username }
        });

        console.log(`Received salt response for user ${entries.username}:`, saltResp);

        if (saltResp.kind != "Success") {
            toast.error(`Failed to obtain the salt for user ${entries.username}. Error: ${saltResp.kind}`);
            return false;
        }

        console.log(`Hashing password for user ${entries.username} with received salt.`);

        const salt: Uint8Array = base64ToUint8Array(saltResp.salt);

        const hashResult: Argon2BrowserHashResult = await argon2.hash({
            ...argon2Opts,
            pass: entries.password,
            salt,
        });

        console.log(`Received hash result for user ${entries.username}:`, hashResult);

        const modifiedEntries: Extract<LoginInfo<"server">, { tab: "signIn" }> = {
            tab: entries.tab,
            username: entries.username,
            password_hash: hashResult.encoded,
        };

        const modifiedFormData = new FormData();

        for (const [key, value] of Object.entries(modifiedEntries)) {
            modifiedFormData.append(key, value);
        }

        startTransition(() => {
            handleLoginAction(modifiedFormData);
        });
    }
}


function makeOnSignUpSubmit(handleLoginAction: (formData: FormData) => Promise<any>) {
    return async function onSignUpSubmit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        disableEmptyInputs(event);
        const formData = new FormData(event.currentTarget);
        const entries: Extract<LoginInfo<"client">, { tab: "signUp" }> = Object.fromEntries(formData.entries()) as any;

        const salt = crypto.getRandomValues(new Uint8Array(16));

        const res: Argon2BrowserHashResult = await argon2.hash({
            ...argon2Opts,
            pass: entries.password,
            salt,
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
    const [loginOutcome, handleLoginAction, isLoginPending] = useActionState(handleClientLoginAttempt, undefined);
    useEffect(() => {
        if (loginOutcome !== undefined) {
            console.log('loginOutcome:', loginOutcome);
            // Handle the login outcome (success or error)
            if (loginOutcome.kind === "Success") {
                toast.success("Login successful!");
                console.log(loginOutcome.jwt);
                const claims = jwtDecode<JwtClaims>(loginOutcome.jwt);
                console.log('Decoded JWT claims:', claims);
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
                        onSubmit={makeOnSignInSubmit(async (formData) => await handleLoginAction(formData))}
                    >
                        <input type="hidden" name="tab" value={loginInfo.tab} />
                        <input
                            type="text"
                            placeholder="Username"
                            autoComplete="username"
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
                            disabled={isLoginPending}
                        >
                            {isLoginPending ? <LoadingSpinner inline={true} size="w-6 h-6" /> : "Sign In"}
                        </button>
                    </Form>
                ) : (
                    <>
                        {/* TODO: find a way to avoid sending empty strings for optional fields */}
                        <Form
                            action={handleLoginAction}
                            className="flex flex-col gap-4"
                            onSubmit={makeOnSignUpSubmit(async (formData) => await handleLoginAction(formData))}
                        >
                            <input type="hidden" name="tab" value={loginInfo.tab} />
                            <input
                                type="text"
                                placeholder="Username"
                                className="border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                name="username"
                                autoComplete="username"
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
                            <p className="text-sm text-gray-500">
                                Note: Sign-up may take a while as we use OWASP-recommended Argon2id hashing algorithm, which is slow.
                            </p>
                            <button
                                type="submit"
                                className="bg-green-500 text-white py-2 rounded hover:bg-green-600 transition flex items-center justify-center"
                                disabled={isLoginPending}
                            >
                                {isLoginPending ? <LoadingSpinner inline={true} size="w-6 h-6" /> : "Sign Up"}
                            </button>
                        </Form>
                    </>
                )}
            </div>
        </>
    );
}
