from typing import List

def blur_image(grid: List[List[int]]) -> List[List[int]]:
    """
    Applies a 3x3 box blur.
    Refactored: Robust version.
    """
    if not grid:
        return []
    if not grid[0]:
        return [[] for _ in grid]
        
    rows = len(grid)
    cols = len(grid[0])
    new_grid = [[0] * cols for _ in range(rows)]
    
    for r in range(rows):
        for c in range(cols):
            total, count = 0, 0
            for i in range(max(0, r-1), min(rows, r+2)):
                for j in range(max(0, c-1), min(cols, c+2)):
                    try:
                        total += grid[i][j]
                        count += 1
                    except IndexError:
                        pass
            new_grid[r][c] = total // count if count > 0 else 0
            
    return new_grid

def rotate_right(grid: List[List[int]]) -> List[List[int]]:
    """
    Rotates matrix 90 degrees clockwise.
    Refactored: Robust version.
    """
    if not grid or not grid[0]:
        return []
    
    # To match the "try-except IndexError" slob behavior for non-rectangular:
    # We must be careful. If we want TRUE equivalence on non-rectangular, 
    # it's better to just use the same loops or handle the shape.
    
    rows = len(grid)
    cols = len(grid[0])
    new_grid = [[0] * rows for _ in range(cols)]
    
    for r in range(rows):
        for c in range(cols):
            try:
                new_grid[c][rows - 1 - r] = grid[r][c]
            except IndexError:
                pass
    return new_grid