"use server";

import { cookies } from "next/headers";

import React from "react";

import Footer from "@/app/_components/Footer";
import TopNavBar from "@/app/_components/TopNavBar";
import { Cookies } from "@/app/_util/cookies";
import Chessboard from "./Chessboard";

type UserPageProps = {
    params: Promise<{
        userId: string;
    }>
};

export default async function UserPage({ params }: UserPageProps) {
    const { userId } = await params;
    const cookieStore = await cookies();
    const accessToken = cookieStore.get(Cookies.ACCESS_TOKEN);
    const loggedIn = !!accessToken;

    return (
        <div className="font-sans grid grid-rows-[auto_1fr_auto] justify-items-center min-h-screen">
            {/* Navigation Bar */}
            <TopNavBar userInfo={{ loggedIn }} />
            {/* Main Content */}
            <main>
                <Chessboard />
                {/* Render user information */}
            </main>
            {/* Footer */}
            <Footer />
        </div>
    );
}
