import matplotlib.pyplot as plt # type: ignore
from matplotlib.patches import Rectangle # type: ignore
import re


def parse_series_name(series_name):
    """
    Parse panel dimensions and cell configuration from series name.
    
    Example: "1745x670-SOLARIX-ME-855-G-904-MATT-SNOW-s54p1M10HC"
    Returns: (width, height, total_cells, parallel_strings)
    
    Format: WIDTHxHEIGHT-...-sXXpYY...
    where XX = cells in series, YY = parallel strings
    """
    # Extract dimensions (e.g., "1745x670")
    dim_match = re.match(r'(\d+)x(\d+)', series_name)
    if not dim_match:
        raise ValueError(f"Cannot parse dimensions from: {series_name}")
    
    height = int(dim_match.group(1))
    width = int(dim_match.group(2))
    
    # Extract cell configuration (e.g., "s54p1")
    cell_match = re.search(r's(\d+)p(\d+)', series_name, re.IGNORECASE)
    if not cell_match:
        raise ValueError(f"Cannot parse cell configuration from: {series_name}")
    
    cells_series = int(cell_match.group(1))
    parallel_strings = int(cell_match.group(2))
    
    total_cells = cells_series * parallel_strings
    
    return width, height, total_cells, parallel_strings


def calculate_cell_layout(panel_width, panel_height, total_cells):
    """
    Determine the optimal cell layout (columns x rows) for a given panel and cell count.
    Tries to find a configuration that fits standard 182x91mm cells.
    
    Returns: (cells_horizontal, cells_vertical, cell_width, cell_height, h_gap, v_gap)
    """
    # Standard half-cut M10 cell dimensions
    CELL_STANDARD_WIDTH = 182  # mm
    CELL_STANDARD_HEIGHT = 91  # mm
    
    # Determine orientation based on panel aspect ratio
    is_landscape = panel_width > panel_height
    
    if is_landscape:
        # Landscape: cells are wider than tall (182x91)
        cell_w = CELL_STANDARD_WIDTH
        cell_h = CELL_STANDARD_HEIGHT
        h_gap = 3    # mm between columns
        v_gap = 1.5  # mm between rows
    else:
        # Portrait: cells are taller than wide (91x182)
        cell_w = CELL_STANDARD_HEIGHT
        cell_h = CELL_STANDARD_WIDTH
        h_gap = 1.5  # mm between columns
        v_gap = 3    # mm between rows
    
    # Find all possible factorizations of total_cells
    possible_configs = []
    for h in range(1, total_cells + 1):
        if total_cells % h == 0:
            v = total_cells // h
            
            # Calculate required space
            req_width = h * cell_w + (h - 1) * h_gap
            req_height = v * cell_h + (v - 1) * v_gap
            
            # Check if it fits
            if req_width <= panel_width and req_height <= panel_height:
                # Calculate how well it fits (prefer configurations that use space efficiently)
                width_usage = req_width / panel_width
                height_usage = req_height / panel_height
                avg_usage = (width_usage + height_usage) / 2
                
                possible_configs.append((h, v, avg_usage))
    
    if not possible_configs:
        raise ValueError(f"Cannot fit {total_cells} cells in panel {panel_width}x{panel_height}mm")
    
    # Choose the configuration with best space usage
    possible_configs.sort(key=lambda x: x[2], reverse=True)
    cells_horizontal, cells_vertical, _ = possible_configs[0]
    
    return cells_horizontal, cells_vertical, cell_w, cell_h, h_gap, v_gap


def draw_panel_sketch(series_name, output_path):
    """
    Generate a portrait-oriented panel sketch by swapping input dimensions.
    """
    try:
        # 1. Parse original dimensions
        orig_width, orig_height, total_cells, parallel_strings = parse_series_name(series_name)
        
        # 2. SWAP dimensions for Portrait (90 degrees CCW rotation)
        # If input is 1745x670, we treat it as 670x1745
        panel_width = orig_width if orig_width < orig_height else orig_height
        panel_height = orig_height if orig_height > orig_width else orig_width
        
        # 3. Calculate cell layout based on new dimensions
        cells_h, cells_v, cell_w, cell_h, h_gap, v_gap = calculate_cell_layout(
            panel_width, panel_height, total_cells
        )
        
        # Create figure
        fig, ax = plt.subplots(1, 1, figsize=(8, 12), facecolor='white')
        ax.set_facecolor('white')
        
        # Draw panel outline
        panel_rect = Rectangle((0, 0), panel_width, panel_height,
                               linewidth=1.5, edgecolor='black', facecolor='none')
        ax.add_patch(panel_rect)
        
        # Calculate total space occupied by cells
        total_cells_width = cells_h * cell_w + (cells_h - 1) * h_gap
        total_cells_height = cells_v * cell_h + (cells_v - 1) * v_gap
        
        # Calculate margins to center the cells
        left_right_margin = (panel_width - total_cells_width) / 2
        top_bottom_margin = (panel_height - total_cells_height) / 2
        
        # Draw cells
        for row in range(cells_v):
            for col in range(cells_h):
                x = left_right_margin + col * (cell_w + h_gap)
                y = top_bottom_margin + row * (cell_h + v_gap)
                
                cell_rect = Rectangle((x, y), cell_w, cell_h,
                                     linewidth=0.5, edgecolor='black', facecolor='none')
                ax.add_patch(cell_rect)
        
        # 4. Update dimension labels to reflect the new orientation
        # Width label on top
        ax.text(panel_width/2, panel_height + 30, str(int(panel_width)), 
                ha='center', va='bottom', fontsize=18, color='black')
        
        # Height label on right
        ax.text(panel_width + 30, panel_height/2, str(int(panel_height)), 
                ha='left', va='center', fontsize=18, color='black', rotation=270)
        
        # Set axis limits
        ax.set_xlim(-50, panel_width + 100)
        ax.set_ylim(-50, panel_height + 100)
        ax.set_aspect('equal')
        ax.axis('off')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
        plt.close()
        
        return True
        
    except Exception as e:
        print(f"Error creating panel sketch: {e}")
        return False


# # Test the function
# if __name__ == "__main__":
#     # Test with the example series
#     test_series = "1745x670-SOLARIX-ME-855-G-904-MATT-SNOW-s54p1M10HC"
#     success = draw_panel_sketch(test_series, "panel_test.png")
#     print(f"Test result: {'Success' if success else 'Failed'}")