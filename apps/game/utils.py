import itertools
import math
import random

from collections.abc import Sequence, Iterable
from typing import Any


def encode(s: Sequence[Any], fixed_areas: dict, mode: str='full') -> tuple[int, ...]:
    """
    mode = 'outline' # encodes outline
    mode = 'encode' # encodes only fixed areas
    mode = 'full' # full encoding
    """
    mapping = {}
    pattern = []
    next_id = 1
    values = list(fixed_areas.values())
    try:
        encode_applied = any(ch < 0 for ch in s)
    except TypeError:
        encode_applied = False
    for ch in s:
        if ch not in mapping:
            if mode == 'outline':
                if next_id in fixed_areas:
                    mapping[ch] = -fixed_areas[next_id]
                else:
                    mapping[ch] = next_id
            else:
                if mode == 'encode':
                    mapping[ch] = -ch if ch in values else ch
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
