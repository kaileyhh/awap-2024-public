import sys
import json
import compress_json
from src.game_state import GameState
from src.map import Map
from src.game_constants import Team, TowerType
from src.tower import Tower
from src.debris import Debris

# python replay_game.py <mapname>.awap24r [--web]
WEB_MODE = False
if len(sys.argv) > 1:
    REPLAY_FILE_PATH = sys.argv[1]
    if '--web' in sys.argv:
        WEB_MODE = True
else:
    print("Please provide the replay file path as a command line argument.")
    print("Example: python replay_game.py <mapname>.awap24r")
    exit()

if REPLAY_FILE_PATH.endswith('.awap24r.gz'):
    replay = compress_json.load(REPLAY_FILE_PATH)
elif REPLAY_FILE_PATH.endswith('.awap24r'):
    with open(REPLAY_FILE_PATH, 'r') as file:
        replay = json.load(file)
else:
    print("Please provide a valid replay file.")

print("Winner", replay['metadata']['winner'])
print("Blue bot", replay['metadata']['blue_bot'])
print("Red bot", replay['metadata']['red_bot'])
map_name = replay['metadata']['map_name']
map_path = f"maps/{map_name}.awap24m"
map = Map(map_path)
gs = GameState(map)
    
def get_tower(team, json_tower):
    id = json_tower['id']
    json_typ = json_tower['type']
    if json_typ == 'solar_farm':
        typ = TowerType.SOLAR_FARM
    elif json_typ == 'gunship':
        typ = TowerType.GUNSHIP
    elif json_typ == 'bomber':
        typ = TowerType.BOMBER
    elif json_typ == 'reinforcer':
        typ = TowerType.REINFORCER
    x = json_tower['x']
    y = json_tower['y']
    max_cooldown = json_tower['max_cooldown']
    cooldown = json_tower['cooldown']

    res = Tower(team, typ, x, y)
    res.id = id
    res.current_cooldown = cooldown
    return res

def get_debris(team, json_debris):
    id = json_debris['id']
    x = json_debris['x']
    y = json_debris['y']
    max_health = json_debris['max_health']
    health = json_debris['health']
    max_cooldown = json_debris['max_cooldown']
    cooldown = json_debris['cooldown']
    sent_by_opponent = json_debris['sent_by_opponent']

    res = Debris(team, x, y, max_cooldown, max_health, sent_by_opponent)
    res.id = id
    res.current_cooldown = cooldown
    res.health = health
    return res

def set_turn(turn):
    gs.turn = turn['turn_number']
    gs.balance[Team.BLUE] = turn['blue_balance']
    gs.balance[Team.RED] = turn['red_balance']
    gs.health[Team.BLUE] = turn['blue_health']
    gs.health[Team.RED] = turn['red_health']
    gs.time_remaining[Team.BLUE] = turn['blue_time_remaining']
    gs.time_remaining[Team.RED] = turn['red_time_remaining']

    gs.towers[Team.BLUE] = {}
    for json_tower in turn['blue_towers']:
        tower = get_tower(Team.BLUE, json_tower)
        gs.towers[Team.BLUE][tower.id] = tower
    gs.towers[Team.RED] = {}
    for json_tower in turn['red_towers']:
        tower = get_tower(Team.RED, json_tower)
        gs.towers[Team.RED][tower.id] = tower
    
    gs.debris[Team.BLUE] = {}
    for json_debris in turn['blue_debris']:
        debris = get_debris(Team.BLUE, json_debris)
        gs.debris[Team.BLUE][debris.id] = debris
    gs.debris[Team.RED] = {}
    for json_debris in turn['red_debris']:
        debris = get_debris(Team.RED, json_debris)
        gs.debris[Team.RED][debris.id] = debris

    gs.current_snipes[Team.BLUE] = turn['blue_snipes']
    gs.current_snipes[Team.RED] = turn['red_snipes']
    gs.current_bombs[Team.BLUE] = turn['blue_bombs']
    gs.current_bombs[Team.RED] = turn['red_bombs']

for turn in replay['turns']:
    set_turn(turn)
    if WEB_MODE:
        pass
        
    try:
        gs.render()
    except:
        print("PyGame may not be compatible with your system. Try running the replay with the --web flag.")
        exit()
