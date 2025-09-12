"use client";

import { z } from "zod/v4";
import { FormEvent, useState } from "react";
import Form from "next/form";
import { handleLogin } from "./actions";
import { Toaster, toast } from "sonner";
import { MAX_CHESS_DOT_COM_USERNAME_LENGTH, MAX_LICHESS_USERNAME_LENGTH, MAX_PASSWORD_LENGTH, MAX_USERNAME_LENGTH, MIN_CHESS_DOT_COM_USERNAME_LENGTH, MIN_LICHESS_USERNAME_LENGTH, MIN_PASSWORD_LENGTH, MIN_USERNAME_LENGTH } from "./config";
import { LoginError } from "./shared";

interface BaseLoginInfo {
    username: string;
    password: string;
}

interface OptionalSignupFields {
    chessDotComUsername?: string;
    lichessUsername?: string;
}

export type LoginTab = "signIn" | "signUp";

export type LoginInfo = BaseLoginInfo & (
    {
        tab: "signIn"
    } | {
        tab: "signUp"
    } & OptionalSignupFields
);

const loginErrorSchema: z.ZodEnum<typeof LoginError> = z.enum(LoginError);

// Based on <https://stackoverflow.com/a/31376894/8341513>
function disableEmptyInputs(event: FormEvent<HTMLFormElement>) {
    const controls = event.currentTarget.elements;
    for (let i = 0, iLen = controls.length; i < iLen; i++) {
        const el = controls[i] as HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement;
        if ('value' in el) {
            el.disabled = el.value == '';
        }
    }
}

async function handleLoginWrapper(formData: FormData) {
    "use client";
    try {
        await handleLogin(formData);
        toast.success("Login successful!");
    } catch (error) {
        if (!(error instanceof Error)) {
            toast.error(`An unknown error returned from ${handleLogin.name}`);
            return;
        }
        const parsedError = loginErrorSchema.safeParse(error.message);
        if (!parsedError.success) {
            toast.error(`Couldn't parse the error returned from ${handleLogin.name}: ${error.message}`);
            console.error(parsedError.error.issues);
            console.error(error.message);
            return;
        }
        toast.error(`Login failed: ${parsedError.data}`);
    }
}

export default function LoginForm() {
    const [loginInfo, setLoginInfo] = useState<Partial<LoginInfo> & { tab: LoginTab }>({
        tab: "signIn",
    });

    return (
        <>
            <Toaster position="top-right" />

            <div className="w-full max-w-2xl bg-white shadow-md rounded-lg p-6">
                {/* Tabs */}
                <div className="flex mb-6 border-b border-gray-200">
                    <button
                        className={`flex-1 py-2 text-center ${loginInfo.tab === "signIn"
                            ? "border-b-2 border-blue-500 font-semibold"
                            : "text-gray-500"
                            }`}
                        onClick={() => setLoginInfo({ ...loginInfo, tab: "signIn" })}
                    >
                        Sign In
                    </button>
                    <button
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
                        action={handleLoginWrapper}
                        className="flex flex-col gap-4"
                        onSubmit={disableEmptyInputs}
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
                        <Form action={handleLoginWrapper} className="flex flex-col gap-4">
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
