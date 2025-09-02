// import Image from "next/image";
import TopNavBar from "@/app/_components/TopNavBar";
import Footer from "../_components/Footer";
import LoginForm from "./LoginForm";
import { toast, Toaster } from "sonner";

export default function Login() {
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
