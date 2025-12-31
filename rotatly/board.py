from collections.abc import Sequence
from typing import Any

from .utils import lst_to_lst_of_lsts


class Cell:
    def __init__(self, row: int, col: int, name: int, border_dict: dict, css_variable: str):
        self.row = row
        self.col = col
        self.name = name
        self.display_name = {1: 'A', 2: 'B', 3: 'C', 4: 'D', '': ''}[name]
        self.border_dict = border_dict
        self.cell_width = f'var(--{css_variable})'
        self.thickness = f'{self.cell_width} / 12' if name else '5px'
        self._basic_styles = {'position': 'absolute', 'background-color': 'black'}

    @property
    def color_class(self) -> str:
        return {1: 'red', 2: 'green', 3: 'blue', 4: 'purple'}[self.name]

    @property
    def border_styles(self) -> Sequence[str]:
        increment = f'{self.thickness} / 2'
        length = f'{self.cell_width} + {self.thickness}'
        offset_y = f'{self.cell_width} * {self.row} - {increment}'
        offset_x = f'{self.cell_width} * {self.col} - {increment}'
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
                            left=f'{offset_x} + {self.cell_width}'))
        if self.border_dict.get('bottom'):
            lst.append(dict(height=self.thickness,
                            width=length,
                            top=f'{offset_y} + {self.cell_width}',
                            left=offset_x))
        s = ''.join(f'{key}:{value};' for key, value in self._basic_styles.items())
        return [''.join(f'{key}:calc({value});' for key, value in item.items()) + s for item in lst]


def init_borders(outline: Sequence[Any], css_variable: str, board: Sequence[Any] | None = None) -> Sequence[Cell]:
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
                Cell(row_index, col_index, '' if board is None else digit, cell_border, css_variable))
        cells.append(current_row)
    return cells
