import chess

from conversion import TopLeftSquare
from inference import PredictionStatus

class LiveGameState:
    def __init__(self, *, p1: str, p2: str, orientation: TopLeftSquare = TopLeftSquare.H8):
        self.p1 = p1
        self.p2 = p2
        self.paused = False
        self.concluded = None
        self.board = chess.Board()
        self.orientation = orientation
        self.prediction_status = PredictionStatus.ValidMove
        self.diagnostics = ''
    def pause(self):
        self.paused = True
    def unpause(self):
        self.paused = False
    def push_move(self, move: chess.Move):
        # If the game has already concluded, then pushing the move is unsuccessful.
        if self.concluded is not None or self.board.result() != '*':
            return
        # If this move is illegal, it is also unsuccessful.
        if move not in self.board.legal_moves:
            return
        # Push the move.
        self.board.push(move)
        # Update whether this move concludes the game.
        if self.board.result() != '*':
            self.concluded = self.board.result()
    def undo_move(self):
        self.concluded = False
        # If the list is empty, that does not matter.
        try:
            self.board.pop()
        except IndexError:
            pass
    def rename_player1(self, new_name: str):
        self.p1 = new_name
    def rename_player2(self, new_name: str):
        self.p2 = new_name
    def move_list(self) -> list[str]:
        mock_board = chess.Board()
        moves = []
        for move in self.board.move_stack:
            moves.append(mock_board.san(move))
            mock_board.push(move)
        return moves
    def serialise(self) -> str:
        p = ['0', '1'][self.paused]
        c = self.concluded if self.concluded is not None else '*'
        f = self.board.fen()
        m = '|'.join(self.move_list())
        o = self.orientation.name.lower()
        return f'p1<{self.p1}>p2<{self.p2}>paused<{p}>concluded<{c}>fen<{f}>moves<{m}>orientation<{o}>'
