import json, urllib.request, urllib.error
import xml.etree.ElementTree as ET
import time, os, sys

with open('collection.json') as f:
    data = json.load(f)

games = data['games']
ids = [g['id'] for g in games]
token = os.environ['BGG_TOKEN']

print(f"Fetching details for {len(ids)} games...")

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

details = {}
for batch_num, batch in enumerate(chunks(ids, 20)):
    id_str = ','.join(batch)
    url = f'https://boardgamegeek.com/xmlapi2/thing?id={id_str}&type=boardgame'
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
            details[gid] = {'categories': categories, 'mechanics': mechanics, 'families': families}
        print(f"  Batch {batch_num+1} done ({len(batch)} games)")
    except ET.ParseError as e:
        print(f"  Batch {batch_num+1} XML parse error: {e}")

    time.sleep(2)

for game in games:
    d = details.get(game['id'], {})
    game['categories'] = d.get('categories', [])
    game['mechanics']  = d.get('mechanics', [])
    game['families']   = d.get('families', [])

data['games'] = games
with open('collection.json', 'w') as f:
    json.dump(data, f, indent=2)

print(f"Details added for {len(details)} games")
