"use client";

import { Move } from "chess.js";
import { useRef } from "react";

type Game = Array<AnalyzedMove>;

type MoveEvaluation = {
    kind: "best_move"
} | {
    kind: "subpar_move",
    // In centipawns
    delta: number
}

type AnalyzedMove = {
    move: Move;
    evaluation: MoveEvaluation | null;
}

export default function AnalysisMenu() {
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) {
            console.log(`Upload handler triggered. File size: ${file.size}`);
        }
    };

    const handleUploadClick = () => {
        fileInputRef.current?.click();
    };

    return (
        <div className="min-h-[600px] min-w-[300px] border border-gray-300 rounded-lg p-4">
            <h1 className="text-center mb-4">Game Analysis Settings</h1>

            <div className="flex flex-col gap-2">
                <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pgn"
                    onChange={handleFileUpload}
                    className="hidden"
                />
                <button
                    onClick={handleUploadClick}
                    className="border-2 border-blue-500 bg-blue-50 hover:bg-blue-100 rounded p-3 text-left"
                >
                    Upload .pgn
                </button>
                <button className="border-2 border-gray-300 bg-gray-100 text-gray-400 rounded p-3 text-left cursor-not-allowed" disabled>
                    Input manually
                </button>
            </div>
        </div>
    );
}
