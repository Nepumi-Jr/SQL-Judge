import mysql.connector
import time
from random import randint
import sqlparse
import configparser

from dto import ResultDto
from compare_create import compare as create_compare
from compare_select import compare as select_compare

show_log = False

def log(*content, **kwargs):
    if show_log:
        print(*content, **kwargs)

try:
    sql_config = configparser.ConfigParser()
    sql_config.read("sql_grader_config.ini")

    admin_config_connection = {
        "host": sql_config["connection"]["host"],
        "port": sql_config["connection"]["port"],
        "user": sql_config["superUser"]["user"],
        "password": sql_config["superUser"]["password"]
    }
    
    grader_config_connection = {
        "host": sql_config["connection"]["host"],
        "port": sql_config["connection"]["port"],
        "user": sql_config["graderUser"]["user"],
        "password": sql_config["graderUser"]["password"]
    }

except Exception as e:
    log("Can't read the config...\n", e)

    admin_config_connection = {
        "host": "localhost",
        "user" : "root",
        "password": "0000"
    }

    grader_config_connection = {
        "host": "localhost",
        "user" : "root",
        "password": "0000"
    }



def generateResultReport(prerequisite_sql_path:Union[str, None],solution_sql_path:str, user_sql_path:str, result_path:str, this_show_log:bool = False):
    global show_log
    show_log = this_show_log
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

    def create_random_db(adminCursor):
        while True:
            now_time_data = time.localtime()
            db_name = f"db{now_time_data.tm_year:04d}{now_time_data.tm_mon:02d}{now_time_data.tm_mday:02d}_{now_time_data.tm_hour:02d}{now_time_data.tm_min:02d}{now_time_data.tm_sec:02d}_{randint(0, 9999):04d}"
            
            # check if the database already exists
            adminCursor.execute("SHOW DATABASES")
            if db_name not in adminCursor:
                break
        adminCursor.execute(f"CREATE DATABASE {db_name};")
        return db_name

    solution_sql_s = read_sql_file(solution_sql_path)
    user_sql_s = read_sql_file(user_sql_path)

    with mysql.connector.connect(**admin_config_connection) as admin_connection:
        with admin_connection.cursor() as admin_cursor:
            solution_db = create_random_db(admin_cursor)
            user_db = create_random_db(admin_cursor)

    log("Total",len(solution_sql_s), "Commands")
    log("UTotal",len(user_sql_s), "Commands")

    with mysql.connector.connect(**grader_config_connection) as grader_connection:
        with grader_connection.cursor() as grader_cursor:

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
                            result = select_compare(grader_cursor, solution_sql, user_sql_s[i], solution_db, user_db, show_log)
                        elif solution_command == "CREATE":
                            result = create_compare(grader_cursor, solution_sql, user_sql_s[i], solution_db, user_db, show_log)
                        else:   # didn't compare the result yet
                            grader_cursor.execute(f"USE {solution_db}")
                            grader_cursor.execute(solution_sql)
                            
                            grader_cursor.execute(f"USE {user_db}")

                            start_time = time.time()
                            try:
                                grader_cursor.execute(user_sql_s[i])
                            except Exception as e:
                                result = ResultDto("X", 0, 1, 0, str(e))
                            else:
                                elapsed = int((time.time() - start_time) * 1000)
                                result = ResultDto("P", 1, 1, elapsed, "Correct result")
                    except Exception as e:
                        results.append(f"!;0;1;0;0;{e}")
                        break
                    results.append(result.to_string_result())

    log("Results", results)
    for case, result  in enumerate(results):
        with open(f"{result_path}_{case}", 'w') as file:
                file.write(result)
            
    log("Drop DB...")
    with mysql.connector.connect(**admin_config_connection) as admin_connection:
        with admin_connection.cursor() as admin_cursor:
            admin_cursor.execute(f"DROP DATABASE {solution_db}")
            admin_cursor.execute(f"DROP DATABASE {user_db}")

    log("Done")


if __name__ == "__main__":
    generateResultReport(None, "testSolution.sql", "testUser.sql", "result.txt")
