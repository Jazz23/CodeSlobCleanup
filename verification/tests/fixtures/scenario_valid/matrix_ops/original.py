from typing import List

def blur_image(grid: List[List[int]]) -> List[List[int]]:
    """
    Applies a 3x3 box blur.
    Slob: Deep nesting, manual boundary checks everywhere.
    """
    if not grid:
        return []
    if not grid[0]:
        return [[] for _ in grid]
        
    rows = len(grid)
    cols = len(grid[0])
    new_grid = []
    
    for r in range(rows):
        new_row = []
        for c in range(cols):
            # Calculate average of neighbors
            total = 0
            count = 0
            
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    nr = r + dr
                    nc = c + dc
                    
                    if 0 <= nr < rows and 0 <= nc < cols:
                        # Brittle: assumes rows are same length
                        try:
                            val = grid[nr][nc]
                            if isinstance(val, int):
                               total += val
                               count += 1
                        except IndexError:
                            pass
            
            avg = total // count if count > 0 else 0
            new_row.append(avg)
        new_grid.append(new_row)
        
    return new_grid

def rotate_right(grid: List[List[int]]) -> List[List[int]]:
    """
    Rotates matrix 90 degrees clockwise.
    Slob: Allocating new list with loops.
    """
    if not grid:
        return []
    if not grid[0]:
        return [[] for _ in range(0)] # This is weird but whatever
        
    rows = len(grid)
    cols = len(grid[0])
    
    new_grid = []
    for _ in range(cols):
        row = []
        for _ in range(rows):
            row.append(0)
        new_grid.append(row)
        
    for r in range(rows):
        for c in range(cols):
            try:
                new_grid[c][rows - 1 - r] = grid[r][c]
            except IndexError:
                pass
            
    return new_grid