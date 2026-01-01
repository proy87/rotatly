import math
import heapq
from collections import deque

from collections.abc import Sequence, Iterable
from typing import Any, Self
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
    max_path_length = 12
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

    nodes_expanded = 0
    while q_start and q_goal:
        nodes_expanded += 1
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


class StateNode:
    def __init__(self, state: Sequence[Any], f: int = 0, g: int = 0, move: tuple[int, bool] | None = None,
                 parent: Self | None = None):
        self.state = state
        self.g = g
        self.move = move
        self.parent = parent
        self.f = f

    def __lt__(self, other: Self) -> bool:
        return self.f < other.f


def heuristic(state: Sequence[Any], target: Sequence[Any]) -> int:
    misplaced = sum(a != b for a, b in zip(state, target))
    return (misplaced + 3) // 4


def reconstruct_path(node: StateNode) -> list[StateNode]:
    path = []
    while node.parent is not None:
        path.append(node.move)
        node = node.parent
    path.reverse()
    return path


def a_star(start: Sequence[Any], goal: Sequence[Any], blocks: Sequence[Block]) -> Sequence[tuple] | None:
    max_len = 30
    start = encode(start)
    goal = encode(goal)
    if start == goal:
        return []

    # Initialize frontiers
    fwd_pq = []
    bwd_pq = []

    start_node = StateNode(start, f=heuristic(start, goal), g=0)
    goal_node = StateNode(goal, f=heuristic(goal, start), g=0)

    heapq.heappush(fwd_pq, start_node)
    heapq.heappush(bwd_pq, goal_node)

    fwd_visited = {start: start_node}
    bwd_visited = {goal: goal_node}

    meeting_state = None
    min_dist = max_len + 1

    while fwd_pq and bwd_pq:
        # --- Forward step ---
        current = heapq.heappop(fwd_pq)
        for nxt, move in neighbors(current.state, blocks, reverse=False):
            g_new = current.g + 1
            f_new = g_new + heuristic(nxt, goal)
            if f_new >= min_dist:
                continue
            if nxt not in fwd_visited or g_new < fwd_visited[nxt].g:
                nxt_node = StateNode(nxt, g=g_new, move=move, parent=current)
                nxt_node.f = f_new
                fwd_visited[nxt] = nxt_node
                heapq.heappush(fwd_pq, nxt_node)

            if nxt in bwd_visited:
                total_dist = g_new + bwd_visited[nxt].g
                if total_dist < min_dist:
                    min_dist = total_dist
                    meeting_state = nxt

        # --- Backward step ---
        current = heapq.heappop(bwd_pq)
        for nxt, move in neighbors(current.state, blocks, reverse=True):
            g_new = current.g + 1
            f_new = g_new + heuristic(nxt, start)
            if f_new >= min_dist:
                continue
            if nxt not in bwd_visited or g_new < bwd_visited[nxt].g:
                nxt_node = StateNode(nxt, g=g_new, move=move, parent=current)
                nxt_node.f = f_new
                bwd_visited[nxt] = nxt_node
                heapq.heappush(bwd_pq, nxt_node)

            if nxt in fwd_visited:
                total_dist = g_new + fwd_visited[nxt].g
                if total_dist < min_dist:
                    min_dist = total_dist
                    meeting_state = nxt

        if meeting_state is not None:
            break

    if meeting_state is None:
        return None

    # Reconstruct path
    fwd_path = reconstruct_path(fwd_visited[meeting_state])
    bwd_path = reconstruct_path(bwd_visited[meeting_state])
    full_path = fwd_path + [(k, 'CCW' if v == 'CW' else 'CW') for k, v in bwd_path[::-1]]
    return full_path


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
