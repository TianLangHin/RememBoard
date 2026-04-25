from collections import namedtuple
import chess
import datetime
import sqlite3

StoredGame = namedtuple('StoredGame', ['date', 'white', 'black', 'result', 'moves'])

class GameStorage:
    def __init__(self):
        self.connection = sqlite3.connect('game_records.db')
        self.cursor = self.connection.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Games (
                GameID INTEGER PRIMARY KEY,
                Date TEXT,
                White TEXT,
                Black TEXT,
                Result TEXT,
                Moves TEXT
            );
        ''')
    def find_game(self, game_id: int):
        for row in self.cursor.execute('SELECT * FROM Games WHERE GameID = ?;', (game_id,)):
            return row
        return None
    def search_games(self, *, date: str = '%', white: str = '%', black: str = '%', result: str = '%'):
        result = self.cursor.execute(
            'SELECT * FROM Games WHERE Date LIKE ? AND White LIKE ? AND Black LIKE ? AND Result LIKE ?;',
            (date, white, black, result))
        entries = []
        for row in result:
            entries.append(row)
        return entries
    def delete_game(self, game_id: int):
        self.cursor.execute('DELETE FROM Games WHERE GameID = ?;', (game_id,))
        self.connection.commit()
    def insert_game(self, *, white: str, black: str, board: chess.Board):
        date = datetime.date.today().isoformat()
        moves = ' '.join(move.uci() for move in board.move_stack)
        result = board.result()
        self.cursor.execute(
            'INSERT INTO Games (Date, White, Black, Result, Moves) VALUES (?, ?, ?, ?, ?);',
            (date, white, black, result, moves))
        self.connection.commit()
    def finalise(self):
        self.connection.close()
