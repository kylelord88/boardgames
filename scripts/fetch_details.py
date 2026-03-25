import json, urllib.request, urllib.error
import xml.etree.ElementTree as ET
import time, os, sys

with open('collection.json') as f:
    data = json.load(f)

games = data['games']
expansions = data.get('expansions', [])
token = os.environ['BGG_TOKEN']

# Build lookup maps
game_map = {g['id']: g for g in games}
expansion_map = {e['id']: e for e in expansions}

all_ids = [g['id'] for g in games] + [e['id'] for e in expansions]
print(f"Fetching details for {len(games)} games + {len(expansions)} expansions ({len(all_ids)} total)...")

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

details = {}
for batch_num, batch in enumerate(chunks(all_ids, 20)):
    id_str = ','.join(batch)
    url = f'https://boardgamegeek.com/xmlapi2/thing?id={id_str}&type=boardgame,boardgameexpansion'
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'})
    xml_data = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                xml_data = resp.read()
            break
        except Exception as e:
            print(f"  Batch {batch_num+1} attempt {attempt+1} failed: {e}")
            time.sleep(8)

    if not xml_data:
        print(f"  Batch {batch_num+1} skipped after all retries")
        continue

    try:
        root = ET.fromstring(xml_data)
        for item in root.findall('item'):
            gid = item.get('id')
            categories = [l.get('value') for l in item.findall('link[@type="boardgamecategory"]')]
            mechanics  = [l.get('value') for l in item.findall('link[@type="boardgamemechanic"]')]
            families   = [l.get('value') for l in item.findall('link[@type="boardgamefamily"]')]
            # For expansions: get which base game they belong to
            expands    = [l.get('id') for l in item.findall('link[@type="boardgameexpansion"]')
                          if l.get('inbound') == 'true']
            details[gid] = {
                'categories': categories,
                'mechanics': mechanics,
                'families': families,
                'expands': expands,
            }
        print(f"  Batch {batch_num+1} done ({len(batch)} items)")
    except ET.ParseError as e:
        print(f"  Batch {batch_num+1} XML parse error: {e}")

    time.sleep(2)

# Apply details to base games
for game in games:
    d = details.get(game['id'], {})
    game['categories'] = d.get('categories', [])
    game['mechanics']  = d.get('mechanics', [])
    game['families']   = d.get('families', [])
    game['expansions_owned'] = []  # reset, will fill below

# Match owned expansions to their base games
matched = 0
for exp in expansions:
    d = details.get(exp['id'], {})
    exp['categories'] = d.get('categories', [])
    exp['mechanics']  = d.get('mechanics', [])
    exp['families']   = d.get('families', [])
    expands_ids = d.get('expands', [])
    for base_id in expands_ids:
        if base_id in game_map:
            game_map[base_id]['expansions_owned'].append({
                'id': exp['id'],
                'name': exp['name'],
                'year': exp['year'],
                'thumbnail': exp['thumbnail'],
            })
            matched += 1

print(f"Matched {matched} expansions to base games")

data['games'] = games
data['expansions'] = expansions
with open('collection.json', 'w') as f:
    json.dump(data, f, indent=2)

print(f"Done. Details added for {len(details)} items.")
