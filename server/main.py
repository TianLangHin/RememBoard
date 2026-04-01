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
        self.connected_clients.remove(ws_connection)
        ws_connection.close()
    # Returns True if successful.
    def add_controller(self, ws_connection) -> bool:
        if self.connected_controller is None:
            self.connected_controller = ws_connection
            return True
        return False
    def remove_controller(self, ws_connection):
        if self.connected_controller == ws_connection:
            self.connected_controller.close()
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

# Example: 'addgame P1 P2 h8 http://192.168.1.47:8080/video'
def parse_add_game(cmd: list[str]) -> Optional[Tuple[LiveGameState, str]]:
    if len(cmd) < 5:
        return None
    if cmd[0] != 'addgame':
        return None
    p1, p2 = cmd[1], cmd[2]
    enum_lookup = {
        'a1': TopLeftSquare.A1,
        'a8': TopLeftSquare.A8,
        'h1': TopLeftSquare.H1,
        'h8': TopLeftSquare.H8,
    }
    orientation = enum_lookup.get(cmd[3], None)
    if orientation is None:
        return None
    stream = cmd[4]
    return LiveGameState(p1=p1, p2=p2, orientation=orientation), stream

def parse_remove_game(cmd: list[str]) -> Optional[int]:
    if len(cmd) < 2:
        return None
    if cmd[0] != 'removegame':
        return None
    if not cmd[1].isnumeric():
        return None
    return int(cmd[1])

async def handle_message(message: str, ws_connection):
    async with lock:
        global SERVER_STATE
        if ws_connection == SERVER_STATE.connected_controller:
            parts = message.split()
            if message == 'inference':
                statuses_to_controller = []
                images_to_client = []
                fens = []
                # Computer vision inference is triggered by the controller
                # sending the "inference" message to the server.
                for game_state, video_stream in SERVER_STATE.games:
                    frame = read_and_resize_frame(video_stream)
                    result = MODEL.predict(frame, imgsz=640, conf=0.25, verbose=False)[0]
                    prediction = yolo_inference_to_piece_list(
                        result,
                        warped=True,
                        orientation=game_state.orientation)
                    status_string = {
                        PredictionStatus.ValidMove: 'v',
                        PredictionStatus.InvalidMove: 'i',
                        PredictionStatus.AmbiguousMove: 'a',
                        PredictionStatus.Obstructed: 'o',
                    }
                    if prediction is not None:
                        # `possible_moves` will be given to the controller,
                        # but currently that is not implemented.
                        predict_status, possible_moves = get_predicted_transition(
                            known_board=game_state.board,
                            piece_list=prediction,
                            match_exact=True)
                        if predict_status == PredictionStatus.ValidMove:
                            if possible_moves[0] != chess.Move.null():
                                game_state.push_move(possible_moves[0])
                                print('Valid move found:', possible_moves[0])
                                print('New game state:', game_state.board.fen())
                        else:
                            # Might need to put automatic pausing here.
                            pass
                    else:
                        predict_status = PredictionStatus.Obstructed
                    # plotted_img = cv2.imencode('.png', result.plot(font_size=20))[1]
                    plotted_img = cv2.imencode('.png', frame)[1]
                    statuses_to_controller.append(f'{status_string[predict_status]}|{game_state.serialise()}')
                    images_to_client.append(base64.b64encode(plotted_img.tobytes()).decode('utf-8'))
                    fens.append(game_state.board.fen())
                # After inference is conducted, we finally distribute the messages to each connection.
                # The clients need the images and FEN of each game.
                for client in SERVER_STATE.connected_clients:
                    payload = [f'{a}|{b}' for a, b in zip(images_to_client, fens)]
                    await client.send(','.join(payload))
                # The controller needs to know the status of each game.
                if SERVER_STATE.connected_controller is not None:
                    payload = [f'{a}|{b}' for a, b in zip(statuses_to_controller, fens)]
                    await SERVER_STATE.connected_controller.send(','.join(payload))
            elif (add_game_command := parse_add_game(parts)) is not None:
                game_state, stream_uri = add_game_command
                video = BufferlessVideo(stream_uri)
                SERVER_STATE.add_new_game(game_state, video)
                print(f'Added game: {stream_uri}')
            elif (remove_game_command := parse_remove_game(parts)) is not None:
                remove_index = remove_game_command
                SERVER_STATE.remove_game(remove_index)
                print(f'Removed game at index: {remove_index}')
            # Also need to make commands for push/undo move/rename players.

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
        if starting_message == 'client':
            SERVER_STATE.remove_client(ws_connection)
        elif starting_message == 'controller':
            SERVER_STATE.remove_controller(ws_connection)


# Main server cycle.
async def main():
    print('RememBoard server has started.')
    async with websockets.serve(main_handle, 'localhost', PORT_NUMBER, ping_interval=None) as server:
        await server.wait_closed()

if __name__ == '__main__':
    asyncio.run(main())
