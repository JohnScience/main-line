import { Chess } from "chess.js";

import { Chessboard, ChessboardEvent, COLOR, INPUT_EVENT_TYPE } from "cm-chessboard";

import { MainlineChessboard } from "./common";
import { PROMOTION_DIALOG_RESULT_TYPE, PromotionDialogResult } from "cm-chessboard/src/extensions/promotion-dialog/PromotionDialog.js";

let seed = 71;
function random() {
    const x = Math.sin(seed++) * 10000;
    return x - Math.floor(x);
}

function makeEngineMove(chess: Chess, chessboard: MainlineChessboard) {
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

export function inputHandler(chess: Chess, event: ChessboardEvent<MainlineChessboard>): boolean {
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
