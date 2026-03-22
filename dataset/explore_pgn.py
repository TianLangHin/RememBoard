from itertools import product
import chess
from chess.pgn import Game
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy as np
import os
import pandas as pd
import seaborn as sns
import sys

type Breakdown = dict[tuple[chess.Piece, chess.Color], np.ndarray]

PIECES = [
    chess.PAWN,
    chess.KNIGHT,
    chess.BISHOP,
    chess.ROOK,
    chess.QUEEN,
    chess.KING,
]

COLOURS = [
    chess.WHITE,
    chess.BLACK,
]

def increment(data: Breakdown, board: chess.Board):
    for square in range(64):
        if (piece := board.piece_at(square)) is not None:
            piece_type = piece.piece_type
            colour = piece.color
            sq_rank, sq_file = divmod(square, 8)
            sq_rank = 7 - sq_rank
            data[piece_type, colour][sq_rank, sq_file] += 1

def heatmap(games: list[Game]) -> Breakdown:
    heatmap_data = {
        (piece, colour): np.array([[0] * 8] * 8)
        for piece, colour in product(PIECES, COLOURS)
    }
    for game in games:
        if len(game.errors) > 0:
            print(game.errors)
        board = game.board()
        for move in game.mainline_moves():
            board.push(move)
            increment(heatmap_data, board)
    return heatmap_data

def game_lengths(games: list[Game]) -> list[int]:
    return [
        len(list(game.mainline_moves()))
        for game in games
    ]

def load_games(filename: str) -> list[Game]:
    games = []
    with open(filename, 'rt') as f:
        while (game_pgn := chess.pgn.read_game(f)):
            games.append(game_pgn)
    return games

def create_diagrams(game_name: str, game_data: list[Game]):
    piece_names = ['Pawn', 'Knight', 'Bishop', 'Rook', 'Queen', 'King']
    colour_names = ['White', 'Black']
    cmap = 'hot'
    game_str = game_name.replace(' ', '-')

    hmp_data = heatmap(game_data)

    fig, axes = plt.subplots(2, 6, figsize=(20, 5))
    fig.suptitle(f'Heatmap for {game_name}')
    fig.subplots_adjust(wspace=0.5)
    for i, (colour, piece) in enumerate(product(COLOURS, PIECES)):
        ax = axes[*divmod(i, 6)]
        ax.set_title(f'{colour_names[i // 6]} {piece_names[i % 6]}')
        ax.set_box_aspect(1)
        hmp = sns.heatmap(hmp_data[piece, colour], ax=ax, cmap=cmap, cbar=True)
        hmp.set_xticklabels(list('abcdefgh'))
        hmp.set_yticklabels(list('87654321'), rotation=0)
    plt.savefig(f'explore-{game_str}-heatmaps.png')
    fig.tight_layout()
    combined_hmp = sum(hmp_data.values())

    plt.figure()
    hmp = sns.heatmap(combined_hmp, cmap=cmap)
    hmp.set_xticklabels(list('abcdefgh'))
    hmp.set_yticklabels(list('87654321'), rotation=0)
    plt.title(f'Combined Heatmap for {game_name}')
    plt.savefig(f'explore-{game_str}-combined-heatmap.png')

    plt.figure(figsize=(12, 12))
    plt.title(f'Frequency plot of piece types for {game_name}')
    df = pd.DataFrame({
        'Piece types': [
            f'{colour_names[i // 6]} {piece_names[i % 6]}'
            for i in range(len(PIECES) * len(COLOURS))
        ],
        'Frequency': [
            hmp_data[piece, colour].sum()
            for colour, piece in product(COLOURS, PIECES)
        ],
    })
    bpt = sns.barplot(data=df, x='Piece types', y='Frequency')
    bpt.bar_label(bpt.containers[0], fmt='{:.0f}')
    plt.xticks(rotation=70)
    plt.savefig(f'explore-{game_str}-bar-plot.png')

    plt.figure()
    length_data = game_lengths(game_data)
    hsp = sns.histplot(length_data, binwidth=10)
    hsp.set_xticks(np.arange(10, 300, 20))
    hsp.yaxis.set_major_locator(MaxNLocator(integer=True))
    plt.title(f'Histogram of the number of positions per game in {game_name}')
    plt.savefig(f'explore-{game_str}-histogram.png')

def main():
    pgn_filename = sys.argv[1]
    if pgn_filename == 'aggregate':
        games = []
        for pgn in os.listdir('championships-1866-2021'):
            games.extend(load_games(os.path.join('championships-1866-2021', pgn)))
        create_diagrams('all games', games)
    else:
        games = load_games(os.path.join('championships-1866-2021', pgn_filename))
        game_name = pgn_filename.strip('.pgn')
        create_diagrams(game_name, games)

if __name__ == '__main__':
    main()
