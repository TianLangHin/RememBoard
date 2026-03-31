from collections import namedtuple
from enum import Enum
from itertools import product
from typing import List, Optional, Tuple
from ultralytics.engine.results import Results
import chess
import cv2
import numpy as np

Box = namedtuple('Box', ['x', 'y', 'w', 'h'])
Corners = namedtuple('Corners', ['tl', 'tr', 'bl', 'br'])
TopLeftSquare = Enum('TopLeftSquare', ['A1', 'A8', 'H1', 'H8'])

def original_corners_as_ndarray(corners: Corners) -> np.ndarray:
    return np.float32([
        [corners.tl[0], corners.tl[1]],
        [corners.tr[0], corners.tr[1]],
        [corners.br[0], corners.br[1]],
        [corners.bl[0], corners.bl[1]],
    ])

def target_corners_as_ndarray(*, width: int, pad: int) -> np.ndarray:
    return np.float32([
        [0 + pad, 0 + pad],         # top-left
        [width - pad, 0 + pad],     # top-right
        [width - pad, width - pad], # bottom-right
        [0 + pad, width - pad],     # bottom-left
    ])

def corners_from_point_list(centres: List[Tuple[float, float]]) -> Corners:
    assert len(centres) >= 4
    # The first item is x (increasing to the right), the second item is y (increasing downwards).
    from_top_left = lambda point: point[0] + point[1]
    from_bottom_left = lambda point: point[0] - point[1]
    # This only considers the maximal four corners of the possible chessboard square,
    # thus always returning 4 corners.
    return Corners(
        tl=min(centres, key=from_top_left),
        tr=max(centres, key=from_bottom_left),
        bl=min(centres, key=from_bottom_left),
        br=max(centres, key=from_top_left))

def average_bounding_square(corners: List[Tuple[float, float]]) -> Corners:
    tl, tr, bl, br = [(int(corner[0]), int(corner[1])) for corner in corners_from_point_list(corners)]
    left = (tl[0] + bl[0]) // 2
    right = (tr[0] + br[0]) // 2
    top = (tl[1] + tr[1]) // 2
    bottom = (bl[1] + br[1]) // 2
    return Corners(tl=(left, top), tr=(right, top), bl=(left, bottom), br=(right, bottom))

def apply_transform(*, point: Tuple[float, float], matrix: np.ndarray) -> Tuple[int, int]:
    x, y = point
    d = matrix[2, 0] * x + matrix[2, 1] * y + matrix[2, 2]
    new_x = (matrix[0, 0] * x + matrix[0, 1] * y + matrix[0, 2]) / d
    new_y = (matrix[1, 0] * x + matrix[1, 1] * y + matrix[1, 2]) / d
    return (int(new_x), int(new_y))

def intersection_area(corners: Tuple[Tuple[float, float], Tuple[float, float]], box: Box) -> float:
    # print(corners, box)
    b_top_left = (box.x - 0.5 * box.w, box.y - 0.5 * box.h)
    b_bottom_right = (box.x + 0.5 * box.w, box.y + 0.5 * box.h)
    c_top_left, c_bottom_right = corners
    x_overlap = max(0, min(b_bottom_right[0], c_bottom_right[0]) - max(b_top_left[0], c_top_left[0]))
    y_overlap = max(0, min(b_bottom_right[1], c_bottom_right[1]) - max(b_top_left[1], c_top_left[1]))
    return x_overlap * y_overlap

