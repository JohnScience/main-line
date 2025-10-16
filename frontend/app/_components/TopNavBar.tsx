"use client";

import Image from "next/image";
import Link from "next/link";

import { useState } from "react";

import { Optional } from "@/app/_util/types";
import { inferRuntimeEnvironment } from "@/app/_util/runtime";
import { CONTACT_EMAIL } from "@/app/config";
import { LogoutButton } from "./LogoutButton";
import { JwtClaims } from "api-client/build/gen_shared_types";


const DEFAULT_AVATAR_SOURCE = "/account.svg";

export interface UserInfo {
    claims: JwtClaims | null;
    avatarSource: string | null;
}

interface Props {
    userInfo?: Partial<UserInfo>;
    contactEmail?: string;
    logoWidth?: number;
    logoHeight?: number;
}

const DEFAULT_USER_INFO: UserInfo = {
    claims: null,
    avatarSource: DEFAULT_AVATAR_SOURCE,
};

export default function TopNavBar(
    { contactEmail, logoWidth, logoHeight, userInfo: initUserInfo }: Props
) {
    let runtime = inferRuntimeEnvironment();

    switch (runtime) {
        case "web-worker": throw new Error("TopNavBar cannot be rendered in a web-worker environment");
        case "frontend-server": {
            if (initUserInfo?.claims === undefined) {
                throw new Error("When rendering TopNavBar on the frontend-server, userInfo.claims must be provided");
            }
            if (initUserInfo?.avatarSource === undefined) {
                throw new Error("When rendering TopNavBar on the frontend-server, userInfo.avatarSource must be provided");
            }
            break;
        }
        case "browser": break;
    };

    initUserInfo = initUserInfo ?? DEFAULT_USER_INFO;
    initUserInfo.avatarSource = initUserInfo.avatarSource ?? DEFAULT_AVATAR_SOURCE;

    logoWidth = logoWidth ?? 120;
    logoHeight = logoHeight ?? 30;
    contactEmail = contactEmail ?? CONTACT_EMAIL;

    const [userInfo, setUserInfo] = useState(initUserInfo as UserInfo);

    return (
        <>
            { /* Navigation Bar */}
            < nav className="w-full flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-800 bg-white/80 dark:bg-black/80 backdrop-blur-sm" >
                {/* Logo */}
                < div className="flex items-center gap-2" >
                    <Image
                        className="dark:invert"
                        src="/main-line.svg"
                        alt="Main line chess logo"
                        width={logoWidth}
                        height={logoHeight}
                        priority
                    />
                </div >

                {/* Right side (optional links or buttons) */}
                <div className="flex items-center gap-6 text-sm font-medium" >
                    <Link href="/" className="hover:underline hover:underline-offset-4">Main Page</Link>
                    { /*
                <a
                    href="/about"
                    className="hover:underline hover:underline-offset-4"
                >
                    About
                </a>
                */ }
                    {userInfo.claims && <Link href={`/user/${userInfo.claims.sub}`} className="hover:underline hover:underline-offset-4">Profile</Link>}
                    <Link href="/same-device" className="hover:underline hover:underline-offset-4">Play</Link>
                    <a
                        href={`mailto:${contactEmail}`}
                        className="hover:underline hover:underline-offset-4"
                    >
                        Contact
                    </a>
                    {
                        userInfo.claims === undefined ?
                            <a
                                className="flex items-center gap-2 hover:underline hover:underline-offset-4"
                                href="/login"
                            >
                                Log In
                                <Image
                                    aria-hidden
                                    src={userInfo.avatarSource ?? DEFAULT_AVATAR_SOURCE}
                                    alt="Account icon"
                                    width={32}
                                    height={32}
                                />
                            </a>
                            :
                            <LogoutButton
                                onLogout={() => setUserInfo(DEFAULT_USER_INFO)}
                            >
                                Logout
                                <Image
                                    aria-hidden
                                    src={userInfo.avatarSource ?? DEFAULT_AVATAR_SOURCE}
                                    alt="Account icon"
                                    width={32}
                                    height={32}
                                />
                            </LogoutButton>
                    }
                </div >
            </nav >
        </>
    )
}