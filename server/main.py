from typing import List, Optional, Tuple
import asyncio
import base64
import chess
import cv2
import numpy as np
import sqlite3
import websockets

from conversion import TopLeftSquare, yolo_inference_to_piece_list
from inference import PredictionStatus, get_predicted_transition
from parse import parse_add_game, parse_remove_game, \
    parse_push_move, parse_undo_move, parse_rename_players, \
    parse_pause_game, parse_unpause_game, parse_reorient_game
from state import LiveGameState
from video import BufferlessVideo

from ultralytics import YOLO

class ServerState:
    def __init__(self):
        self.connected_clients = set()
        self.connected_controller = None
        self.games: List[Tuple[LiveGameState, BufferlessVideo]] = []
    def add_client(self, ws_connection):
        self.connected_clients.add(ws_connection)
    def remove_client(self, ws_connection):
        if ws_connection in self.connected_clients:
            self.connected_clients.remove(ws_connection)
    # Returns True if successful.
    def add_controller(self, ws_connection) -> bool:
        if self.connected_controller is None:
            self.connected_controller = ws_connection
            return True
        return False
    def remove_controller(self, ws_connection):
        if self.connected_controller == ws_connection:
            self.connected_controller = None
    def add_new_game(self, game_state: LiveGameState, stream: BufferlessVideo):
        self.games.append((game_state, stream))
    def remove_game(self, index: int):
        if 0 <= index < len(self.games):
            del self.games[index]

MODEL = YOLO('model/yolo11s-v0-0-1.pt')
PORT_NUMBER = 19941
SERVER_STATE = ServerState()
lock = asyncio.Lock()

def read_and_resize_frame(cap: BufferlessVideo) -> Optional[np.ndarray]:
    if cap.is_opened():
        ret, frame = cap.read()
        if ret:
            return cv2.resize(frame, (640, 360))
    return None

def create_transmission_payload(
        img: str,
        status: PredictionStatus,
        diagnostics: str,
        game_state: LiveGameState) -> str:
    status_map = {
        PredictionStatus.ValidMove:     'valid',
        PredictionStatus.InvalidMove:   'invalid',
        PredictionStatus.AmbiguousMove: 'ambiguous',
        PredictionStatus.Obstructed:    'obstructed',
    }
    s = status_map[status]
    return f'status<{s}<{diagnostics}>>game<{game_state.serialise()}>img<{img}>'

