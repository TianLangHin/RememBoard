from enum import Enum
from typing import List, Optional
import chess

from analysis import board_to_piece_list
from conversion import TopLeftSquare, yolo_inference_to_piece_list

type PieceList = List[Optional[chess.Piece]]

LiveGameState = Enum('LiveGameState', ['ValidMove', 'InvalidMove', 'AmbiguousMove', 'Obstructed', 'Paused', 'Concluded'])

def check_pieces_match(*, target: PieceList, prediction: PieceList, match_exact: bool) -> bool:
    target_set = {square for square in range(64) if target[square] is not None}
    prediction_set = {square for square in range(64) if prediction[square] is not None}
    if match_exact:
        return target_set == prediction_set
    else:
        return prediction_set.issubset(target_set)

def get_possible_moves(*, known_board: chess.Board, piece_list: PieceList, match_exact: bool) -> List[chess.Move]:
    true_pieces = board_to_piece_list(known_board)
    possible_moves = []
    # First, we see if the piece patterns match against the existing board (i.e., no move made).
    if check_pieces_match(target=true_pieces, prediction=piece_list, match_exact=match_exact):
        possible_moves.append(chess.Move.null())
    # Next, we look for every possible legal move.
    for move in known_board.legal_moves:
        board.push(move)
        # We check to see if the piece patterns match for each possible next legal position.
        moved_pieces = board_to_piece_list(board)
        if check_pieces_match(target=moved_pieces, prediction=piece_list, match_exact=match_exact):
            possible_moves.append(move)
        board.pop()
    return possible_moves
