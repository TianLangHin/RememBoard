import chess

from conversion import TopLeftSquare

class LiveGameState:
    def __init__(self, *, p1: str, p2: str, orientation: TopLeftSquare = TopLeftSquare.H8):
        self.p1 = p1
        self.p2 = p2
        self.paused = False
        self.concluded = False
        self.board = chess.Board()
        self.orientation = orientation
    def pause(self):
        self.paused = True
    def unpause(self):
        self.paused = False
    def push_move(self, move: chess.Move):
        # If the game has already concluded, then pushing the move is unsuccessful.
        if self.concluded or self.board.result() != '*':
            self.concluded = True
            return
        # If this move is illegal, it is also unsuccessful.
        if move not in self.board.legal_moves:
            return
        # Push the move.
        self.board.push(move)
        # Update whether this move concludes the game.
        if self.board.result() != '*':
            self.concluded = True
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
    def serialise(self) -> str:
        p = ['0', '1'][self.paused]
        c = ['0', '1'][self.concluded]
        f = self.board.fen()
        o = self.orientation.name
        return f'p1[{self.p1}]p2[{self.p2}]paused[{p}]concluded[{c}]fen[{f}]orientation[{o}]'