async def handle_message(message: str, ws_connection):
    async with lock:
        global SERVER_STATE
        if ws_connection == SERVER_STATE.connected_controller:
            parts = message.split()
            if message == 'inference':
                # This will contain a list of strings referring to each game in SERVER_STATE.
                payload_list = []

                # Computer vision inference is triggered by the controller
                # sending the "inference" message to the server.
                for game_state, video_stream in SERVER_STATE.games:
                    # The payload contains three components:
                    # an image (base64), prediction status (with associated chess moves), and game status.

                    frame = read_and_resize_frame(video_stream)
                    if not game_state.paused:
                        # First, model inference happens if the game is not paused.
                        result = MODEL.predict(frame, imgsz=640, conf=0.25, verbose=False)[0]
                        piece_list = yolo_inference_to_piece_list(result, warped=True, orientation=game_state.orientation)

                        # Payload item #1.
                        game_image = cv2.imencode('.png', result.plot(font_size=20))[1]

                        # The only case where `yolo_inference_to_piece_list` returns None
                        # is when not enough corners are found, which means the frame is obstructed.
                        if piece_list is None:
                            # Payload item #2.
                            prediction_status = PredictionStatus.Obstructed
                        else:
                            # Payload item #2.
                            prediction_status, possible_moves = get_predicted_transition(
                                known_board=game_state.board,
                                piece_list=piece_list,
                                match_exact=True)
                            if prediction_status == PredictionStatus.ValidMove and possible_moves[0] != chess.Move.null():
                                # This will not go out of index error since one move is always returned with 'ValidMove'.
                                game_state.push_move(possible_moves[0])
                                print('Valid move found:', possible_moves[0])
                                print('New game state:', game_state.board.fen())
                            elif prediction_status == PredictionStatus.InvalidMove:
                                # This gives time to the arbiter to make manual edits.
                                game_state.pause()
                                print('Invalid move detected. Game paused.')
                    else:
                        # Payload item #1.
                        game_image = cv2.imencode('.png', frame)[1]
                        # Payload item #2.
                        prediction_status = PredictionStatus.ValidMove

                    # Assemble payload.
                    encoded_image = base64.b64encode(game_image.tobytes()).decode('utf-8')
                    payload = create_transmission_payload(encoded_image, prediction_status, '', game_state)
                    payload_list.append(payload)

                # The same payload is distributed to all connections (client and controller).
                for client in SERVER_STATE.connected_clients:
                    await client.send(','.join(payload_list))
                if SERVER_STATE.connected_controller is not None:
                    await SERVER_STATE.connected_controller.send(','.join(payload_list))

            elif (add_game_command := parse_add_game(parts)) is not None:
                game_state, stream_uri = add_game_command
                video = BufferlessVideo(stream_uri)
                SERVER_STATE.add_new_game(game_state, video)
                print(f'Added game: {stream_uri}')
                print(f'Player 1: {game_state.p1}, Player 2: {game_state.p2}, Orientation: {game_state.orientation}')

            elif (remove_game_command := parse_remove_game(parts)) is not None:
                remove_index = remove_game_command
                SERVER_STATE.remove_game(remove_index)
                print(f'Removed game at index: {remove_index}')

            elif (push_move_command := parse_push_move(parts)) is not None:
                game_index, move_uci = push_move_command
                if 0 <= game_index < len(SERVER_STATE.games):
                    move = chess.Move.from_uci(move_uci)
                    if move in SERVER_STATE.games[game_index][0].board.legal_moves:
                        SERVER_STATE.games[game_index][0].board.push(move)
                        print(f'Pushed {move_uci} to game {game_index}')

            elif (undo_move_command := parse_undo_move(parts)) is not None:
                game_index = undo_move_command
                if 0 <= game_index < len(SERVER_STATE.games):
                    SERVER_STATE.games[game_index][0].board.pop()
                    print(f'Latest move in game {game_index} is undone.')

            elif (rename_command := parse_rename_players(parts)) is not None:
                game_index, p1_name, p2_name = rename_command
                if 0 <= game_index < len(SERVER_STATE.games):
                    SERVER_STATE.games[game_index][0].p1 = p1_name
                    SERVER_STATE.games[game_index][0].p2 = p2_name
                    print(f'For game {game_index}, Player 1 is now "{p1_name}" and Player 2 is now "{p2_name}".')

            elif (pause_command := parse_pause_game(parts)) is not None:
                game_index = pause_command
                if 0 <= game_index < len(SERVER_STATE.games):
                    SERVER_STATE.games[game_index][0].pause()
                    print(f'Game {game_index} is paused.')

            elif (unpause_command := parse_unpause_game(parts)) is not None:
                game_index = unpause_command
                if 0 <= game_index < len(SERVER_STATE.games):
                    SERVER_STATE.games[game_index][0].unpause()
                    print(f'Game {game_index} is unpaused.')

            elif (reorient_command := parse_reorient_game(parts)) is not None:
                game_index, new_orientation = reorient_command
                if 0 <= game_index < len(SERVER_STATE.games):
                    SERVER_STATE.games[game_index][0].orientation = new_orientation
                    print(f'Game {game_index} has been reoriented to {new_orientation}.')

# This function handles the websocket connection lifetime
# from when the connection is established until it is stopped.
async def main_handle(ws_connection):
    global SERVER_STATE
    try:
        # In the client, this message must be sent via the 'open' event handler.
        starting_message = await ws_connection.recv()
        # This message will establish whether it is a client or controller.
        # We only accept a protocol starting with 'client' or 'controller'.
        if starting_message == 'client':
            SERVER_STATE.add_client(ws_connection)
            print('Client has been added:', ws_connection)
        elif starting_message == 'controller':
            success = SERVER_STATE.add_controller(ws_connection)
            if success:
                print('Controller has been added:', ws_connection)
            else:
                print('Controller connection', ws_connection, 'failed')
        # The following needs to be used for every connection
        # (both clients and controllers) to keep the connection alive,
        # even if the clients won't be sending messages to the server.
        async for message in ws_connection:
            await handle_message(message, ws_connection)
    except websockets.exceptions.ConnectionClosed:
        print('Connection closed:', ws_connection)
    finally:
        # Tries both possibilities, preventing an UnboundLocalError.
        SERVER_STATE.remove_client(ws_connection)
        SERVER_STATE.remove_controller(ws_connection)

# Main server cycle.
async def main():
    print('RememBoard server has started.')
    async with websockets.serve(main_handle, 'localhost', PORT_NUMBER, ping_interval=None) as server:
        await server.wait_closed()

if __name__ == '__main__':
    asyncio.run(main())
