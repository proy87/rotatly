import math
from collections import deque
from collections.abc import Sequence, Iterable
from typing import Any

from apps.game.utils import encode


class InvalidMoveException(Exception):
    pass


class Node:
    symbol = None
    reverse_symbol = None

    def __init__(self, index, indices: Iterable[int], cols:int, allow_direct: bool = True, allow_reverse: bool = True):
        self.index = index
        self.index0 = index - 1
        self.indices = indices
        self.allow_direct = allow_direct
        self.allow_reverse = allow_reverse
        self.cols = cols

    def get_source_indices(self):
        raise NotImplementedError

    def get_target_indices(self):
        return self.indices

    def move(self, s, direct: bool = True) -> tuple[int, ...]:
        if (direct and not self.allow_direct) or (not direct and not self.allow_reverse):
            raise InvalidMoveException
        s = list(s)
        if direct:
            source_indices = self.get_source_indices()
            target_indices = self.get_target_indices()
        else:
            source_indices = self.get_target_indices()
            target_indices = self.get_source_indices()

        for index, value in zip(target_indices, [s[i] for i in source_indices]):
            s[index] = value
        return tuple(s)

    def name(self):
        return self.__class__.__name__.lower()

    @property
    def row0(self):
        raise NotImplementedError

    @property
    def col0(self):
        raise NotImplementedError

    @property
    def row(self):
        return self.row0 + 1

    @property
    def col(self):
        return self.col0 + 1

    @property
    def source_indices_as_str(self):
        return ','.join(str(s) for s in self.get_source_indices())

    @property
    def target_indices_as_str(self):
        return ','.join(str(s) for s in self.get_target_indices())


class Rotate(Node):
    symbol = '↻'
    reverse_symbol = '↺'

    def get_source_indices(self):
        i, j, k, l = self.indices
        return l, i, j, k

    @property
    def row0(self):
        return self.index0 // (self.cols - 1)

    @property
    def col0(self):
        return self.index0 % (self.cols - 1)


class Horizontal(Node):
    symbol = '→'
    reverse_symbol = '←'

    def get_source_indices(self):
        indices = list(self.indices)
        return [indices[-1]] + indices[:-1]

    @property
    def row0(self):
        return self.index0

    @property
    def col0(self):
        return 0


class Vertical(Horizontal):
    symbol = '↓'
    reverse_symbol = '↑'

    @property
    def row0(self):
        return 0

    @property
    def col0(self):
        return self.index0


def get_nodes(n: int, m: int, disabled_nodes: dict | None = None) -> Sequence[Node]:
    disabled_nodes = disabled_nodes or {}
    def _create_class(klass, ins, idx, s=0):
        disallow_direct, disallow_reverse = disabled_nodes.get(idx + s + 1, (False, False))
        return klass(idx + 1, ins, m, not disallow_direct, not disallow_reverse)

    nodes = []
    index = 0
    # rotate cw and ccw
    for i in range(m * (n - 1)):
        if (i + 1) % m:
            nodes.append(_create_class(Rotate, (i, i + 1, i + m + 1, i + m), index))
            index += 1

    shift = (m - 1) * (n - 1)
    # down and up
    for index in range(m):
        nodes.append(_create_class(Vertical, range(index, n * m, m), index, shift))

    shift += m
    # right and left
    for index in range(n):
        nodes.append(_create_class(Horizontal, range(index * m, (index + 1) * m), index, shift))

    return nodes


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
