from typing import List, Optional, Tuple
import chess
import re

from conversion import TopLeftSquare
from state import LiveGameState

# Example: 'addgame "P1" "P2" h8 http://192.168.1.47:8080/video wooden'
def parse_add_game(cmd: str) -> Optional[Tuple[LiveGameState, str]]:
    matches = re.match(r'addgame "(.*)" "(.*)" (a1|a8|h1|h8) (.+) (wooden-yolo|handheld-yolo|wooden-rtdetr|handheld-rtdetr)', cmd)
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
def parse_reorient_game(cmd: str) -> Optional[Tuple[int, TopLeftSquare]]:
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

# Example: 'conclude 0 1/2-1/2'
def parse_conclude_game(cmd: str) -> Optional[Tuple[int, str]]:
    matches = re.match(r'conclude (\d+) ([*]|1-0|0-1|1/2-1/2)', cmd)
    if matches is None:
        return None
    index, conclusion = matches.groups()
    return int(index), conclusion

# Example: 'storage insert 0'
def parse_insert_game(cmd: str) -> Optional[int]:
    matches = re.match(r'storage insert (\d+)', cmd)
    if matches is None:
        return None
    index, = matches.groups()
    return int(index)

# Example: 'storage find 0'
def parse_find_game(cmd: str) -> Optional[int]:
    matches = re.match(r'storage find (\d+)', cmd)
    if matches is None:
        return None
    index, = matches.groups()
    return int(index)

# Example: 'storage search "2026-01-31" "White" "Black" "1-0"'
def parse_search_games(cmd: str) -> Optional[Tuple[str, str, str, str]]:
    matches = re.match(r'storage search "(.*)" "(.*)" "(.*)" "(.*)"', cmd)
    if matches is None:
        return None
    date, white, black, result = matches.groups()
    return date, white, black, result

# Example: 'storage delete 0'
def parse_delete_game(cmd: str) -> Optional[int]:
    matches = re.match(r'storage delete (\d+)', cmd)
    if matches is None:
        return None
    index, = matches.groups()
    return int(index)
