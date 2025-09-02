import Image from "next/image";
import Link from "next/link";
import { CONTACT_EMAIL } from "@/app/config";

interface Props {
    contactEmail?: string;
    logoWidth?: number;
    logoHeight?: number;
}

export default function TopNavBar(
    { contactEmail, logoWidth, logoHeight }: Props
) {
    logoWidth = logoWidth ?? 120;
    logoHeight = logoHeight ?? 30;
    contactEmail = contactEmail ?? CONTACT_EMAIL;

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
                < div className="flex items-center gap-6 text-sm font-medium" >
                    <Link href="/" className="hover:underline hover:underline-offset-4">Home</Link>
                    { /*
                <a
                    href="/about"
                    className="hover:underline hover:underline-offset-4"
                >
                    About
                </a>
                */ }
                    <a
                        href={`mailto:${contactEmail}`}
                        className="hover:underline hover:underline-offset-4"
                    >
                        Contact
                    </a>
                    <a
                        className="flex items-center gap-2 hover:underline hover:underline-offset-4"
                        href="/login"
                    >
                        Log In
                        <Image
                            aria-hidden
                            src="/account.svg"
                            alt="Account icon"
                            width={32}
                            height={32}
                        />
                    </a>
                </div >
            </nav >
        </>
    )
}