"use client";

import React, { useEffect } from "react";

import { Chess } from "chess.js";
import { Chessboard as CmChessboard, INPUT_EVENT_TYPE, COLOR, ChessboardEvent } from "cm-chessboard";
import { MARKER_TYPE, Markers } from "cm-chessboard/src/extensions/markers/Markers.js";
import { PROMOTION_DIALOG_RESULT_TYPE, PromotionDialog, PromotionDialogResult } from "cm-chessboard/src/extensions/promotion-dialog/PromotionDialog.js";
import { Accessibility } from "cm-chessboard/src/extensions/accessibility/Accessibility.js";
import { RightClickAnnotator } from "cm-chessboard/src/extensions/right-click-annotator/RightClickAnnotator.js";

import "cm-chessboard/assets/chessboard.css";
import "cm-chessboard/assets/extensions/markers/markers.css";
import "cm-chessboard/assets/extensions/arrows/arrows.css";
import "cm-chessboard/assets/extensions/promotion-dialog/promotion-dialog.css";

type ExtensionsTuple = [
    typeof Markers,
    typeof RightClickAnnotator,
    typeof PromotionDialog,
    typeof Accessibility
];

type MyChessboard = CmChessboard<ExtensionsTuple>;

let seed = 71;
function random() {
    const x = Math.sin(seed++) * 10000;
    return x - Math.floor(x);
}

function makeEngineMove(chess: Chess, chessboard: MyChessboard) {
    const possibleMoves = chess.moves({ verbose: true })
    if (possibleMoves.length > 0) {
        const randomIndex = Math.floor(random() * possibleMoves.length)
        const randomMove = possibleMoves[randomIndex]
        setTimeout(() => { // smoother with 500ms delay
            chess.move({ from: randomMove.from, to: randomMove.to })
            chessboard.setPosition(chess.fen(), true);
        }, 500)
    }
}

function inputHandler(chess: Chess, event: ChessboardEvent<MyChessboard>): boolean {
    // Sometimes, there's an undefined event
    if (!event) {
        return false;
    }
    console.log("inputHandler", event)
    switch (event.type) {
        case INPUT_EVENT_TYPE.movingOverSquare: return false; // ignore this event
        case INPUT_EVENT_TYPE.moveInputStarted: {
            event.chessboard.removeLegalMovesMarkers();
            // mark legal moves
            const moves = chess.moves({ square: event.squareFrom, verbose: true })
            event.chessboard.addLegalMovesMarkers(moves);
            return moves.length > 0
        };
        case INPUT_EVENT_TYPE.validateMoveInput: {
            event.chessboard.removeLegalMovesMarkers();
            console.log("Legal moves: ", chess.moves());
            const move = { from: event.squareFrom, to: event.squareTo };
            console.log("Move: ", move);
            let result;
            try {
                result = chess.move(move)
            } catch (error) {
                console.error("Error making move:", error);
                result = null;
            }
            if (result) {
                (async () => {
                    await event.chessboard.state.moveInputProcess; // wait for the move input process has finished
                    await event.chessboard.setPosition(chess.fen(), true); // update position, maybe castled and wait for animation has finished
                    makeEngineMove(chess, event.chessboard);
                })();
            } else {
                // promotion?
                let possibleMoves = chess.moves({ square: event.squareFrom, verbose: true });
                for (const possibleMove of possibleMoves) {
                    if (!possibleMove.promotion) { continue; };
                    if (possibleMove.to !== event.squareTo) { continue; };
                    event.chessboard.showPromotionDialog(event.squareTo, COLOR.white, (result: PromotionDialogResult) => {
                        switch (result.type) {
                            case PROMOTION_DIALOG_RESULT_TYPE.canceled: {
                                event.chessboard.enableMoveInput(inputHandler.bind(null, chess), COLOR.white);
                                event.chessboard.setPosition(chess.fen(), true);
                                break;
                            };
                            case PROMOTION_DIALOG_RESULT_TYPE.pieceSelected: {
                                chess.move({ from: event.squareFrom, to: event.squareTo, promotion: result.piece.charAt(1) });
                                event.chessboard.setPosition(chess.fen(), true);
                                makeEngineMove(chess, event.chessboard);
                            }
                        }
                    })
                    return true
                }
            }
            return !!result
        };
        case INPUT_EVENT_TYPE.moveInputFinished: return false;
    }
    return false; // default reject
}

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
        <div ref={chessboardRef}></div>
    );
}