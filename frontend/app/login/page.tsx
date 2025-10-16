"use server";

import { redirect } from "next/navigation";

import { JwtClaims, UserId } from "api-client/build/gen_shared_types";

import TopNavBar from "@/app/_components/TopNavBar";
import Footer from "@/app/_components/Footer";
import { Cookies, getWrappedTypedCookie } from "@/app/_util/cookies";

import LoginForm from "./LoginForm";

export default async function Login() {
    const claims: JwtClaims | null = await getWrappedTypedCookie(Cookies.ACCESS_TOKEN, "frontend-server").value ?? null;

    if (claims) {
        const userId: UserId = claims.sub;
        redirect(`/user/${userId}`);
    }

    return (
        <>
            <div className="font-sans grid grid-rows-[auto_1fr_20px] items-center justify-items-center min-h-screen">
                {/* Navigation Bar */}
                <TopNavBar userInfo={{ claims, avatarSource: null }} />

                {/* Main Content */}
                <main className="row-start-2 w-full max-w-md" >

                    <LoginForm />
                </main>

                {/* Footer */}
                <Footer />
            </div>
        </>
    );
}
