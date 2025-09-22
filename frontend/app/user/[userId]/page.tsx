"use server";

import { cookies } from "next/headers";

import Footer from "@/app/_components/Footer";
import TopNavBar from "@/app/_components/TopNavBar";
import { Cookies } from "@/app/_util/cookies";

type UserPageProps = {
    params: Promise<{
        userId: string;
    }>
};

export default async function UserPage({ params }: UserPageProps) {
    const { userId } = await params;
    const cookieStore = await cookies();
    const accessToken = cookieStore.get(Cookies.ACCESS_TOKEN);
    console.log("Access token:", accessToken);
    const loggedIn = !!accessToken;
    console.log("Logged in:", loggedIn);

    return (
        <div className="font-sans grid grid-rows-[auto_1fr_auto] justify-items-center min-h-screen">
            {/* Navigation Bar */}
            <TopNavBar userInfo={{ loggedIn }} />
            {/* Main Content */}
            <main>
                <h1>User Profile for user with id {userId}</h1>
                {/* Render user information */}
            </main>
            {/* Footer */}
            <Footer />
        </div>
    );
}
