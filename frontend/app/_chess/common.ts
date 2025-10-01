import { Chessboard } from "cm-chessboard";
import { Accessibility } from "cm-chessboard/src/extensions/accessibility/Accessibility.js";
import { Markers } from "cm-chessboard/src/extensions/markers/Markers.js";
import { PromotionDialog } from "cm-chessboard/src/extensions/promotion-dialog/PromotionDialog.js";
import { RightClickAnnotator } from "cm-chessboard/src/extensions/right-click-annotator/RightClickAnnotator.js";

export type ExtensionsTuple = [
    typeof Markers,
    typeof RightClickAnnotator,
    typeof PromotionDialog,
    typeof Accessibility
];

export type MainlineChessboard = Chessboard<ExtensionsTuple>;
