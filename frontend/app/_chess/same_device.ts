import { Chess, Color } from "chess.js";
import { ChessboardEvent, COLOR, INPUT_EVENT_TYPE } from "cm-chessboard";

import { MainlineChessboard } from "./common";
import { PROMOTION_DIALOG_RESULT_TYPE, PromotionDialogResult } from "cm-chessboard/src/extensions/promotion-dialog/PromotionDialog.js";

function passTurn(chessboard: MainlineChessboard, lastMoved: Color, chess: Chess) {
    let turn: Color;
    switch (chess.turn()) {
        case "w": turn = COLOR.white; break;
        case "b": turn = COLOR.black; break;
    }
    if (turn !== lastMoved) {
        chessboard.disableMoveInput();
        chessboard.enableMoveInput(inputHandler.bind(null, chess), turn);
        chessboard.setOrientation(turn, true);
    }
}

export function inputHandler(chess: Chess, event: ChessboardEvent<MainlineChessboard>): boolean {
    if (!event) return false;

    console.log("inputHandler", event);

    switch (event.type) {
        case INPUT_EVENT_TYPE.movingOverSquare:
            return false; // ignore hovering

        case INPUT_EVENT_TYPE.moveInputStarted: {
            event.chessboard.removeLegalMovesMarkers();
            const moves = chess.moves({ square: event.squareFrom, verbose: true });
            event.chessboard.addLegalMovesMarkers(moves);
            return moves.length > 0;
        }

        case INPUT_EVENT_TYPE.validateMoveInput: {
            let turn: Color;
            switch (chess.turn()) {
                case "w": turn = COLOR.white; break;
                case "b": turn = COLOR.black; break;
            }
            event.chessboard.removeLegalMovesMarkers();

            const move = { from: event.squareFrom, to: event.squareTo };
            console.log("Attempted move:", move);

            let result;
            try {
                result = chess.move(move);
            } catch (error) {
                console.error("Error making move:", error);
                result = null;
            }

            if (result) {
                // Normal successful move
                (async () => {
                    await event.chessboard.state.moveInputProcess;
                    await event.chessboard.setPosition(chess.fen(), true);
                    passTurn(event.chessboard, turn, chess);
                })();
            } else {
                // Handle promotion dialog if needed
                let possibleMoves = chess.moves({ square: event.squareFrom, verbose: true });
                for (const possibleMove of possibleMoves) {
                    if (!possibleMove.promotion) continue;
                    if (possibleMove.to !== event.squareTo) continue;

                    event.chessboard.showPromotionDialog(
                        event.squareTo,
                        chess.turn() === "w" ? COLOR.white : COLOR.black,
                        (result: PromotionDialogResult) => {
                            switch (result.type) {
                                case PROMOTION_DIALOG_RESULT_TYPE.canceled: {
                                    event.chessboard.enableMoveInput(inputHandler.bind(null, chess));
                                    event.chessboard.setPosition(chess.fen(), true);
                                    break;
                                }
                                case PROMOTION_DIALOG_RESULT_TYPE.pieceSelected: {
                                    chess.move({
                                        from: event.squareFrom,
                                        to: event.squareTo,
                                        promotion: result.piece.charAt(1),
                                    });
                                    event.chessboard.setPosition(chess.fen(), true);
                                    passTurn(event.chessboard, turn, chess);
                                    break;
                                }
                            }
                        }
                    );
                    return true;
                }
            }

            return !!result;
        }
        case INPUT_EVENT_TYPE.moveInputCanceled: {
            event.chessboard.removeLegalMovesMarkers();
            return false;

        }
        case INPUT_EVENT_TYPE.moveInputFinished:
            console.log(chess.turn());
            return false;
    }

    return false; // default reject
}
