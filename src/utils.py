import json
from urllib.parse import unquote_plus
from config import *
#from .validation import *
import re
import gzip
import os

#return true and keyword found else return false and "Manual intervention" 
def distance(keylist,line,position):
    print(keylist)
    for item in keylist:
        #index = line.casefold().find(item)
        index = re.finditer(item,line.casefold())
        print(item,index)
        
        for i in index:
            if position-i.span()[1] < spanning_distance and position-i.span()[1] >= 0:
                print(item)
                print("spanning_distance")
                print(position-i.span()[1] < spanning_distance)
                # for checking if the spanning distance is less
                if not ((line.casefold()[i.span()[1]].isalnum()) or line.casefold()[i.span()[1]] == '_'):
                    # print(line.casefold()[i.span()[1]]) if the next character to keyword is some alphanum
                    if i.span()[0]>0:
                        if not (line.casefold()[i.span()[0]-1].isalnum() or line.casefold()[i.span()[0]-1] == '_'):
                            # print(line.casefold()[i.span()[0]-1]) if the previous character is some alphanum
                            # print(item)
                            return True, item
                    else:
                        return True, item
    return False, "Manual Intervention required"



def eliminate(line,list_substr):
    for substr in list_substr:
        line = line.replace(substr[0],substr[1])
    return line
    