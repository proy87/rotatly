import itertools
import math
import random

from collections.abc import Sequence, Iterable
from typing import Any


def encode(s: Sequence[Any], fixed_areas: dict, for_outline: bool=False) -> tuple[int, ...]:
    mapping = {}
    pattern = []
    next_id = 1
    values = list(fixed_areas.values())
    encode_applied = any(isinstance(ch, int) and ch < 0 for ch in s)
    for ch in s:
        if ch not in mapping:
            if for_outline:
                if next_id in fixed_areas:
                    mapping[ch] = -fixed_areas[next_id]
                else:
                    mapping[ch] = next_id
            else:
                if encode_applied:
                    mapping[ch] = ch if ch < 0 else next_id
                else:
                    mapping[ch] = -ch if ch in values else next_id
            next_id += 1
        pattern.append(mapping[ch])
    return tuple(pattern)


def generate_random_square(n: int) -> tuple[tuple[int, ...], ...]:
    numbers = list(range(1, n + 1))
    random.shuffle(numbers)
    square = [0] * n ** 2
    while numbers:
        number = numbers.pop()
        combinations = list(itertools.combinations([i for i, v in enumerate(square) if v == 0], n))
        random.shuffle(combinations)
        for c in combinations[0]:
            square[c] = number
    return tuple([tuple(square[i: i + n]) for i in range(0, n ** 2, n)])


def generate_all_boards(n: int) -> Iterable[tuple[int, ...]]:
    numbers = list(range(n))

    def inner(sq: list[int], idx: int, prev_comb: tuple[int, ...] | None = None) -> Iterable[tuple[int, ...]]:
        if idx >= n:
            yield tuple(sq)
        else:
            number = numbers[idx]
            for comb in itertools.combinations([i for i, v in enumerate(sq) if v == 0], n):
                if prev_comb is not None and comb[0] < prev_comb[0]:
                    continue
                sqq = sq[::]
                for c in comb:
                    sqq[c] = number
                yield from inner(sqq, idx + 1, comb)

    yield from inner([0] * n ** 2, 0)


def lst_to_lst_of_lsts(lst: Sequence[Any]) -> Sequence[Sequence[Any]]:
    split = int(math.sqrt(len(lst)))
    return tuple(tuple(lst[i: i + split]) for i in range(0, len(lst), split))


def generate_target_preview(board: Sequence[int],
                            outline: Sequence[int],
                            fixed_areas: dict[int, int] | None = None) -> list[int]:
    fixed_areas = fixed_areas or {}
    outline_groups: dict[int, list[int]] = {}
    for idx, group_id in enumerate(outline):
        outline_groups.setdefault(group_id, []).append(idx)

    group_to_color: dict[int, int] = {}
    used_colors: set[int] = set()

    for group_id in outline_groups:
        if group_id < 0:
            color = abs(group_id)
            group_to_color[group_id] = color
            used_colors.add(color)

    for group_id, color in fixed_areas.items():
        if group_id in outline_groups and group_id not in group_to_color:
            group_to_color[group_id] = color
            used_colors.add(color)

    sorted_groups = sorted(outline_groups.items(), key=lambda item: len(item[1]), reverse=True)
    for group_id, indices in sorted_groups:
        if group_id in group_to_color:
            continue
        color_counts: dict[int, int] = {}
        for idx in indices:
            color = board[idx]
            color_counts[color] = color_counts.get(color, 0) + 1
        best_color = None
        best_count = -1
        for color, count in color_counts.items():
            if color in used_colors:
                continue
            if count > best_count:
                best_color = color
                best_count = count
        if best_color is None:
            for color, count in color_counts.items():
                if count > best_count:
                    best_color = color
                    best_count = count
        if best_color is None:
            continue
        group_to_color[group_id] = best_color
        used_colors.add(best_color)

    return [group_to_color[group_id] for group_id in outline]
