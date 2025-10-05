"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { jwtDecode } from "jwt-decode";

import { getSupportedImgFormats } from "api-client";
import { JwtClaims, LikelyResponse, UserId } from "api-client/build/gen_shared_types";

import Footer from "@/app/_components/Footer";
import TopNavBar from "@/app/_components/TopNavBar";
import { Cookies } from "@/app/_util/cookies";
import { UserAvatar } from "./UserAvatar";

type UserPageProps = {
    params: Promise<{
        userId: string;
    }>
};

interface UserInfo {
    avatarUrl?: string;
    username: string;
    id: UserId;
    email?: string;
    chessDotComProfile?: string;
    lichessDotOrgProfile?: string;
}

export default async function UserPage({ params }: UserPageProps) {
    const { userId: viewedUserId } = await params;
    const cookieStore = await cookies();
    const accessToken = cookieStore.get(Cookies.ACCESS_TOKEN);
    let viewingUserId: UserId | null = null;
    if (accessToken) {
        const jwt = jwtDecode<JwtClaims>(accessToken.value);
        viewingUserId = jwt.sub;
    }
    const loggedIn = !!accessToken;

    const supportedImgFormatsResp: LikelyResponse<string> = await getSupportedImgFormats({});

    let supportedImgFormats: string | null = null;

    switch (supportedImgFormatsResp.kind) {
        case "Success":
            supportedImgFormats = supportedImgFormatsResp.value;
            break;
        case "InternalServerError":
            redirect("/500");
    }

    let userInfo: UserInfo | null = {
        // avatarUrl: `/api/users/${viewedUserId}/avatar`, // Example avatar URL
        username: `HardcodedName`,
        id: parseInt(viewedUserId)
    };

    return (
        <div className="font-sans grid grid-rows-[auto_1fr_auto] justify-items-center min-h-screen">
            {/* Navigation Bar */}
            <TopNavBar userInfo={{ loggedIn }} />
            {/* Main Content */}
            <main className="p-10 w-full">
                { /* User Profile Information */}
                <div className="min-h-[300px] w-full bg-blue-100 rounded-lg grid grid-cols-[275px_auto] items-center">
                    <div className="p-2">
                        <UserAvatar avatarUrl={userInfo?.avatarUrl || null} supportedImgFormats={supportedImgFormats} />
                    </div>
                    {/* Textual Information */}
                    <div className="h-full p-6">
                        <h2 className="text-2xl font-bold text-gray-800 mb-4">{`${userInfo?.id == viewingUserId ? "Your" : `${userInfo?.username}'s`} Profile`}</h2>
                        <div className="space-y-3">
                            <div>
                                <span className="font-semibold text-gray-600">Username:</span>
                                <span className="ml-2 text-gray-800">{userInfo?.username}</span>
                            </div>
                            <div>
                                <span className="font-semibold text-gray-600">ID:</span>
                                <span className="ml-2 text-gray-800">{userInfo?.id}</span>
                            </div>
                            <div>
                                <span className="font-semibold text-gray-600">Email:</span>
                                <span className="ml-2 text-gray-800">{userInfo?.email || "No email provided"}</span>
                            </div>
                            <div>
                                <span className="font-semibold text-gray-600">Chess.com Profile:</span>
                                <span className="ml-2 text-gray-800">{userInfo?.chessDotComProfile || "No profile linked"}</span>
                            </div>
                            <div>
                                <span className="font-semibold text-gray-600">Lichess.org Profile:</span>
                                <span className="ml-2 text-gray-800">{userInfo?.lichessDotOrgProfile || "No profile linked"}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
            {/* Footer */}
            <Footer />
        </div>
    );
}
