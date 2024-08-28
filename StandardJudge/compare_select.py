from dto import ResultDto, SqlSolutionTagDto
from time import time


def compare(cursor, solution_sql:str, user_sql:str, solution_db:str, user_db:str, solution_tag: SqlSolutionTagDto) -> ResultDto:
    # Selection will select the result from the user's database
    # first execute the solution sql in the user database
    # then execute the user sql in the user database
    # compare the result

    is_solution_error = False

    #test solution sql
    cursor.execute(f"USE {solution_db}")
    if solution_tag.is_ignore_error:
        try:
            cursor.execute(solution_sql)
            cursor.fetchall()
        except:
            is_solution_error = True
            pass
    else:
        cursor.execute(solution_sql)
        cursor.fetchall()

    #test user sql
    try:
        cursor.execute(f"USE {user_db}")
        cursor.execute(solution_sql)
        solution_result = cursor.fetchall()
    except Exception as e:
        if solution_tag.is_ignore_error:
            is_solution_error = is_solution_error and True
        else:
            return ResultDto("X", 0, 1, 0, str(e))

    cursor.execute(f"USE {user_db}")
    
    start_time = time()
    try:
        cursor.execute(user_sql)
    except Exception as e:
        if solution_tag.is_ignore_error and is_solution_error:
            return ResultDto("P", 1, 1, 0, "Correct with ignore Error")
        return ResultDto("X", 0, 1, 0, str(e))
    user_result = cursor.fetchall()
    elapsed = time() - start_time

    if solution_tag.is_ignore_error and is_solution_error:
        return ResultDto("-", 0, 1, elapsed * 1000, "This is not an error")
    
    # starting to compare the result
    cur_score, max_score = 0, 0
    penalty = 0
    for i, v in enumerate(solution_result):
        if i >= len(user_result):
            max_score += len(v)
            break
        
        for j, vv in enumerate(v):
            if j >= len(user_result[i]):
                max_score += len(v) - j
                break

            if vv == user_result[i][j]:
                cur_score += 1
            max_score += 1

        penalty += len(user_result[i]) - len(v)
    
    if len(user_result) > len(solution_result):
        for i in range(len(solution_result), len(user_result)):
            penalty += len(user_result[i])
    
    final_score = max(0 , cur_score - penalty)


    if final_score == max_score:
        result = ResultDto("P", 1, 1, elapsed * 1000, "Correct result")
    elif final_score / max_score >= 0.5:
        result = ResultDto("H", final_score / max_score, 1, elapsed * 1000, f"Correct {cur_score} out of {max_score} (penalty: -{penalty})")
    else:
        result = ResultDto("-", 0, 1, elapsed * 1000, f"Wrong result (Correct {cur_score} out of {max_score} penalty: -{penalty}")

    return result