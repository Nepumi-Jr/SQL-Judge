"""
    Input by 9 or more argument
    1 : test case (start from 1)
    2 : timeLimit in ms
    3 : memoryLimit in mb
    4 : PROBLEM_DIR
    5 : source path
    6 : cmp cmd
    7 : cmp args
    8 : run cmd
    9 : run args

    output will return by stdout in formatting below
    {verdict};{score};{maxscore};{elapsed};{memory};{comment}
"""
from os import path, remove
import sys

import SQLExecute

judgeArgs = sys.argv[-1]

if not path.exists(judgeArgs):
    print(f"!;0;1;0;0;Judge args not found :(",end = "")
    exit(0)

try:
    with open(judgeArgs,"r") as f:
        judgeArgs = f.read().split("\n")

except:
    print(f"!;0;1;0;0;Can't read Judge args:(",end = "")
    exit(0)

if(len(judgeArgs) < 9):
    print(f"!;0;1;0;0;Not Enough info to judge\nexpected 9 args got {len(judgeArgs)} args",end = "")
    exit(0)

try:

    testCase = int(judgeArgs[0]) or ""
    timeLimit = int(judgeArgs[1] or "")#In ms
    memoryLimit = int(judgeArgs[2] or "")#mb
    PROBLEM_DIR = judgeArgs[3] or ""
except:
    print(f"!;0;1;0;0;Can't convert data :(",end = "")
    exit(0)

if(len(judgeArgs) < 6):
    print(f"!;0;1;0;0;Program not Found",end = "")
    exit(0)


srcPath = judgeArgs[4] or ""
prerequisitePath = None
if path.exists(path.join(PROBLEM_DIR,"prerequisite.sql")):
    prerequisitePath = path.join(PROBLEM_DIR,"prerequisite.sql")
solPath = path.join(PROBLEM_DIR,"solution.sql")
resultPath = path.join(PROBLEM_DIR,"result")



#This is from Kiyago's standard judge
def main():

    if testCase == 1:
        try:
            SQLExecute.generateResultReport(prerequisitePath,solPath,srcPath, resultPath)
        except Exception as e:
            print(f"!;0;1;0;0;{e}",end = "")
            exit(1)
    
    curResultPath = f"{resultPath}_{testCase-1}"

    if not path.exists(curResultPath):
        if testCase == 1:
            exit(1)
        else:
            print("E;0;0;0;0;End of Test",end = "")
        return

    with open(curResultPath,"r") as f:
        result = f.read().strip()
        
    print(result,end = "")
    if result[0] == "!":
        exit(1)
    try:
        remove(curResultPath)
    except:
        pass

main()
