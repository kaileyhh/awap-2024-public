import json
import compress_json
from colorama import Fore, Back, Style, init
import time

init(autoreset=True)  

# Command line argument for the replay file path
import sys
if len(sys.argv) > 1:
    REPLAY_FILE_PATH = sys.argv[1]
else:
    print("Please provide the replay file path as a command line argument.")
    print("Example: python3 replay_game.py <filename>.awap24r")
    exit()

def load_replay(file_path):
    if file_path.endswith('.awap24r.gz'):
        replay_data = compress_json.load(REPLAY_FILE_PATH)
    elif file_path.endswith('.awap24r'):
        with open(file_path, 'r') as file:
            replay_data = json.load(file)
    else:
        print("Please provide a valid replay file.")
    return replay_data

def visualize_turn(turn, metadata):
    # Create a grid with the path
    grid = [[' ' for _ in range(metadata['map_width'])] for _ in range(metadata['map_height'])]
    for path_coord in metadata['map_path']:
        x, y = path_coord
        grid[y][x] = Fore.RESET + Back.RESET + '-'

    # Add towers to the grid
    for tower in turn['blue_towers']:
        grid[tower['y']][tower['x']] = Fore.BLUE + 'B' if tower.get('cooldown', 0) == 0 else Fore.CYAN + 'b'  # Blue tower or bomb
    for tower in turn['red_towers']:
        grid[tower['y']][tower['x']] = Fore.RED + 'R' if tower.get('cooldown', 0) == 0 else Fore.MAGENTA + 'r'  # Red tower or bomb

    # Add balloons to the grid
    for balloon in turn['blue_bombs']:
        x, y = balloon
        grid[y][x] = Fore.BLUE + 'B'
    for balloon in turn['red_bombs']:
        x, y = balloon
        grid[y][x] = Fore.RED + 'R'

    # Display the grid 
    for row in grid:
        print(' '.join(row))

    print(f"Turn Number: {turn['turn_number']}")
    print(f"Red Balance: {turn['red_balance']}, Blue Balance: {turn['blue_balance']}")
    time.sleep(0.001)  # Adjust replay speed

# Load game replay from file
replay = load_replay(REPLAY_FILE_PATH)

# Parse metadata
metadata = replay['metadata']
game_name = metadata['game_name']
print(f"Game Name: {metadata['game_name']}")
print(f"Map Name: {metadata['map_name']}")
print(f"Map Size: {metadata['map_width']}x{metadata['map_height']}")
print(f"Players: {metadata['red_bot']} vs {metadata['blue_bot']}")
time.sleep(1)


# Visualize each turn
for turn in replay['turns']:
    visualize_turn(turn, metadata)