import math
from collections import deque

from collections.abc import Sequence, Iterable
from typing import Any
from .utils import encode


class Block:
    def __init__(self, index: int, indices: tuple[int, int, int, int], allow_cw: bool = True, allow_ccw: bool = True):
        self.index = index
        self.indices = indices
        self.allow_cw = allow_cw
        self.allow_ccw = allow_ccw

    @classmethod
    def get_blocks(cls, n: int, m: int, disabled_nodes: dict):
        def get_key(index, key):
            if index not in disabled_nodes:
                index = str(index)
            return disabled_nodes.get(index, {}).get(key, False)

        blocks = [(i, i + 1, i + m, i + m + 1) for i in range(m * (n - 1)) if (i + 1) % m]
        return [cls(i, indices, not get_key(i, 'cw'), not get_key(i, 'ccw')) for i, indices in
                enumerate(blocks, start=1)]


def rotate_block(state: tuple[int, ...], block_indices: tuple[int, int, int, int], cw: bool = True) -> tuple:
    s = list(state)
    i, j, k, l = block_indices
    if cw:
        s[i], s[j], s[l], s[k] = s[k], s[i], s[j], s[l]
    else:
        s[i], s[j], s[l], s[k] = s[j], s[l], s[k], s[i]
    return encode(s)


def neighbors(state: tuple[int, ...], blocks: Sequence[Block], reverse: bool = False) -> Iterable[tuple]:
    for block in blocks:
        if reverse:
            if block.allow_ccw:
                yield rotate_block(state, block.indices, True), (block.index, 'CW')
            if block.allow_cw:
                yield rotate_block(state, block.indices, False), (block.index, 'CCW')
        else:
            if block.allow_cw:
                yield rotate_block(state, block.indices, True), (block.index, 'CW')
            if block.allow_ccw:
                yield rotate_block(state, block.indices, False), (block.index, 'CCW')


def bfs(start: Sequence[Any], goal: Sequence[Any], blocks: Sequence[Block]) -> Sequence[tuple] | None:
    max_path_length = 15
    start = encode(start)
    goal = encode(goal)

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
            for nxt, move in neighbors(cur, blocks, reverse=False):
                if nxt not in visited_start:
                    visited_start[nxt] = path + [move]
                    if nxt in visited_goal:
                        # Meeting point found
                        return visited_start[nxt] + [(idx, 'CW' if d == 'CCW' else 'CCW') for idx, d in
                                                     reversed(visited_goal[nxt])]
                    q_start.append(nxt)
        # Expand from goal
        for _ in range(len(q_goal)):
            cur = q_goal.popleft()
            path = visited_goal[cur]
            if len(path) >= (max_path_length // 2):
                continue
            for nxt, move in neighbors(cur, blocks, reverse=True):
                if nxt not in visited_goal:
                    visited_goal[nxt] = path + [move]
                    if nxt in visited_start:
                        # Meeting point found
                        return visited_start[nxt] + [(idx, 'CW' if d == 'CCW' else 'CCW') for idx, d in
                                                     reversed(visited_goal[nxt])]
                    q_goal.append(nxt)
    return None  # unsolvable


def is_solved(start: Sequence[Any], goal: Sequence[Any], moves: Sequence[tuple[int, bool]],
              disabled_nodes: dict) -> bool:
    n = int(math.sqrt(len(start)))
    blocks = {block.index: block for block in Block.get_blocks(n, n, disabled_nodes)}

    for index, cw in moves:
        if index not in blocks:
            return False
        block = blocks[index]
        if getattr(block, f'allow_{'cw' if cw else 'ccw'}'):
            start = rotate_block(start, block.indices, cw)
        else:
            return False
    return start == encode(goal)


def solve(board: Sequence[Any], outline: Sequence[Any], disabled_nodes: dict) -> Sequence[tuple] | None:
    n = int(math.sqrt(len(board)))
    blocks = Block.get_blocks(n, n, disabled_nodes)
    return bfs(board, outline, blocks)
