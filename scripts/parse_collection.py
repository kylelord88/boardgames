import xml.etree.ElementTree as ET
import json, sys, datetime

try:
    tree = ET.parse('raw_collection.xml')
    root = tree.getroot()
except ET.ParseError as e:
    print(f"XML parse error: {e}", file=sys.stderr)
    sys.exit(1)

print(f"Root tag: {root.tag}, total children: {len(list(root))}")

def parse_item(item):
    game_id = item.get('objectid')

    name_el = item.find('name')
    name = name_el.text if name_el is not None else 'Unknown'

    year_el = item.find('yearpublished')
    year = year_el.text if year_el is not None else ''

    thumb_el = item.find('thumbnail')
    thumbnail = thumb_el.text.strip() if thumb_el is not None and thumb_el.text else ''

    image_el = item.find('image')
    image = image_el.text.strip() if image_el is not None and image_el.text else ''

    stats = item.find('stats')
    avg_rating = num_ratings = weight = ''
    min_players = max_players = min_playtime = max_playtime = ''

    if stats is not None:
        min_players = stats.get('minplayers', '')
        max_players = stats.get('maxplayers', '')
        min_playtime = stats.get('minplaytime', '')
        max_playtime = stats.get('maxplaytime', '')
        rating_el = stats.find('rating')
        if rating_el is not None:
            avg_el = rating_el.find('average')
            if avg_el is not None:
                avg_rating = avg_el.get('value', '')
            num_rating_el = rating_el.find('usersrated')
            if num_rating_el is not None:
                num_ratings = num_rating_el.get('value', '')
            weight_el = rating_el.find('averageweight')
            if weight_el is not None:
                weight = weight_el.get('value', '')

    user_rating_el = item.find('.//rating')
    user_rating = ''
    if user_rating_el is not None:
        val = user_rating_el.get('value', '')
        if val not in ('N/A', '0', ''):
            user_rating = val

    num_plays_el = item.find('numplays')
    num_plays = num_plays_el.text if num_plays_el is not None else '0'

    return {
        'id': game_id,
        'name': name,
        'year': year,
        'thumbnail': thumbnail,
        'image': image,
        'avg_rating': avg_rating,
        'num_ratings': num_ratings,
        'user_rating': user_rating,
        'weight': weight,
        'num_plays': num_plays,
        'min_players': min_players,
        'max_players': max_players,
        'min_playtime': min_playtime,
        'max_playtime': max_playtime,
    }

games = []
expansions = []

for item in root.findall('item'):
    subtype = item.get('subtype', '')
    parsed = parse_item(item)
    if subtype == 'boardgameexpansion':
        expansions.append(parsed)
    else:
        parsed['expansions_owned'] = []  # will be filled by fetch_details.py
        games.append(parsed)

games.sort(key=lambda g: g['name'].lower())
expansions.sort(key=lambda g: g['name'].lower())

print(f"Base games: {len(games)}, Expansions: {len(expansions)}")

output = {
    'username': 'eyeamthekiller0',
    'updated': datetime.datetime.utcnow().isoformat() + 'Z',
    'count': len(games),
    'expansion_count': len(expansions),
    'games': games,
    'expansions': expansions,
}

with open('collection.json', 'w') as f:
    json.dump(output, f, indent=2)

print(f"Saved {len(games)} games and {len(expansions)} expansions to collection.json")
