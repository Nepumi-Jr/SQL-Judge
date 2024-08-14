import mysql.connector
import time
from random import randint
import sqlparse

from dto import ResultDto
from compare_create import compare as create_compare
from compare_select import compare as select_compare

show_log = False

def log(*content, **kwargs):
    if show_log:
        print(*content, **kwargs)

def generateResultReport(solution_sql_path:str, user_sql_path:str, result_path:str, this_show_log:bool = False):
    global show_log
    show_log = this_show_log
    mydb = mysql.connector.connect( #TODO : manage with config file
        host="localhost",
        user="root",
        password="0000"
    )
    my_cursor = mydb.cursor()
    results = []

    def read_sql_file(file_path):
        with open(file_path, 'r') as file:

            content = file.read()
            statements = [sqlparse.format(s, strip_comments = True, strip_whitespace = True) for s in sqlparse.split(content) if s.strip() != ""]
            statements = [s for s in statements if s.strip() != ""]

            # log("path", file_path)
            # for s in statements:
            #     log(">",s)

            return statements

    def create_random_db():
        while True:
            now_time_data = time.localtime()
            db_name = f"db{now_time_data.tm_year:04d}{now_time_data.tm_mon:02d}{now_time_data.tm_mday:02d}_{now_time_data.tm_hour:02d}{now_time_data.tm_min:02d}{now_time_data.tm_sec:02d}_{randint(0, 9999):04d}"
            
            # check if the database already exists
            my_cursor.execute("SHOW DATABASES")
            if db_name not in my_cursor:
                break
        my_cursor.execute(f"CREATE DATABASE {db_name};")
        return db_name

    solution_sql_s = read_sql_file(solution_sql_path)
    
    user_sql_s = read_sql_file(user_sql_path)

    solution_db = create_random_db()
    user_db = create_random_db()

    log("Total",len(solution_sql_s), "Commands")
    log("UTotal",len(user_sql_s), "Commands")

    for i, solution_sql in enumerate(solution_sql_s):
        if i >= len(user_sql_s):
            results.append("X;0;1;0;0;User didn't finish the task")
            continue

        solution_command = solution_sql.split()[0].upper().strip()
        user_command = user_sql_s[i].split()[0].upper().strip()
        log("cmd", solution_command, user_command)
        if solution_command != user_command:
            results.append("-;0;1;0;0;Different command")
            continue
        
        try:
            if solution_command == "SELECT":
                result = select_compare(my_cursor, solution_sql, user_sql_s[i], solution_db, user_db, show_log)
            elif solution_command == "CREATE":
                result = create_compare(my_cursor, solution_sql, user_sql_s[i], solution_db, user_db, show_log)
            else:   # didn't compare the result yet
                my_cursor.execute(f"USE {solution_db}")
                my_cursor.execute(solution_sql)
                
                my_cursor.execute(f"USE {user_db}")

                start_time = time.time()
                try:
                    my_cursor.execute(user_sql_s[i])
                except Exception as e:
                    result = ResultDto("X", 0, 1, 0, str(e))
                else:
                    elapsed = int((time.time() - start_time) * 1000)
                    result = ResultDto("P", 1, 1, elapsed, "Correct result")
        except Exception as e:
            results.append(f"!;0;1;0;0;{e}")
            break
        results.append(result.to_string_result())

    with open(result_path, 'w') as file:
        for line in results:
            file.write(line + '\n')

    my_cursor.execute(f"DROP DATABASE {solution_db}")
    my_cursor.execute(f"DROP DATABASE {user_db}")

if __name__ == "__main__":
    generateResultReport("testSolution.sql", "testUser.sql", "result.txt")
