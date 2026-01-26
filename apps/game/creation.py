import logging
import random
from typing import Iterable, Mapping, Sequence, Any

from apps.game.constants import CUSTOM_GAME_STR, CUSTOM_GAME_SLUG_LENGTH
from apps.game.models import Custom, Daily, Outline
from apps.game.solver import solve
from apps.game.utils import encode

logger = logging.getLogger(__name__)

DEFAULT_OUTLINE_BOARD = (
    0, 0, 1, 1,
    0, 0, 1, 1,
    2, 2, 3, 3,
    2, 2, 3, 3,
)


def get_or_create_default_outline() -> Outline:
    outline = Outline.objects.order_by("index").first()
    if outline:
        return outline
    return Outline.objects.create(index=1, board=DEFAULT_OUTLINE_BOARD)


def get_outline_for_index(index: int | None = None) -> Outline:
    outlines = list(Outline.objects.order_by("index"))
    if outlines:
        if index:
            return outlines[(index - 1) % len(outlines)]
        return random.choice(outlines)
    return get_or_create_default_outline()


def normalize_create_payload(
    outline_items: Iterable[Any],
    board_items: Iterable[Any],
    fixed_areas_items: Mapping[Any, Any],
    disabled_node_items: Iterable[Any],
) -> tuple[list[int] | None, list[int] | None, dict[int, int] | None, dict[str, dict[str, bool]] | None, str | None]:
    mapping: dict[str, int] = {}
    outline: list[int] = []
    next_id = 0
    for item in outline_items:
        if item is None:
            continue
        key = str(item)
        if not key:
            continue
        if key not in mapping:
            mapping[key] = next_id
            next_id += 1
        outline.append(mapping[key])

    if len(outline) != 16:
        return None, None, None, None, "Incomplete outline."
    if len(mapping) != 4:
        return None, None, None, None, "Invalid outline."

    fixed_areas: dict[int, int] = {}
    for key, value in fixed_areas_items.items():
        key = str(key)
        if key not in mapping:
            continue
        try:
            value_int = int(value)
        except (TypeError, ValueError):
            continue
        if not 1 <= value_int <= 4:
            continue
        fixed_areas[mapping[key] + 1] = value_int

    vals = list(fixed_areas.values())
    if len(vals) != len(set(vals)):
        return None, None, None, None, "Invalid outline."
    if len(vals) == 3:
        elements = {1, 2, 3, 4}
        missing_key = (elements - set(fixed_areas.keys())).pop()
        missing_val = (elements - set(vals)).pop()
        fixed_areas[missing_key] = missing_val
    fixed_areas = {k: v for k, v in sorted(fixed_areas.items())}

    board: list[int] = []
    for item in board_items:
        try:
            n = int(item)
            if not 1 <= n <= 4:
                raise ValueError
            board.append(n)
        except (TypeError, ValueError):
            continue

    if len(board) != 16:
        return None, None, None, None, "Incomplete board."
    if any(len([c for c in board if c == e]) != 4 for e in (1, 2, 3, 4)):
        return None, None, None, None, "Invalid board."

    nodes: list[int] = []
    for item in disabled_node_items:
        try:
            n = int(item)
            if not 1 <= n <= 9:
                raise ValueError
            nodes.append(n)
        except (TypeError, ValueError):
            continue

    disabled_nodes = {f"{n}": {"cw": True, "ccw": True} for n in sorted(set(nodes))}
    if len(disabled_nodes) == 9:
        return None, None, None, None, "No active nodes."

    return outline, board, fixed_areas, disabled_nodes, None


def _encode_board_for_storage(board: Sequence[int]) -> list[int]:
    mapping: dict[int, int] = {}
    next_id = 0
    encoded_board: list[int] = []
    for item in board:
        if item not in mapping:
            mapping[item] = next_id
            next_id += 1
        encoded_board.append(mapping[item])
    return encoded_board


