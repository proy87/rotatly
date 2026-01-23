from collections.abc import Sequence
from typing import Any

from .utils import lst_to_lst_of_lsts


class Cell:
    colors_dict = {i: c for i, c in enumerate(('red', 'green', 'blue', 'purple'), start=1)}
    names_dict = {1: 'A', 2: 'B', 3: 'C', 4: 'D', 0: ''}
    # Hex colors matching Vite frontend
    hex_colors = {1: '#ff6467', 2: '#7ccf00', 3: '#51a2ff', 4: '#c27aff'}

    def __init__(self, row: int, col: int, for_outline: bool, border_dict: dict, name: int = 0, outline_color: int = 0, connections: dict = None):
        self.row = row
        self.col = col
        self.name = name
        self.outline_color = outline_color  # Target/outline color for border styling
        self.connections = connections or {}  # Which neighbors have the same color
        if for_outline:
            self.display_name = ''
        else:
            self.display_name = self.names_dict[name]
        self.border_dict = border_dict
        self.cell_size = f'var(--cell-size)'
        self.thickness = 'round(down, var(--grid-thickness), 2px)'
        self.for_outline = for_outline

    @property
    def connection_classes(self) -> str:
        """Generate CSS classes for tile connections (same-color neighbors)."""
        classes = []
        if self.connections.get('top'):
            classes.append('conn-top')
        if self.connections.get('bottom'):
            classes.append('conn-bottom')
        if self.connections.get('left'):
            classes.append('conn-left')
        if self.connections.get('right'):
            classes.append('conn-right')
        return ' '.join(classes)

    @property
    def color_class(self) -> str:
        if self.for_outline:
            return self.colors_dict[-self.name] if self.name < 0 else ''
        else:
            return '' if self.name == 0 else self.colors_dict[self.name]

    @property
    def border_color(self) -> str:
        """Get the hex color for border outlines based on TARGET/outline color."""
        key = abs(self.outline_color) if self.outline_color != 0 else 1
        return self.hex_colors.get(key, '#fe9a00')

    @property
    def outline_border_style(self) -> str:
        """Generate CSS border style for outline grid cell.
        
        Logic:
        - Outline extends slightly beyond the tile (5px on each side)
        - Where there's a border (different region): keep the 5px gap
        - Where there's no border (same region): extend to connect (0 gap)
        
        Using CSS calc() with variables:
        - --tile-size: full grid cell size
        - --tile-inner: tile size
        - gap: 5px (space between tile edge and grid cell edge = (tile-size - tile-inner) / 2 = 10px, we use half)
        """
        color = self.border_color
        border_width = '4px'
        
        has_top = self.border_dict.get('top')
        has_bottom = self.border_dict.get('bottom')
        has_left = self.border_dict.get('left')
        has_right = self.border_dict.get('right')
        
        top_w = border_width if has_top else '0'
        bottom_w = border_width if has_bottom else '0'
        left_w = border_width if has_left else '0'
        right_w = border_width if has_right else '0'
        
        # Rounded corners only where two adjacent edges have borders
        radius = '12px'
        top_left = radius if has_top and has_left else '0'
        top_right = radius if has_top and has_right else '0'
        bottom_left = radius if has_bottom and has_left else '0'
        bottom_right = radius if has_bottom and has_right else '0'
        
        # Gap calculation:
        # - Base gap from tile edge = 5px (half of tile margin)
        # - If border exists: use full gap (5px)
        # - If no border: use 0 (extend to connect with neighbor)
        gap = 5  # pixels
        
        m_top = gap if has_top else 0
        m_bottom = gap if has_bottom else 0
        m_left = gap if has_left else 0
        m_right = gap if has_right else 0
        
        # Calculate width and height based on margins
        # width = tile-size - margin-left - margin-right
        # height = tile-size - margin-top - margin-bottom
        width = f'calc(var(--tile-size) - {m_left}px - {m_right}px)'
        height = f'calc(var(--tile-size) - {m_top}px - {m_bottom}px)'
        
        return (
            f'border-color:{color};'
            f'border-top-width:{top_w};'
            f'border-bottom-width:{bottom_w};'
            f'border-left-width:{left_w};'
            f'border-right-width:{right_w};'
            f'border-radius:{top_left} {top_right} {bottom_right} {bottom_left};'
            f'width:{width};'
            f'height:{height};'
            f'margin:{m_top}px {m_right}px {m_bottom}px {m_left}px;'
        )

    @property
    def border_styles(self) -> Sequence[str]:
        increment = f'{self.thickness} / 2'
        length = f'{self.cell_size} + {self.thickness}'
        offset_y = f'{self.cell_size} * {self.row} - {increment}'
        offset_x = f'{self.cell_size} * {self.col} - {increment}'
        # Get color from TARGET/outline for border styling
        bg_color = self.border_color
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
        # Add background-color to each border style
        return [''.join(f'{key}:calc({value});' for key, value in item.items()) + f'background-color:{bg_color};' for item in lst]


def init_borders(outline: Sequence[Any], board: Sequence[Any] | None = None, outline_colors: Sequence[Any] | None = None) -> Sequence[Cell]:
    """
    Create cells with border information.
    
    Args:
        outline: Encoded pattern IDs (for determining where borders should be)
        board: Current board state (for tile colors)
        outline_colors: Actual target colors (for border coloring) - use target_preview_board
    """
    outline = lst_to_lst_of_lsts(outline)
    if board:
        board = lst_to_lst_of_lsts(board)
    if outline_colors:
        outline_colors = lst_to_lst_of_lsts(outline_colors)
    
    cells = []
    grid_size = len(outline)
    border = dict(top=(0, -1), bottom=(0, 1), left=(-1, 0), right=(1, 0))
    
    for row_index, row in enumerate(board or outline):
        current_row = []
        for col_index, digit in enumerate(row):
            outline_value = outline[row_index][col_index]
            
            # Determine borders: show on ALL sides where neighbor has different pattern
            cell_border = {}
            for name, (hor_shift, ver_shift) in border.items():
                i1, i2 = (row_index + ver_shift), (col_index + hor_shift)
                if i1 < 0 or i2 < 0 or i1 >= grid_size or i2 >= len(outline[0]):
                    cell_border[name] = True  # Grid edge
                else:
                    neighbour = outline[i1][i2]
                    cell_border[name] = outline_value != neighbour
            
            # Get actual color for border styling
            # Use outline_colors (target_preview_board) if provided, otherwise fall back
            if outline_colors:
                actual_color = int(outline_colors[row_index][col_index])
            else:
                actual_color = outline_value
            
            # Calculate connections (same-color neighbors) for smooth tile combining
            connections = {}
            for name, (hor_shift, ver_shift) in border.items():
                i1, i2 = (row_index + ver_shift), (col_index + hor_shift)
                if i1 >= 0 and i2 >= 0 and i1 < grid_size and i2 < len(outline[0]):
                    # Check if neighbor has same pattern (same region)
                    neighbour = outline[i1][i2]
                    connections[name] = outline_value == neighbour
                else:
                    connections[name] = False
            
            current_row.append(
                Cell(row_index, col_index,
                     name=digit,
                     for_outline=board is None,
                     border_dict=cell_border,
                     outline_color=actual_color,
                     connections=connections))
        cells.append(current_row)
    return cells
