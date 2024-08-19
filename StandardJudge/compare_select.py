from dto import ResultDto
from time import time

show_log = False
def log(*content, **kwargs):
    if show_log:
        print(*content, **kwargs)

def compare(cursor, solution_sql:str, user_sql:str, solution_db:str, user_db:str, is_log:bool) -> ResultDto:
    # Selection will select the result from the user's database
    # first execute the solution sql in the user database
    # then execute the user sql in the user database
    # compare the result

    #DON'T TOUCH THIS
    global show_log

    #test solution sql
    cursor.execute(f"USE {solution_db}")
    cursor.execute(solution_sql)
    _ = cursor.fetchall()

    #test user sql
    try:
        cursor.execute(f"USE {user_db}")
        cursor.execute(solution_sql)
        solution_result = cursor.fetchall()
    except Exception as e:
        return ResultDto("X", 0, 1, 0, str(e))

    cursor.execute(f"USE {user_db}")
    
    start_time = time()
    try:
        cursor.execute(user_sql)
    except Exception as e:
        result = ResultDto("X", 0, 1, 0, str(e))
    user_result = cursor.fetchall()
    elapsed = time() - start_time

    
    if solution_result == user_result:
        result = ResultDto("P", 1, 1, elapsed * 1000, "Correct result")
    else:
        result = ResultDto("-", 0, 1, elapsed * 1000, "Wrong result")

    return result