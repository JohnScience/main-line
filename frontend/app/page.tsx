import TopNavBar from "./_components/TopNavBar";
import Footer from "./_components/Footer";

export default function Home() {
  return (
    <div className="font-sans grid grid-rows-[auto_1fr_20px] items-center justify-items-center min-h-screen">
      {/* Navigation Bar */}
      <TopNavBar />

      {/* Main Content */}
      <main className="flex flex-col gap-[32px] row-start-2 items-center sm:items-start p-8 sm:p-20">
        <h1 className="font-bold text-4xl text-center sm:text-left">
          How it works
        </h1>
        <ol className="font-mono list-inside list-decimal text-sm/6 text-center sm:text-left">
          <li className="mb-2 tracking-[-.01em]">
            Create an account <strong>(optionally)</strong>.
          </li>
          <li className="tracking-[-.01em]">
            Analyze your games <strong>for free</strong>.
          </li>
          <li className="mt-2 tracking-[-.01em]">
            Get better at chess <strong>fast</strong>.
          </li>
        </ol>
      </main>

      {/* Footer */}
      <Footer />
    </div>
  );
}
