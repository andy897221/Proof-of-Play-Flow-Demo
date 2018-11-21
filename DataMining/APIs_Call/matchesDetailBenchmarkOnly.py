import math, time, requests, json
url = 'https://api.opendota.com/api/matches/{}'
match_ids = open('1stAug2018Matches.txt', 'r').read()
match_ids = json.loads(match_ids)
out = open('matchDetailsBenchmark.csv', 'a+', encoding='utf-8')
out.write(str(("{},"*12)[:-1]+"\n").format(
        'match_id',
        'playerNum',
        'isRadiant',
        'gold_per_min',
        'xp_per_min',
        'kills_per_min',
        'last_hits_per_min',
        'hero_damage_per_min',
        'hero_healing_per_min',
        'tower_damage',
        'stuns_per_min',
        "kda"
        ))
outTime = open('matchDetailsTimeDomain.csv', 'a+', encoding='utf-8')
outTime.write(str(("{},"*2)[:-1]+"\n").format('radiant_xp_adv', 'radiant_gold_adv'))

if len(match_ids) > 20000: getMatchNum = 20000
else: getMatchNum = len(match_ids)

for match in range(0, getMatchNum):
    match_id = match_ids[match]["match_id"]
    curReq = url.format(match_id)
    res = json.loads(requests.get(curReq).text)
    playerNum = len(res["players"])
    for player in range(0,playerNum):
        curPlayer = res['players'][player]
        out.write(str(("{},"*12)[:-1]+"\n").format(
            'match_id',
            player,
            curPlayer["isRadiant"],
            curPlayer["benchmarks"]['gold_per_min']['raw'],
            curPlayer["benchmarks"]['xp_per_min']['raw'],
            curPlayer["benchmarks"]['kills_per_min']['raw'],
            curPlayer["benchmarks"]['last_hits_per_min']['raw'],
            curPlayer["benchmarks"]['hero_damage_per_min']['raw'],
            curPlayer["benchmarks"]['hero_healing_per_min']['raw'],
            curPlayer["benchmarks"]['tower_damage']['raw'],
            curPlayer["benchmarks"]['stuns_per_min']['raw'],
            curPlayer["kda"]
            ))
    xp_adv = ""
    for i in res['radiant_xp_adv']: xp_adv+=str(i+" ")
    gold_adv = ""
    for i in res['radiant_xp_adv']: gold_adv+=str(i+" ")
    outTime.write(str(("{},"*2)[:-1]+"\n").format(
        xp_adv[:-1],
        gold_adv[:-1]))
    time.sleep(10)