# Takes in the results of a YOLO model inference run on a single image.
# Takes an optional parameter `warped`, which will first perspective transform
# the model inference first before mapping to the squares.
def yolo_inference_to_piece_list(result: Results, *, warped: bool = True, orientation: TopLeftSquare) -> Optional[List[Optional[chess.Piece]]]:
    corner_centres: List[Tuple[float, float]] = []
    piece_boxes: List[Tuple[str, float, Box]] = []

    for box in result.boxes:
        class_name = result.names[box.cls.item()]
        x, y, w, h = box.xywh[0]
        conf = box.conf.item()
        if class_name == 'corner':
            corner_centres.append((x.item(), y.item()))
        else:
            piece_boxes.append((class_name, conf, Box(x=x.item(), y=y.item(), w=w.item(), h=h.item())))

    if len(corner_centres) < 4:
        return None

    # After this step, corners are arranged in the order of: [top_left, top_right, bottom_left, bottom_right]
    if warped:
        # This process maps the corners to a square of 640px by 640px.
        # This square is not actually generated explicitly as an image,
        # but the coordinates are warped to correspond to one conceptually.
        # This potentially makes it more robust when mapping bounding boxes to chessboard locations.
        img_width = 640
        img_padding = 50
        corners = corners_from_point_list(corner_centres)
        src = original_corners_as_ndarray(corners)
        dest = target_corners_as_ndarray(width=img_width, pad=img_padding)
        transform = cv2.getPerspectiveTransform(src, dest)
        # This replaces the coordinates of `piece_boxes` to contain the perspective transformed coordinates.
        for i in range(len(piece_boxes)):
            piece_type, conf, (x, y, w, h) = piece_boxes[i]
            top_left = (x - 0.5 * w, y - 0.5 * h)
            bottom_right = (x + 0.5 * w, y + 0.5 * h)
            top_left = apply_transform(point=top_left, matrix=transform)
            bottom_right = apply_transform(point=bottom_right, matrix=transform)
            x = (top_left[0] + bottom_right[0]) // 2
            y = (top_left[1] + bottom_right[1]) // 2
            w = bottom_right[0] - top_left[0]
            h = bottom_right[1] - top_left[1]
            piece_boxes[i] = (piece_type, conf, Box(x=x, y=y, w=w, h=h))
        corner_centres = Corners(*[apply_transform(point=corner, matrix=transform) for corner in corners])
        # At the end of this process, `corner_centres` contains the warped corners
        # and `piece_boxes` contains the warped bounding boxes of each detected piece.
        # The type of `corner_centres` is still `Corners`.
    else:
        corner_centres = average_bounding_square(corner_centres)

    # Next, we split up the square demarcated by the corners into 64 squares.
    # `box_width` and `box_height` are the side lengths of these squares.
    box_width = (corner_centres.tr[0] - corner_centres.tl[0]) / 8
    box_height = (corner_centres.bl[1] - corner_centres.tl[1]) / 8
    # This lambda generates the corner `x` such units rightwards and `y` units downwards from the top left.
    point_from_tl = lambda *, x, y: (corner_centres.tl[0] + box_width * x, corner_centres.tl[1] + box_height * y)
    # The top-left and bottom-right corners of each square indexed from 0 to 63 (rightwards then down)
    # is thus found using the above.
    square_corners = [
        (point_from_tl(x=square % 8, y=square // 8), point_from_tl(x=square % 8 + 1, y=square // 8 + 1))
        for square in range(64)
    ]

    # Next, for every piece, we find the square its bounding box overlaps with the most, and place it there.
    # If there is an overlap (more than one piece being mapped to the same square), we choose the one with the highest confidence.
    assigned_pieces = [None] * 64
    for i in range(len(piece_boxes)):
        piece_type, conf, piece_box = piece_boxes[i]
        closest_square = max(range(64), key=lambda square: intersection_area(square_corners[square], piece_box))
        # We only consider pieces that overlap with the board itself
        # since there may be other pieces in the picture but off the board.
        # This is the case when even the closest square has zero intersection with its bounding box.
        if intersection_area(square_corners[closest_square], piece_box) == 0:
            continue
        if assigned_pieces[closest_square] is None:
            assigned_pieces[closest_square] = (piece_type, conf)
        else:
            _, prev_conf = assigned_pieces[closest_square]
            if conf > prev_conf:
                assigned_pieces[closest_square] = (piece_type, conf)

    # Finally, we convert the above indices to the correct chess square, depending on which square is in the top left corner.
    match orientation:
        case TopLeftSquare.A1:
            chess_squares = (f'{f}{r}' for f, r in product(chess.FILE_NAMES, chess.RANK_NAMES))
        case TopLeftSquare.A8:
            chess_squares = (f'{f}{r}' for r, f in product(chess.RANK_NAMES[::-1], chess.FILE_NAMES))
        case TopLeftSquare.H1:
            chess_squares = (f'{f}{r}' for r, f in product(chess.RANK_NAMES, chess.FILE_NAMES[::-1]))
        case TopLeftSquare.H8:
            chess_squares = (f'{f}{r}' for f, r in product(chess.FILE_NAMES[::-1], chess.RANK_NAMES[::-1]))

    piece_name_map = {
        'white pawn':   chess.Piece(chess.PAWN,   chess.WHITE),
        'white knight': chess.Piece(chess.KNIGHT, chess.WHITE),
        'white bishop': chess.Piece(chess.BISHOP, chess.WHITE),
        'white rook':   chess.Piece(chess.ROOK,   chess.WHITE),
        'white queen':  chess.Piece(chess.QUEEN,  chess.WHITE),
        'white king':   chess.Piece(chess.KING,   chess.WHITE),
        'black pawn':   chess.Piece(chess.PAWN,   chess.BLACK),
        'black knight': chess.Piece(chess.KNIGHT, chess.BLACK),
        'black bishop': chess.Piece(chess.BISHOP, chess.BLACK),
        'black rook':   chess.Piece(chess.ROOK,   chess.BLACK),
        'black queen':  chess.Piece(chess.QUEEN,  chess.BLACK),
        'black king':   chess.Piece(chess.KING,   chess.BLACK),
    }

    # We use the above conversions to finally place the pieces in the correct indices.
    corrected_piece_locations = [None] * 64
    for index, square in enumerate(chess_squares):
        if assigned_pieces[index] is not None:
            new_index = chess.parse_square(square)
            corrected_piece_locations[new_index] = piece_name_map[assigned_pieces[index][0]]

    return corrected_piece_locations

if __name__ == '__main__':
    from ultralytics import YOLO
    import os

    model = YOLO('server/model/yolo11s-v0-0-1.pt')
    images = os.listdir(os.path.join(os.getcwd(), '..', 'ChessDataset', 'wc2021'))
    game = 'g01'
    for image in images:
        if game in image:
            frame = cv2.imread(os.path.join(os.getcwd(), '..', 'ChessDataset', 'wc2021', image))
            results = model.predict(frame, imgsz=640, conf=0.25, verbose=False)[0]
            top_left = TopLeftSquare.H8
            piece_list = yolo_inference_to_piece_list(results, warped=False, orientation=top_left)
            if piece_list is not None:
                board = chess.Board.empty()
                for i in range(len(piece_list)):
                    board.set_piece_at(i, piece_list[i])
                print(board)
            else:
                print('Corner detection was incorrect.')
            input('Next: ')
