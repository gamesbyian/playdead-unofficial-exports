import matplotlib.pyplot as plt

def plot_wechsler_string(s):
    # Define the encoding for the characters
    encoding = '0123456789abcdefghijklmnopqrstuv'
    bitstrings = [bin(i)[2:].zfill(5) for i in range(len(encoding))]

    # Mapping from character to bitstring
    char_to_bits = dict(zip(encoding, bitstrings))

    # Initialize an empty list to store the grid
    grid = []

    # Process the input string and construct the grid
    current_row = []
    for char in s:
        if char == 'z':  # Separator for a new strip
            if current_row:  # if current_row is not empty
                grid.append(current_row)
            current_row = []
        elif char in char_to_bits:
            current_row.append(list(map(int, list(char_to_bits[char]))))
        elif char == 'w':  # 'w' represents two zeros
            current_row.append([0, 0])
        elif char == 'x':  # 'x' represents three zeros
            current_row.append([0, 0, 0])

    # Add the last row if it's not empty
    if current_row:
        grid.append(current_row)

    # Flatten the grid for plotting
    flat_grid = [cell for strip in grid for cell in strip]
    n_rows = len(flat_grid)
    n_cols = len(flat_grid[0])

    # Create the figure and axis
    fig, ax = plt.subplots(figsize=(n_cols, n_rows))
    ax.set_xlim(0, n_cols)
    ax.set_ylim(0, n_rows)

    # Remove the axes
    ax.axis('off')

    # Plot each cell
    for i, row in enumerate(flat_grid):
        for j, cell in enumerate(row):
            if cell == 1:
                ax.add_patch(plt.Rectangle((j, n_rows-i-1), 1, 1, fill=True, color='black'))
            else:
                ax.add_patch(plt.Rectangle((j, n_rows-i-1), 1, 1, fill=False, edgecolor='black'))

    # Show the plot
    plt.show()

# Example usage:
pattern_string = '69d1d96'
plot_wechsler_string(pattern_string)
