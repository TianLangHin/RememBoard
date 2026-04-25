from typing import List, Optional, Tuple
import chess
import re

from conversion import TopLeftSquare
from state import LiveGameState

# Example: 'addgame "P1" "P2" h8 http://192.168.1.47:8080/video wooden'
def parse_add_game(cmd: str) -> Optional[Tuple[LiveGameState, str]]:
    matches = re.match(r'addgame "(.*)" "(.*)" (a1|a8|h1|h8) (.+) (wooden|handheld)', cmd)
    if matches is None:
        return None
    enum_lookup = {
        'a1': TopLeftSquare.A1,
        'a8': TopLeftSquare.A8,
        'h1': TopLeftSquare.H1,
        'h8': TopLeftSquare.H8,
    }
    p1, p2, orientation, stream, board_type = matches.groups()
    orientation = enum_lookup.get(orientation, None)
    if orientation is None:
        return None
    return LiveGameState(p1=p1, p2=p2, orientation=orientation), stream, board_type

# Example: 'removegame 0'
def parse_remove_game(cmd: str) -> Optional[int]:
    matches = re.match(r'removegame (\d+)', cmd)
    if matches is None:
        return None
    return int(matches.group(1))

# Example: 'makemove 0 e2e4'
def parse_push_move(cmd: str) -> Optional[Tuple[int, str]]:
    matches = re.match(r'makemove (\d+) (.+)', cmd)
    if matches is None:
        return None
    index, move = matches.groups()
    return int(index), move

# Example: 'undomove 0'
def parse_undo_move(cmd: str) -> Optional[int]:
    matches = re.match(r'undomove (\d+)', cmd)
    if matches is None:
        return None
    index, = matches.groups()
    return int(index)

# Example: 'renameplayers 0 Magnus Ian'
def parse_rename_players(cmd: str) -> Optional[Tuple[int, str, str]]:
    matches = re.match(r'renameplayers (\d+) "(.*)" "(.*)"', cmd)
    if matches is None:
        return None
    index, p1, p2 = matches.groups()
    return int(index), p1, p2

# Example: 'pausegame 0'
def parse_pause_game(cmd: str) -> Optional[int]:
    matches = re.match(r'pausegame (\d+)', cmd)
    if matches is None:
        return None
    index, = matches.groups()
    return int(index)

# Example: 'unpausegame 0'
def parse_unpause_game(cmd: str) -> Optional[int]:
    matches = re.match(r'unpausegame (\d+)', cmd)
    if matches is None:
        return None
    index, = matches.groups()
    return int(index)

# Example: 'reorient 0 a1'
def parse_reorient_game(cmd: List[str]) -> Optional[Tuple[int, TopLeftSquare]]:
    matches = re.match(r'reorient (\d+) (a1|a8|h1|h8)', cmd)
    if matches is None:
        return None
    index, orientation = matches.groups()
    enum_lookup = {
        'a1': TopLeftSquare.A1,
        'a8': TopLeftSquare.A8,
        'h1': TopLeftSquare.H1,
        'h8': TopLeftSquare.H8,
    }
    orientation = enum_lookup.get(orientation, None)
    if orientation is None:
        return None
    return int(index), orientation
