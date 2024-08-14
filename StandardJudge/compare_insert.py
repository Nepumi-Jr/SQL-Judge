from dto import ResultDto
from time import time

show_log = False
def log(*content, **kwargs):
    if show_log:
        print(*content, **kwargs)

def compareType(sol:str, user:str):
    groupTypes = [ # for mysql
        ("integer", ["BIT", "TINYINT", "SMALLINT", "MEDIUMINT", "INT", "INTEGER", "BIGINT"]),
        ("real", ["FLOAT", "DOUBLE", "DECIMAL", "DOUBLE PRECISION"]),
        ("string", ["CHAR", "VARCHAR", "TINYTEXT", "TEXT", "MEDIUMTEXT", "LONGTEXT"]),
        ("binary", ["BINARY", "VARBINARY", "TINYBLOB", "BLOB", "MEDIUMBLOB", "LONGBLOB"]),
        ("date", ["DATE", "TIME", "YEAR", "DATETIME", "TIMESTAMP"]),
        ("enum", ["ENUM", "SET"])
    ]

    if "(" in sol:
        sol = sol.split("(")[0].strip()
    
    if "(" in user:
        user = user.split("(")[0].strip()
    
    for groupType in groupTypes:
        if sol.upper() in groupType[1] and user.upper() in groupType[1]:
            return True
    return False


def compare(cursor, solution_sql:str, user_sql:str, solution_db:str, user_db:str, is_log:bool) -> ResultDto:
    # insert just insert for each sql and database
    # them compare the result
    #! note that foreign key can't detected yet...

    #DON'T TOUCH THIS
    global show_log
    show_log = is_log

    operatorWords = ["CREATE", "TABLE", "IF", "NOT", "EXISTS"] # words that are not table name

    cursor.execute(f"USE {solution_db}")
    cursor.execute(solution_sql)
    for word in solution_sql.split():
        if word.upper() not in operatorWords:
            table_name = word
            break
    if table_name == "" or table_name == None:
        raise Exception("Table name is not found in solution")
    cursor.execute(f"DESCRIBE {table_name}")
    solution_result = cursor.fetchall()


    cursor.execute(f"USE {user_db}")
    
    start_time = time()
    try:
        cursor.execute(user_sql)
    except Exception as e:
        result = ResultDto("X", 0, 1, 0, str(e))
    
    try: #TODO : Is this necessary?
        cursor.execute(f"DESCRIBE {table_name}")
    except Exception as e:
        result = ResultDto("X", 0, 1, 0, str(e))
    user_result = cursor.fetchall()
    elapsed = time() - start_time

    if len(solution_result) != len(user_result):
        result = ResultDto("-", 0, 1, elapsed * 1000, "Different length of result")
    
    isPass = True
    sorted_solution_result = sorted(solution_result)
    sorted_user_result = sorted(user_result)
    for i, sol_table_result in enumerate(sorted_solution_result):
        user_table_result = sorted_user_result[i]
        
        # name
        if sol_table_result[0] != user_table_result[0]:
            isPass = False
            break
        
        # type
        if not compareType(sol_table_result[1], user_table_result[1]):
            isPass = False
            break

        # null
        if sol_table_result[2] != user_table_result[2]:
            isPass = False
            break

        # key
        if sol_table_result[3] != user_table_result[3]:
            isPass = False
            break

        # default
        if sol_table_result[4] == None or (sol_table_result[4] != None and sol_table_result[4] == user_table_result[4]):
            isPass = False
            break

        # extra
        if sol_table_result[5] == None or (sol_table_result[5] != None and sol_table_result[5] == user_table_result[5]):
            isPass = False
            break
    
    if isPass:
        result = ResultDto("P", 1, 1, elapsed * 1000, "Correct result")
    else:
        result = ResultDto("-", 0, 1, elapsed * 1000, "Wrong result")

    return result