def create_custom_puzzle(
    outline: Sequence[int],
    board: Sequence[int],
    fixed_areas: Mapping[int, int],
    disabled_nodes: Mapping[str, dict[str, bool]],
) -> tuple[Custom | None, str | None]:
    outline = tuple(outline)
    try:
        outline_obj = Outline.objects.get(board=outline)
    except Outline.DoesNotExist:
        return None, "Invalid outline."

    board = tuple(board)
    try:
        game = Custom.objects.get(board=board,
                                  disabled_nodes=disabled_nodes,
                                  fixed_areas=fixed_areas,
                                  outline=outline_obj)
        return game, None
    except Custom.DoesNotExist:
        pass

    solution = solve(board=encode(board, fixed_areas),
                     outline=encode(outline_obj.board, fixed_areas, for_outline=True),
                     disabled_nodes=disabled_nodes,
                     fixed_areas=fixed_areas)
    if solution is None:
        return None, "The puzzle is unsolvable."
    if len(solution) == 0:
        return None, "The puzzle is already solved."

    encoded_board = _encode_board_for_storage(board)
    game = Custom.objects.create(
        board=board,
        disabled_nodes=disabled_nodes,
        fixed_areas=fixed_areas,
        outline=outline_obj,
        encoded_board=encoded_board,
        moves_min_num=len(solution),
        index="".join(random.choices(CUSTOM_GAME_STR, k=CUSTOM_GAME_SLUG_LENGTH)),
    )
    return game, None


def create_daily_puzzle(
    outline: Sequence[int],
    board: Sequence[int],
    fixed_areas: Mapping[int, int],
    disabled_nodes: Mapping[str, dict[str, bool]],
    index: int,
) -> tuple[Daily | None, str | None]:
    outline = tuple(outline)
    try:
        outline_obj = Outline.objects.get(board=outline)
    except Outline.DoesNotExist:
        return None, "Invalid outline."

    try:
        game = Daily.objects.get(index=index)
        return game, None
    except Daily.DoesNotExist:
        pass

    board = tuple(board)
    solution = solve(board=encode(board, fixed_areas),
                     outline=encode(outline_obj.board, fixed_areas, for_outline=True),
                     disabled_nodes=disabled_nodes,
                     fixed_areas=fixed_areas)
    if solution is None:
        return None, "The puzzle is unsolvable."
    if len(solution) == 0:
        return None, "The puzzle is already solved."

    encoded_board = _encode_board_for_storage(board)
    game = Daily.objects.create(
        index=index,
        board=board,
        disabled_nodes=disabled_nodes,
        fixed_areas=fixed_areas,
        outline=outline_obj,
        encoded_board=encoded_board,
        moves_min_num=len(solution),
    )
    return game, None


def get_or_create_daily_puzzle(index: int, max_tries: int = 200) -> Daily | None:
    """
    Get daily puzzle for given index, or create one automatically if it doesn't exist.
    This ensures puzzles are always available even if a scheduled task didn't run.
    """
    try:
        return Daily.objects.select_related('outline').get(index=index)
    except Daily.DoesNotExist:
        pass

    # Puzzle doesn't exist, create it on-demand
    outline = get_outline_for_index(index)
    board_template = [1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4]
    retryable_errors = {"The puzzle is unsolvable.", "The puzzle is already solved."}

    last_error = None
    for _ in range(max_tries):
        board = board_template[:]
        random.shuffle(board)
        game, error = create_daily_puzzle(
            outline=outline.board,
            board=board,
            fixed_areas={},
            disabled_nodes={},
            index=index,
        )
        if game:
            logger.info(f"Auto-created daily puzzle for index {index}")
            return game
        last_error = error
        if error not in retryable_errors:
            logger.error(f"Failed to create daily puzzle for index {index}: {error}")
            return None

    logger.error(f"Failed to create daily puzzle for index {index} after {max_tries} tries: {last_error}")
    return None
