from collections.abc import Iterable


GRID_SIZE = 4
CELLS_TOTAL = GRID_SIZE * GRID_SIZE


def _normalize_shape(shape: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    rows = [r for r, _ in shape]
    cols = [c for _, c in shape]
    min_r = min(rows)
    min_c = min(cols)
    normalized = tuple(sorted((r - min_r, c - min_c) for r, c in shape))
    return normalized


def _rotate_shape(shape: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    rotated = [(c, -r) for r, c in shape]
    return _normalize_shape(rotated)


def _unique_rotations(shape: Iterable[tuple[int, int]]) -> list[tuple[tuple[int, int], ...]]:
    rotations = set()
    current = _normalize_shape(shape)
    for _ in range(4):
        rotations.add(current)
        current = _rotate_shape(current)
    return sorted(rotations)


def _tetromino_shapes() -> list[tuple[tuple[int, int], ...]]:
    shapes = [
        ((0, 0), (0, 1), (0, 2), (0, 3)),  # I
        ((0, 0), (0, 1), (1, 0), (1, 1)),  # O
        ((0, 0), (0, 1), (0, 2), (1, 1)),  # T
        ((0, 0), (1, 0), (2, 0), (2, 1)),  # L
        ((0, 1), (1, 1), (2, 1), (2, 0)),  # J
        ((0, 1), (0, 2), (1, 0), (1, 1)),  # S
        ((0, 0), (0, 1), (1, 1), (1, 2)),  # Z
    ]
    rotations = []
    for shape in shapes:
        rotations.extend(_unique_rotations(shape))
    return rotations


def _generate_placements() -> list[tuple[int, ...]]:
    placements = set()
    for shape in _tetromino_shapes():
        max_r = max(r for r, _ in shape)
        max_c = max(c for _, c in shape)
        for r in range(GRID_SIZE - max_r):
            for c in range(GRID_SIZE - max_c):
                indices = tuple(sorted((r + dr) * GRID_SIZE + (c + dc) for dr, dc in shape))
                placements.add(indices)
    return sorted(placements)


def generate_outline_boards() -> list[tuple[int, ...]]:
    placements = _generate_placements()
    placements_by_cell: dict[int, list[tuple[int, ...]]] = {i: [] for i in range(CELLS_TOTAL)}
    for placement in placements:
        for idx in placement:
            placements_by_cell[idx].append(placement)

    boards: list[tuple[int, ...]] = []
    board = [-1] * CELLS_TOTAL

    def backtrack(group_id: int) -> None:
        if group_id == 4:
            boards.append(tuple(board))
            return
        try:
            first_empty = board.index(-1)
        except ValueError:
            return
        for placement in placements_by_cell[first_empty]:
            if all(board[idx] == -1 for idx in placement):
                for idx in placement:
                    board[idx] = group_id
                backtrack(group_id + 1)
                for idx in placement:
                    board[idx] = -1

    backtrack(0)
    return boards
