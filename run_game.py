#!/usr/bin/env python3

from src.game import Game
import argparse
import json

def main():
    parser = argparse.ArgumentParser(description="Run the game")
    parser.add_argument("-b", "--blue_path", type=str, required=False)
    parser.add_argument("-r", "--red_path", type=str, required=False)
    parser.add_argument("-m", "--map_path", type=str, required=False)
    parser.add_argument("-c", "--config_file", type=str, required=False)
    parser.add_argument("--render", action="store_true", help="Whether or not to display the game while it is running")
    args = parser.parse_args()

    if args.config_file:
        configs = json.load(open(args.config_file))
        blue_path = configs["bots"][0]
        red_path = configs["bots"][1]
        map_path = configs["map"]
    else:
        if not args.blue_path or not args.red_path or not args.map_path:
            raise Exception("Must provide --blue_path, --red_path, and --map_path if not using --config_file")
        blue_path = args.blue_path
        red_path = args.red_path
        map_path = args.map_path

    game = Game(
        blue_path=blue_path,
        red_path=red_path,
        map_path=map_path,
        render=args.render
    )
    winner = game.run_game()
    print(f"Winner: {winner}")

if __name__ == "__main__":
    main()