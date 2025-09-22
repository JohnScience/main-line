import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";

import "@/app/globals.css";
import { COMPANY_NAME, COMPANY_MOTTO } from "@/app/config";

const geistSans = Geist({
    variable: "--font-geist-sans",
    subsets: ["latin"],
});

const geistMono = Geist_Mono({
    variable: "--font-geist-mono",
    subsets: ["latin"],
});


// TODO: generate metadata <https://nextjs.org/docs/app/getting-started/metadata-and-og-images#generated-metadata>
export const metadata: Metadata = {
    title: `${COMPANY_NAME}: User Profile`,
    description: COMPANY_MOTTO,
};

export default function UserProfileLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="en">
            <body
                className={`${geistSans.variable} ${geistMono.variable} antialiased`}
            >
                {children}
            </body>
        </html>
    );
}
