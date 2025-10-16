"use server";

import { redirect } from "next/navigation";

import { getSupportedImgFormats, getUserPageData } from "api-client";
import { JwtClaims, LikelyResponse, UserId } from "api-client/build/gen_shared_types";

import Footer from "@/app/_components/Footer";
import TopNavBar from "@/app/_components/TopNavBar";
import { Cookies, getWrappedTypedCookie } from "@/app/_util/cookies";
import { UserAvatar } from "./UserAvatar";

type UserPageProps = {
    params: Promise<{
        userId: string;
    }>
};

export default async function UserPage({ params }: UserPageProps) {
    const { userId: viewedUserId } = await params;
    const claims: JwtClaims | null = await getWrappedTypedCookie(Cookies.ACCESS_TOKEN, "frontend-server").value ?? null;
    const viewingUserId: UserId | undefined = claims?.sub;

    const supportedImgFormatsResp: LikelyResponse<string> = await getSupportedImgFormats({});

    let supportedImgFormats: string | null = null;

    switch (supportedImgFormatsResp.kind) {
        case "Success":
            supportedImgFormats = supportedImgFormatsResp.value;
            break;
        case "InternalServerError":
            redirect("/500");
    }

    let userPageData = await getUserPageData({
        path: { user_id: parseInt(viewedUserId) }
    });

    switch (userPageData.kind) {
        case "NotFound":
            console.warn(`Couldn't find the user with id ${parseInt(viewedUserId)}}`);
            redirect("/404");
        case "InternalServerError":
            redirect("/500");
        case "Success":
            break;
    };

    return (
        <div className="font-sans grid grid-rows-[auto_1fr_auto] justify-items-center min-h-screen">
            {/* Navigation Bar */}
            <TopNavBar userInfo={{ claims, avatarSource: null }} />
            {/* Main Content */}
            <main className="p-10 w-full">
                { /* User Profile Information */}
                <div className="min-h-[300px] w-full bg-blue-100 rounded-lg grid grid-cols-[275px_auto] items-center">
                    <div className="p-2">
                        <UserAvatar startingAvatarUrl={userPageData?.avatar_url || null} supportedImgFormats={supportedImgFormats} />
                    </div>
                    {/* Textual Information */}
                    <div className="h-full p-6">
                        <h2 className="text-2xl font-bold text-gray-800 mb-4">{`${parseInt(viewedUserId) == viewingUserId ? "Your" : `${userPageData?.username}'s`} Profile`}</h2>
                        <div className="space-y-3">
                            <div>
                                <span className="font-semibold text-gray-600">Username:</span>
                                <span className="ml-2 text-gray-800">{userPageData?.username}</span>
                            </div>
                            <div>
                                <span className="font-semibold text-gray-600">ID:</span>
                                <span className="ml-2 text-gray-800">{viewedUserId}</span>
                            </div>
                            <div>
                                <span className="font-semibold text-gray-600">Email:</span>
                                <span className="ml-2 text-gray-800">{userPageData?.email || "No email provided"}</span>
                            </div>
                            <div>
                                <span className="font-semibold text-gray-600">Chess.com Profile:</span>
                                <span className="ml-2 text-gray-800">{userPageData?.chess_dot_com_profile || "No profile linked"}</span>
                            </div>
                            <div>
                                <span className="font-semibold text-gray-600">Lichess.org Profile:</span>
                                <span className="ml-2 text-gray-800">{userPageData?.lichess_profile || "No profile linked"}</span>
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
