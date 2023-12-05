import re
from luhn import *
import json
from utils import *
from config import *
card_patterns = [ r'^3[47]'
                , r'^30[0-5]'
                , r'^3([689]|09)'
                , r'^35(2[89]|[3-8][0-9])'
                , r'^(6304|670[69]|6771)'
                , r'^(4026|417500|4508|4844|491(3|7))'
                , r'^4'
                , r'^5[1-5]'
                , r'^(5018|5081|5044|5020|5038|603845|6304|6759|676[1-3]|6220|504834|504817|504645)\d*'
                ]
                
# TESTED
def check_card(line,command):
    card_nos = re.finditer("\d{12,19}", line)
    found = False
    spanner = None
    value = ""
    i = 0
    matched_pattern = ""
    for card in card_nos:
        print(card)
        if verify(card.group()):
            for pattern in card_patterns:
                x = re.match(pattern,card.group())
                if x:
                    matched_pattern = pattern
                    spanner = card
                    print(spanner.span())
                    print(line[spanner.span()[1]-1])
                    found = True
                    # if len(line) <= spanner.span()[1] or not line[spanner.span()[1]].isalnum():
                    #     found = True
                    #     if line[spanner.span()[0]-1].isalnum():
                    #         if line[spanner.span()[0]-1] not in ('n','t'):
                    #             found = False
                    #         else:
                    #             break
                    #     else:
                    #         break
    print(found)
    if found:
        line = line.replace(spanner.group(),"###")
    return "CARD", value, line, matched_pattern
    # if found:
    #     accurate, value = distance(possible_key_dict["card"],line,spanner.span()[0])
    #     print(value)
    #     if accurate:
    #         # falsePositive, value = falseKeyDistance(inverse_key_dict["card"],line,spanner.span()[0])
    #         # if falsePositive:
    #             # return "", "", line, ""
    #         if command == "mask":
    #             # print("masked: "+line)
    #             line = line.replace(spanner.group(),"###")
    #         return "CARD", value, line, matched_pattern
    #     else:
    #         return "", "", line, ""
    # else:
    #     return "", "",line, ""


def check_custom(regex,tag,key_value_list,inverse_key_value_list,line,command):
    finding = re.finditer(regex,line)
    i = 0
    value = ""
    if finding:
        for item in finding:
            position = item.span()[0]
            accurate, value = distance(key_value_list,line,position)
            if accurate:
                i+=1
                # falsePositive, value = falseKeyDistance(inverse_key_value_list,line,position)
                # if falsePositive:
                #     return "", "", line, ""
                if command == "mask":
                    # print("masked: "+line)
                    line = line.replace(item.group(),"###")
                break
        if i>0:
            return tag,value,line, ""
        else:
            return "","",line, ""
    else:
        return "","",line, ""

def check_anomaly(line,command,tags):
    #checking for card
    ans = []
    for tag in tags:
        if tag["tag"] == CARD:
            # print("card")
            result, keyTag, line, pattern = check_card(line,command)
            if result != "":
                ans.append((result,keyTag,pattern))
        else:
            # print(tag["tag"])
            result, keyTag, line, pattern = check_custom(tag["regex"],tag["tag"],tag["key_value_list"],tag["inverse_key_list"],line,command)
            if result != "":
                ans.append((result,keyTag,pattern))
    return ans,line

def mask_data(line,command):
    line = eliminate(line,elimination_chars)
    result,maskedLine = check_anomaly(line,command,tags)
    return result,maskedLine