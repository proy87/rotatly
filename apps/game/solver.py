import math
from collections import deque
from collections.abc import Sequence, Iterable
from typing import Any

from .board import Node
from .utils import encode


def move(state: tuple[int, ...], node: Node, fixed_areas: dict | None = None, direct: bool = True) -> tuple:
    s = node.move(state, direct=direct)
    return s if fixed_areas is None else encode(s, fixed_areas)


def neighbors(state: tuple[int, ...], nodes: Sequence[Node], fixed_areas: dict, reverse: bool = False) -> Iterable[
    tuple]:
    for node in nodes:
        if reverse:
            if node.allow_reverse:
                yield move(state, node, fixed_areas, True), (node.index, node.reverse_symbol)
            if node.allow_direct:
                yield move(state, node, fixed_areas, False), (node.index, node.symbol)
        else:
            if node.allow_direct:
                yield move(state, node, fixed_areas, True), (node.index, node.symbol)
            if node.allow_reverse:
                yield move(state, node, fixed_areas, False), (node.index, node.reverse_symbol)


def bfs(start: tuple[int, ...], goal: tuple[int, ...], nodes: Sequence[Node], fixed_areas: dict) -> Sequence[
                                                                                                        tuple] | None:
    max_path_length = 25

    if start == goal:
        return []

    # BFS from start
    q_start = deque([start])
    visited_start = {start: []}
    # BFS from goal
    q_goal = deque([goal])
    visited_goal = {goal: []}
    while q_start and q_goal:
        # Expand from start
        for _ in range(len(q_start)):
            cur = q_start.popleft()
            path = visited_start[cur]
            if len(path) >= (max_path_length // 2 + (max_path_length % 2)):
                continue
            for nxt, mv in neighbors(cur, nodes, fixed_areas, reverse=False):
                if nxt not in visited_start:
                    visited_start[nxt] = path + [mv]
                    if nxt in visited_goal:
                        # Meeting point found
                        return visited_start[nxt] + list(reversed(visited_goal[nxt]))
                    q_start.append(nxt)
        # Expand from goal
        for _ in range(len(q_goal)):
            cur = q_goal.popleft()
            path = visited_goal[cur]
            if len(path) >= (max_path_length // 2):
                continue
            for nxt, mv in neighbors(cur, nodes, fixed_areas, reverse=True):
                if nxt not in visited_goal:
                    visited_goal[nxt] = path + [mv]
                    if nxt in visited_start:
                        # Meeting point found
                        return visited_start[nxt] + list(reversed(visited_goal[nxt]))
                    q_goal.append(nxt)
    return None  # unsolvable


def is_solved(start: Sequence[Any], goal: Sequence[Any], moves: Sequence[tuple[int, bool]],
              fixed_areas: dict, disabled_nodes: dict) -> bool:
    return False
    n = int(math.sqrt(len(start)))
    blocks = {block.index: block for block in Block.get_blocks(n, n, disabled_nodes)}
    for index, cw in moves:
        if index not in blocks:
            return False
        block = blocks[index]
        if getattr(block, f'allow_{'cw' if cw else 'ccw'}'):
            start = rotate_block(start, block.indices, fixed_areas, cw)
        else:
            return False
    return start == encode(goal, fixed_areas, for_outline=True)


def solve(board: tuple[int, ...], outline: tuple[int, ...], nodes: Sequence[Node], fixed_areas: dict) -> Sequence[
                                                                                                             tuple] | None:
    return bfs(board, outline, nodes, fixed_areas)
