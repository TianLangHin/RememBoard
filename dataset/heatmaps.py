from itertools import product
import chess, chess.pgn
import matplotlib.pyplot as plt
import numpy as np
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

def increment(data: Breakdown, board: chess.Game):
    for square in range(64):
        if (piece := board.piece_at(square)) is not None:
            piece_type = piece.piece_type
            colour = piece.color
            sq_rank, sq_file = divmod(square, 8)
            sq_rank = 7 - sq_rank
            data[piece_type, colour][sq_rank, sq_file] += 1

def heatmap(filename: str) -> Breakdown:
    with open(filename, 'rt') as f:
        games = []
        while (game_pgn := chess.pgn.read_game(f)):
            games.append(game_pgn)
    heatmap_data = {
        (piece, colour): np.array([[0] * 8] * 8)
        for piece, colour in product(PIECES, COLOURS)
    }
    for game in games:
        board = game.board()
        for move in game.mainline_moves():
            board.push(move)
            increment(heatmap_data, board)
    return heatmap_data

def main():
    pgn_filename = sys.argv[1]

    hmp_data = heatmap('championships-1866-2021/pgn/pgn/' + pgn_filename)
    piece_names = ['Pawn', 'Knight', 'Bishop', 'Rook', 'Queen', 'King']
    colour_names = ['White', 'Black']
    game_name = pgn_filename.strip('.pgn')
    cmap = 'hot'

    fig, axes = plt.subplots(2, 6, figsize=(20,10))
    fig.suptitle(f'Heatmap for {game_name}')
    for i, (colour, piece) in enumerate(product(COLOURS, PIECES)):
        ax = axes[*divmod(i, 6)]
        ax.set_title(f'{colour_names[i // 6]} {piece_names[i % 6]}')
        ax.set_box_aspect(1)
        hmp = sns.heatmap(hmp_data[piece, colour], ax=ax, cmap=cmap)
        hmp.set_xticklabels(list('abcdefgh'))
        hmp.set_yticklabels(list('87654321'), rotation=0)
    plt.savefig(f'explore-{game_name}-heatmaps.png')
    combined_hmp = sum(hmp_data.values())

    plt.figure()
    hmp = sns.heatmap(combined_hmp, cmap=cmap)
    hmp.set_xticklabels(list('abcdefgh'))
    hmp.set_yticklabels(list('87654321'), rotation=0)
    plt.title(f'Combined Heatmap for {pgn_filename.strip('.pgn')}')
    plt.savefig(f'explore-{game_name}-combined-heatmap.png')

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
    bpt.bar_label(bpt.containers[0])
    plt.xticks(rotation=70)
    plt.savefig(f'explore-{game_name}-bar-plot.png')

if __name__ == '__main__':
    main()
