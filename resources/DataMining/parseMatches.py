import json, codecs

matchDataF = codecs.open('APIs_Call/badJSONFromOpenData/repairedJSON.data', 'r', 'utf-8-sig')
matchData = json.loads(matchDataF.read())

for data in matchData:
    thisData = open("parsedMatches/{}_{}_match.data".format(str(data['start_time']), str(data['match_id'])), "w")
    thisData.write(json.dumps(data))
    thisData.close()