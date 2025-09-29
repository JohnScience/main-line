"use client";

import { redirect } from "next/navigation";

import { ReactNode } from "react";

import { Cookies } from "../_util/cookies";

type LogoutButtonProps = {
    children?: ReactNode;
    onLogout?: () => void;
}

export function LogoutButton({ children, onLogout }: LogoutButtonProps) {

    async function logout() {
        // At the time of writing,
        // CookieStore API has 90% support, according to
        // https://caniuse.com/cookie-store-api
        await window.cookieStore.delete(Cookies.ACCESS_TOKEN);
        onLogout?.();
        redirect("/login");
    }

    return <button
        className="flex items-center gap-2 hover:underline hover:underline-offset-4 cursor-pointer"
        onClick={logout}
        type="button"
    >
        {children}
    </button>
}