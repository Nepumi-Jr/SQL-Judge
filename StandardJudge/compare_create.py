from dto import ResultDto
from time import time
import file_logger


def log(*content, **kwargs):
    file_logger.log("CREATE", *content, **kwargs)

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


def is_empty(val):
    if val is None:
        return True
    if isinstance(val, str):
        return val.strip() == ""
    if isinstance(val, (list, dict, set, tuple)):
        return len(val) == 0
    return False


def compare(cursor, solution_sql:str, user_sql:str, solution_db:str, user_db:str, solution_tag: SqlSolutionTagDto) -> ResultDto:
    # insert just insert for each sql and database
    # them compare the result
    #! note that foreign key can't detected yet...

    log("DB??", solution_db, user_db)
    log("S>>", solution_sql)
    log("U>>", user_sql)

    operatorWords = ["CREATE", "TABLE", "IF", "NOT", "EXISTS", "VIEW"] # words that are not table name

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
        return ResultDto("X", 0, 1, 0, str(e))
    
    try: #TODO : Is this necessary?
        cursor.execute(f"DESCRIBE {table_name}")
    except Exception as e:
        return ResultDto("X", 0, 1, 0, str(e))
    user_result = cursor.fetchall()
    elapsed = time() - start_time

    # log("TABLE NAME", table_name)
    # log("solution_result", solution_result)
    # log("user_result", user_result)
    # log()

    if len(solution_result) != len(user_result):
        return ResultDto("-", 0, 1, elapsed * 1000, "Different length of result")

    isPass = True
    warning_msgs = []
    sorted_solution_result = sorted(solution_result)
    sorted_user_result = sorted(user_result)
    for i, sol_table_result in enumerate(sorted_solution_result):
        user_table_result = sorted_user_result[i]

        log("Index ", i)
        log("?? : info    ", "(name, type, null, key, default, extra)")
        log("?? : Solution", sol_table_result)
        log("?? : User    ", user_table_result)
        
        # name
        if sol_table_result[0] != user_table_result[0]:
            isPass = False
            log("Fail name")
            break
        
        # type
        if not compareType(sol_table_result[1], user_table_result[1]):
            isPass = False
            log("Fail type", sol_table_result[1], user_table_result[1])
            break

        # null
        if sol_table_result[2] != user_table_result[2]:
            # isPass = False
            # log("Fail null")
            warning_msgs.append(f"Nullable value is different for {sol_table_result[0]}")
            break

        # key
        if sol_table_result[3] != user_table_result[3]:
            # isPass = False
            # log("Fail key", sol_table_result[3], user_table_result[3])
            warning_msgs.append(f"Key value is different for {sol_table_result[0]}")
            break

        # default
        if not is_empty(sol_table_result[4]) and sol_table_result[4] != user_table_result[4]:
            # isPass = False
            # log("Fail default")
            warning_msgs.append(f"Default assign value is different for {sol_table_result[0]}")
            break

        # extra
        if not is_empty(sol_table_result[5]) and sol_table_result[5] != user_table_result[5]:
            # isPass = False
            # log("Fail extra")
            warning_msgs.append(f"Extra attribute value is different for {sol_table_result[0]}")
            break
    
    if isPass:
        if len(warning_msgs) > 0:
            result = ResultDto("%", 1, 1, elapsed * 1000, "Correct with warning...\n" + "\n".join(warning_msgs))
        else:
            result = ResultDto("P", 1, 1, elapsed * 1000, "Correct result")
    else:
        result = ResultDto("-", 0, 1, elapsed * 1000, "Wrong result")

    return result