from chess.pgn import Game
from conversion import TopLeftSquare, yolo_inference_to_piece_list
from typing import List, Optional
from ultralytics import YOLO
import chess
import cv2
import os
import sys

def board_to_piece_list(board: chess.Board) -> List[Optional[chess.Piece]]:
    piece_list = [None] * 64
    for square in range(64):
        piece_list[square] = board.piece_at(square)
    return piece_list

def piece_list_to_board(pieces: List[Optional[chess.Piece]]) -> chess.Board:
    board = chess.Board.empty()
    for square in range(64):
        board.set_piece_at(square, pieces[square])
    return board

# Function used for checking a prediction against the ground truth chess position.
def plot_image_and_classify(model: YOLO, game_num: int, move_num: int, image_dir: str, board: chess.Board) -> bool:
    image_name = f'wc2021g{game_num:0>2}-{move_num:0>4}.png'
    image = cv2.imread(os.path.join(image_dir, image_name))
    # YOLO inference is conducted here.
    result = model.predict(image, imgsz=640, conf=0.25, verbose=False)[0]
    predicted_piece_list = yolo_inference_to_piece_list(result, warped=True, orientation=TopLeftSquare.H8)
    # The raw prediction by YOLO is saved.
    result.plot(font_size=20, save=True, filename=os.path.join(output_dir, f'plotted-{image_name}'), pil=True)

    # We check whether a misclassification has occurred.
    true_piece_list = board_to_piece_list(board)
    if predicted_piece_list == true_piece_list:
        return False
    print(f'Misclassification in Game {game_num}, Image {move_num}.')
    # If it has, there are two possibilities: too many/too few corners found, or an incorrect position.
    if predicted_piece_list is None:
        corners = [box for box in result.boxes if result.names[box.cls.item()] == 'corner']
        print(f'{len(corners)} corners were found.')
    else:
        predicted_board = piece_list_to_board(predicted_piece_list)
        print(f'Expected FEN was "{board.fen()}", got "{predicted_board.fen()}".')
    return True

# Main function to conduct analysis of the model's performance on the WC 2021 dataset.
def model_analysis_main(image_dir: str, output_dir: str):
    model = YOLO('model/yolo11s-v0-0-1.pt')
    # Default location of the PGN, and comes with the repository.
    pgn_dataset = os.path.join(os.getcwd(), '..', 'dataset', 'championships-1866-2021', 'WorldChamp2021.pgn')
    # Gather all the games.
    games = []
    with open(pgn_dataset, 'rt') as f:
        while (game_pgn := chess.pgn.read_game(f)):
            games.append(game_pgn)
    # This records the metrics into a text file later.
    game_metrics = []
    # For every game, we start with evaluating the model's performance on the starting position image.
    # Then, we iterate through each of the moves, passing the new board to the model each time.
    for game_num, game_data in enumerate(games, 1):
        num_positions = 1
        num_misclassifications = 0
        print(f'Starting Game {game_num}.')
        # Keeps track of the true board state.
        board = chess.Board()
        misclassified = plot_image_and_classify(model, game_num, 1, image_dir, board)
        if misclassified:
            num_misclassifications += 1
        for move_num, move_data in enumerate(game_data.mainline_moves(), 2):
            # Ground truth board state is updated here.
            board.push(move_data)
            misclassified = plot_image_and_classify(model, game_num, move_num, image_dir, board)
            if misclassified:
                num_misclassifications += 1
            num_positions += 1
        game_metrics.append((num_misclassifications, num_positions))
        print(f'Finished Game {game_num}, with {num_misclassifications} misclassifications out of {num_positions}.')
    # The summary metrics are written into a text file in the same output directory here.
    with open(os.path.join(output_dir, 'game_metrics.txt'), 'wt') as f:
        for game_num, (misclassified, total) in enumerate(game_metrics, 1):
            f.write(f'Game {game_num} had {misclassified} positions misclassified out of {total}.\n')

# Main function to conduct analysis of the model's performance on an unseen dataset,
# with a customisable PGN location.
def model_analysis_unseen(image_dir: str, output_dir: str, pgn_file: str):
    model = YOLO('model/yolo11s-v0-0-1.pt')
    # Read the PGN.
    with open(pgn_file, 'rt') as f:
        game_data = chess.pgn.read_game(f)
    # Recording metrics of performance on game frames.
    num_positions = 0
    num_misclassifications = 0
    num_rough_matches = 0
    # Recording each of the kinds of errors as well.
    errors = []
    # The ground truth board state is recorded here,
    # and a null move is made just to make it more convenient
    # to implement the move progression with one for-loop.
    board = chess.Board()
    board.push(chess.Move.null())

    all_images = os.listdir(image_dir)
    all_moves = [chess.Move.null()] + list(game_data.mainline_moves())

    for move_num, (move_data, image_name) in enumerate(zip(all_moves, all_images), 1):
        # Board state is updated here.
        board.push(move_data)
        num_positions += 1
        # We read the image in lexicographical order.
        image = cv2.imread(os.path.join(image_dir, image_name))
        result = model.predict(image, imgsz=640, conf=0.25, verbose=False)[0]
        predicted_piece_list = yolo_inference_to_piece_list(result, warped=True, orientation=TopLeftSquare.A1)
        # The inference result is recorded into an image as well.
        result.plot(font_size=20, save=True, filename=os.path.join(output_dir, f'plotted-{image_name}'), pil=True)
        true_piece_list = board_to_piece_list(board)
        # If an exact match is found, then do not count errors.
        if predicted_piece_list == true_piece_list:
            continue
        num_misclassifications += 1
        print(f'Misclassification in image {move_num}.')
        if predicted_piece_list is None:
            # If the misclassification happened due to a wrong corner count, treat is separately.
            corners = [box for box in result.boxes if result.names[box.cls.item()] == 'corner']
            err = f'{len(corners)} corners were found.'
        else:
            # To prepare for realistic logical flow,
            # we check whether it matches the true position in terms of which squares have *any* piece.
            # If so, we indicate it as a "rough match".
            predicted_board = piece_list_to_board(predicted_piece_list)
            true_empty_indices = [i for i in range(64) if true_piece_list[i] is None]
            predicted_empty_indices = [i for i in range(64) if predicted_piece_list[i] is None]
            if true_empty_indices == predicted_empty_indices:
                err = f'On image {move_num}: Rough match - Expected FEN was "{board.fen()}", got "{predicted_board.fen()}".'
                num_rough_matches += 1
            else:
                err = f'On image {move_num}: Expected FEN was "{board.fen()}", got "{predicted_board.fen()}".'
        print(err)
        errors.append(err)
    # The metrics are also outputted into a text file.
    with open(os.path.join(output_dir, 'metrics.txt'), 'wt') as f:
        f.write(f'There were {num_misclassifications} positions misclassified out of {num_positions}, with {num_rough_matches} rough matches.\n')
        for err in errors:
            f.write(f'{err}\n')

if __name__ == '__main__':
    image_dir = sys.argv[1]
    output_dir = sys.argv[2]
    data_setup = sys.argv[3]
    pgn_file = None if len(sys.argv) <= 4 else sys.argv[4] # Optional argument to read the PGN.
    if data_setup == 'main':
        # Analysis against the initial dataset of WorldChamp2021.
        model_analysis_main(image_dir, output_dir)
    elif data_setup == 'unseen':
        # Analysis against the unseen dataset, which in this case is a separately collected image set
        # using Game 24 of the 1987 World Championship.
        model_analysis_unseen(image_dir, output_dir, pgn_file)
