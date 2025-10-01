"use client";

import React, { useEffect } from "react";

import { Chess } from "chess.js";
import { Chessboard as CmChessboard, COLOR } from "cm-chessboard";
import { MARKER_TYPE, Markers } from "cm-chessboard/src/extensions/markers/Markers.js";
import { PromotionDialog } from "cm-chessboard/src/extensions/promotion-dialog/PromotionDialog.js";
import { Accessibility } from "cm-chessboard/src/extensions/accessibility/Accessibility.js";
import { RightClickAnnotator } from "cm-chessboard/src/extensions/right-click-annotator/RightClickAnnotator.js";

import "cm-chessboard/assets/chessboard.css";
import "cm-chessboard/assets/extensions/markers/markers.css";
import "cm-chessboard/assets/extensions/arrows/arrows.css";
import "cm-chessboard/assets/extensions/promotion-dialog/promotion-dialog.css";

import { ExtensionsTuple } from "@/app/_chess/common";
import { inputHandler } from "@/app/_chess/same_device";

export default function Chessboard() {
    let chessboardRef = React.createRef<HTMLDivElement>();
    const chess = new Chess();

    useEffect(() => {
        const chessboard = new CmChessboard<ExtensionsTuple>(
            chessboardRef.current!,
            {
                position: chess.fen(),
                assetsUrl: "/_next/static/cm-chessboard/assets/",
                extensions: [
                    { class: Markers, props: { autoMarkers: MARKER_TYPE.square } },
                    { class: RightClickAnnotator },
                    { class: PromotionDialog },
                    { class: Accessibility, props: { visuallyHidden: true } }
                ]
            }
        );
        chessboard.enableMoveInput(inputHandler.bind(null, chess), COLOR.white);
    }, [/*chessboardRef*/]);

    return (
        <div ref={chessboardRef} className="min-h-[600px] min-w-[600px]"></div>
    );
}