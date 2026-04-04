from typing import List, Optional, Tuple
import chess

from conversion import TopLeftSquare
from state import LiveGameState

# Example: 'addgame P1 P2 h8 http://192.168.1.47:8080/video'
def parse_add_game(cmd: List[str]) -> Optional[Tuple[LiveGameState, str]]:
    if len(cmd) < 5 or cmd[0] != 'addgame':
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

# Example: 'removegame 0'
def parse_remove_game(cmd: List[str]) -> Optional[int]:
    if len(cmd) < 2 or cmd[0] != 'removegame' or not cmd[1].isnumeric():
        return None
    return int(cmd[1])

# Example: 'makemove 0 e2e4'
def parse_push_move(cmd: List[str]) -> Optional[Tuple[int, str]]:
    if len(cmd) < 3 or cmd[0] != 'makemove' or not cmd[1].isnumeric():
        return None
    return int(cmd[1]), cmd[2]

# Example: 'undomove 0'
def parse_undo_move(cmd: List[str]) -> Optional[int]:
    if len(cmd) < 2 or cmd[0] != 'undomove' or not cmd[1].isnumeric():
        return None
    return int(cmd[1])

# Example: 'renameplayers 0 Magnus Ian'
def parse_rename_players(cmd: List[str]) -> Optional[Tuple[int, str, str]]:
    if len(cmd) < 4 or cmd[0] != 'renameplayers' or not cmd[1].isnumeric():
        return None
    return int(cmd[1]), cmd[2], cmd[3]

# Example: 'pausegame 0'
def parse_pause_game(cmd: List[str]) -> Optional[int]:
    if len(cmd) < 2 or cmd[0] != 'pausegame' or not cmd[1].isnumeric():
        return None
    return int(cmd[1])

# Example: 'unpausegame 0'
def parse_unpause_game(cmd: List[str]) -> Optional[int]:
    if len(cmd) < 2 or cmd[0] != 'unpausegame' or not cmd[1].isnumeric():
        return None
    return int(cmd[1])

# Example: 'reorient 0 a1'
def parse_reorient_game(cmd: List[str]) -> Optional[Tuple[int, TopLeftSquare]]:
    if len(cmd) < 3 or cmd[0] != 'reorient' or not cmd[1].isnumeric():
        return None
    enum_lookup = {
        'a1': TopLeftSquare.A1,
        'a8': TopLeftSquare.A8,
        'h1': TopLeftSquare.H1,
        'h8': TopLeftSquare.H8,
    }
    orientation = enum_lookup.get(cmd[2], None)
    if orientation is None:
        return None
    return int(cmd[1]), orientation
