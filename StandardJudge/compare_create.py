from dto import ResultDto, SqlSolutionTagDto
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
    is_solution_error = False
    if solution_tag.is_ignore_error:
        try:
            cursor.execute(solution_sql)
        except:
            is_solution_error = True
            pass
    else:
        cursor.execute(solution_sql)
    
    if not is_solution_error:
        for word in solution_sql.split():
            if word.upper() not in operatorWords:
                table_name = word
                break
        if table_name == "" or table_name == None:
            raise Exception("Table name is not found in solution")
        cursor.execute(f"DESCRIBE {table_name}")
        solution_result = cursor.fetchall()
    else:
        table_name = "YAHALLOOOOO"


    cursor.execute(f"USE {user_db}")
    
    start_time = time()
    try:
        cursor.execute(user_sql)
    except Exception as e:
        if solution_tag.is_ignore_error and is_solution_error:
            return ResultDto("P", 1, 1, 0, "Correct with ignore Error")
        else:
            return ResultDto("X", 0, 1, 0, str(e))
    
    if solution_tag.is_ignore_error and is_solution_error:
        return ResultDto("-", 0, 1, 0, "This is not an error")
    
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


    isPass = True
    warning_msgs = []
    
    solution_table_dict_data = {}
    

    for sol_table_result in solution_result:
        solution_table_dict_data[sol_table_result[0]] = sol_table_result
    

    cur_score = 0
    max_score = 0
    penalty = 0

    for user_table_result in user_result:

        if user_table_result[0] not in solution_table_dict_data:
            penalty += 2 # for each column
            continue
        
        cur_score += 1
        max_score += 1

        sol_table_result = solution_table_dict_data[user_table_result[0]]
        
        # type
        if compareType(sol_table_result[1], user_table_result[1]):
            cur_score += 1
        max_score += 1

        # null
        if sol_table_result[2] != user_table_result[2]:
            pass

        # key
        if sol_table_result[3] != user_table_result[3]:
            pass

        # default
        if not is_empty(sol_table_result[4]) and sol_table_result[4] != user_table_result[4]:
            pass

        # extra
        if not is_empty(sol_table_result[5]) and sol_table_result[5] != user_table_result[5]:
            pass
    
    final_score = max(0, cur_score - penalty)
    if final_score == max_score:
        result = ResultDto("P", 1, 1, elapsed * 1000, "Correct result")
    elif final_score / max_score >= 0.5:
        result = ResultDto("%", final_score / max_score, 1, elapsed * 1000, f"Correct {cur_score} out of {max_score} (penalty: -{penalty})")
    else:
        result = ResultDto("-", 0, 1, elapsed * 1000, f"Rejected (Correct {cur_score} out of {max_score} penalty: -{penalty}")

    return result