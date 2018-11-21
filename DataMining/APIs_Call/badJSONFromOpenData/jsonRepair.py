import sys

f = open(sys.argv[1], 'r', encoding='utf-8')
wF = open('tempJSON.txt', 'a+', encoding='utf-8')
content = f.read()
content = content.replace("None", "null")
content = content.replace("False", "false")
content = content.replace("True", "true")
# val can be " or ', depends on if " or ' is in inside
isState1 = False # " " is state 1
isState2 = False # ' ' is state 2

lastChar = ""
for char in content:
    if char == "'" and isState1 and lastChar != "\\":
        lastChar = char
        continue
    elif char == '"' and isState2 and lastChar != "\\":
        lastChar = char
        continue
    elif char == '"' and not isState1 and not isState2 and lastChar != "\\":
        isState1 = True
    elif char == '"' and isState1 and not isState2 and lastChar != "\\":
        isState1 = False
    elif char == "'" and not isState2 and not isState1 and lastChar != "\\":
        isState2 = True
    elif char == "'" and isState2 and not isState1 and lastChar != "\\":
        isState2 = False
    lastChar = char
    wF.write(char)
f.close()
wF.close()


f = open('tempJSON.txt', 'r', encoding='utf-8')
wF = open('repairedJSON.txt', 'a+', encoding='utf-8')
content = f.read()
content = content.replace("'", '"')
wF.write(content)
f.close()
wF.close()