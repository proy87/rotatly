from collections.abc import Sequence
from typing import Any

from .utils import lst_to_lst_of_lsts


class Cell:
    colors_dict = {i: c for i, c in enumerate(('red', 'green', 'blue', 'purple'), start=1)}
    names_dict = {1: 'A', 2: 'B', 3: 'C', 4: 'D', 0: ''}

    def __init__(self, row: int, col: int, for_outline: bool, border_dict: dict, name: int = 0):
        self.row = row
        self.col = col
        self.name = name
        if for_outline:
            self.display_name = ''
        else:
            self.display_name = self.names_dict[-name if name < 0 else name]
        self.border_dict = border_dict
        self.cell_size = f'var(--cell-size)'
        self.thickness = 'var(--grid-thickness)'
        self.for_outline = for_outline

    @property
    def color_class(self) -> str:
        if self.for_outline:
            return self.colors_dict[-self.name] if self.name < 0 else ''
        else:
            key = -self.name if self.name < 0 else self.name
            return self.colors_dict.get(key, '')

    @property
    def border_styles(self) -> Sequence[str]:
        increment = f'{self.thickness} / 2'
        length = f'{self.cell_size} + {self.thickness}'
        offset_y = f'{self.cell_size} * var(--row, {self.row}) - {increment}'
        offset_x = f'{self.cell_size} * var(--col, {self.col}) - {increment}'
        lst = []
        if self.border_dict.get('left'):
            lst.append(dict(width=self.thickness,
                            height=length,
                            top=offset_y,
                            left=offset_x))
        if self.border_dict.get('top'):
            lst.append(dict(height=self.thickness,
                            width=length,
                            top=offset_y,
                            left=offset_x))
        if self.border_dict.get('right'):
            lst.append(dict(width=self.thickness,
                            height=length,
                            top=offset_y,
                            left=f'{offset_x} + {self.cell_size}'))
        if self.border_dict.get('bottom'):
            lst.append(dict(height=self.thickness,
                            width=length,
                            top=f'{offset_y} + {self.cell_size}',
                            left=offset_x))
        return [''.join(f'{key}:calc({value});' for key, value in item.items()) for item in lst]


def init_borders(outline: Sequence[Any], board: Sequence[Any] | None = None) -> Sequence[Cell]:
    outline = lst_to_lst_of_lsts(outline)
    if board:
        board = lst_to_lst_of_lsts(board)
    cells = []
    border = dict(top=(0, -1), bottom=(0, 1), left=(-1, 0), right=(1, 0))
    for row_index, row in enumerate(board or outline):
        current_row = []
        for col_index, digit in enumerate(row):
            cell_border = {k: True for k in border}
            for name, (hor_shift, ver_shift) in border.items():
                try:
                    i1, i2 = (row_index + ver_shift), (col_index + hor_shift)
                    if i1 < 0 or i2 < 0:
                        raise IndexError
                    neighbour = outline[i1][i2]
                except IndexError:
                    pass
                else:
                    cell_border[name] = name not in ('top', 'left') and outline[row_index][col_index] != neighbour
            current_row.append(
                Cell(row_index, col_index,
                     name=digit,
                     for_outline=board is None,
                     border_dict=cell_border))
        cells.append(current_row)
    return cells
