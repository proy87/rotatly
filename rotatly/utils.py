import itertools
import math
import random

from collections.abc import Sequence, Iterable
from typing import Any


def encode(s: Sequence[Any]) -> tuple[int, ...]:
    mapping = {}
    pattern = []
    next_id = 0
    for ch in s:
        if ch not in mapping:
            mapping[ch] = next_id
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


def get_all_squares(n: int) -> Iterable[tuple[tuple[int, ...], ...]]:
    numbers = list(range(1, n + 1))

    def inner(sq: list[int], idx: int, prev_comb: tuple[int, ...] | None = None) -> Iterable[
        tuple[tuple[int, ...], ...]]:
        if idx >= len(numbers):
            yield tuple([tuple(sq[i: i + n]) for i in range(0, n ** 2, n)])
        else:
            number = numbers[idx]
            for comb in itertools.combinations([i for i, v in enumerate(sq) if v == 0], n):
                if prev_comb is not None and min(comb) < min(prev_comb):
                    continue
                sqq = sq[::]
                for c in comb:
                    sqq[c] = number
                yield from inner(sqq, idx + 1, comb)

    yield from inner([0] * n ** 2, 0)


def lst_to_lst_of_lsts(lst: Sequence[Any], split: int | None = None) -> Sequence[Sequence[Any]]:
    split = split or int(math.sqrt(len(lst)))
    return tuple(tuple(lst[i: i + split]) for i in range(0, len(lst), split))
