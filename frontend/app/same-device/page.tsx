"use server";

import { cookies } from "next/headers";

import React from "react";

import Footer from "@/app/_components/Footer";
import TopNavBar from "@/app/_components/TopNavBar";
import { Cookies, getWrappedTypedCookie } from "@/app/_util/cookies";

import Chessboard from "./Chessboard";
import { JwtClaims } from "api-client/build/gen_shared_types";

type UserPageProps = {
    params: Promise<{
        userId: string;
    }>
};

export default async function UserPage({ params }: UserPageProps) {
    const { userId } = await params;
    const claims: JwtClaims | null = await getWrappedTypedCookie(Cookies.ACCESS_TOKEN, "frontend-server").value ?? null;

    return (
        <div className="font-sans grid grid-rows-[auto_1fr_auto] justify-items-center min-h-screen">
            {/* Navigation Bar */}
            <TopNavBar userInfo={{ claims, avatarSource: null }} />
            {/* Main Content */}
            <main className="flex items-center justify-center">
                <Chessboard />
                {/* Render user information */}
            </main>
            {/* Footer */}
            <Footer />
        </div>
    );
}
