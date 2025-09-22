import { jwtDecode } from "jwt-decode";

import { cookies } from "next/headers";

import { JwtClaims, UserId } from "api-client/build/gen_shared_types";

import TopNavBar from "@/app/_components/TopNavBar";
import Footer from "../_components/Footer";
import LoginForm from "./LoginForm";
import { redirect } from "next/navigation";

export default async function Login() {
    const cookieStore = await cookies();
    const accessToken = cookieStore.get("access_token");

    if (accessToken) {
        const jwt = jwtDecode<JwtClaims>(accessToken.value);
        const userId: UserId = jwt.sub;
        redirect(`/user/${userId}`);
    }

    return (
        <>
            <div className="font-sans grid grid-rows-[auto_1fr_20px] items-center justify-items-center min-h-screen">
                {/* Navigation Bar */}
                <TopNavBar />

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
