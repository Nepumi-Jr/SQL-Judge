from typing import Union
import mysql.connector
import time
from random import randint
import sqlparse
import configparser
import re


from file_logger import log
from dto import ResultDto, SqlSolutionTagDto
from compare_create import compare as create_compare
from compare_select import compare as select_compare


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
    log("Config","Can't read the config...\n", e)

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



def generateResultReport(prerequisite_sql_path:Union[str, None],solution_sql_path:str, user_sql_path:str, result_path:str):
    results = []

    def get_sql_solution_tag(sql_statement, sql_statement_with_comment:str) -> SqlSolutionTagDto:
        is_no_score = False
        is_ignore_error = False

        if "@no_score" in sql_statement_with_comment and "@no_score" not in sql_statement:
            is_no_score = True

        if "@ignore_error" in sql_statement_with_comment and "@ignore_error" not in sql_statement:
            is_ignore_error = True
        
        return SqlSolutionTagDto(is_no_score, is_ignore_error)

    def read_sql_file(file_path) -> tuple[list[str], list[SqlSolutionTagDto]]:
        with open(file_path, 'r') as file:

            content = file.read()
            statements = [sqlparse.format(s, strip_comments = True, strip_whitespace = True).strip() for s in sqlparse.split(content) if s.strip() != "" and sqlparse.format(s, strip_comments = True, strip_whitespace = True).strip() != ""]
            statements_with_comment = [s.strip() for s in sqlparse.split(content) if s.strip() != "" and sqlparse.format(s, strip_comments = True, strip_whitespace = True).strip() != ""]
            
            try:
                with open("sql_grader_ignore_list.txt", 'r') as ignore_file:
                    ignore_list_raw = ignore_file.read().split("\n")
            except:
                ignore_list_raw = []
            
            # reading ignore_list
            ignore_list = []
            for s in ignore_list_raw:
                txt = s.strip()
                if "--" in txt:
                    txt = txt.split("--")[0].strip()
                
                if txt != "":
                    ignore_list.append(txt)
            
            # filtering the statements
            log("User SQL", file_path)
            filtered_statements = []
            problem_sql_tags = []
            for s, sc in zip(statements, statements_with_comment):
                is_ignore = False
                for ignore in ignore_list:
                    if re.search(ignore.replace("%", ".*"), s, re.IGNORECASE):
                        is_ignore = True
                        break
                if not is_ignore:
                    
                    filtered_statements.append(s)
                    problem_sql_tags.append(get_sql_solution_tag(s, sc))
                    log(None, s)
                    log(None, get_sql_solution_tag(s, sc))

            return filtered_statements, problem_sql_tags

    def create_random_db(adminCursor):
        while True:
            now_time_data = time.localtime()
            db_name = f"db{now_time_data.tm_year:04d}{now_time_data.tm_mon:02d}{now_time_data.tm_mday:02d}_{now_time_data.tm_hour:02d}{now_time_data.tm_min:02d}{now_time_data.tm_sec:02d}_{randint(0, 9999):04d}"
            
            # check if the database already exists
            adminCursor.execute("SHOW DATABASES")
            dbs = list(map(lambda x: x[0], adminCursor.fetchall()))
            if db_name not in dbs:
                break
        adminCursor.execute(f"CREATE DATABASE {db_name};")
        return db_name

    def drop_db(adminCursor, db_name):
        try_drop = 0
        while try_drop < 10:
            adminCursor.execute("SHOW DATABASES")
            log("Drop DB", db_name, adminCursor)
            dbs = list(map(lambda x: x[0], adminCursor.fetchall()))
            if db_name in dbs:
                adminCursor.execute(f"DROP DATABASE {db_name}")
            else:
                break
            try_drop += 1


    prerequisite_sql_s =  read_sql_file(prerequisite_sql_path)[0] if prerequisite_sql_path != None else []
    solution_sql_s, problem_sql_tags = read_sql_file(solution_sql_path)
    user_sql_s = read_sql_file(user_sql_path)[0]


    with mysql.connector.connect(**admin_config_connection) as admin_connection:
        with admin_connection.cursor() as admin_cursor:
            solution_db = create_random_db(admin_cursor)
            user_db = create_random_db(admin_cursor)

    with mysql.connector.connect(**grader_config_connection) as grader_connection:
        with grader_connection.cursor() as grader_cursor:
            
            is_prepared = True
            for i, sql in enumerate(prerequisite_sql_s):
                log("Execute","Prepare", sql)
                try:
                    grader_cursor.execute(f"USE {solution_db}")
                    grader_cursor.execute(sql)
                    grader_cursor.execute(f"USE {user_db}")
                    grader_cursor.execute(sql)
                except Exception as pre_e:
                    is_prepared = False
                    log("Execute","ded ", pre_e)
                    results.append(f"!;0;1;0;0;{pre_e}")
                    break
            
            log("Execute","is prepared", is_prepared)

            if is_prepared:

                for i, solution_sql in enumerate(solution_sql_s):
                    is_no_score = problem_sql_tags[i].is_no_score
                    is_ignore_error = problem_sql_tags[i].is_ignore_error

                    def append_result(result:str):
                        if not is_no_score:
                            results.append(result)

                    if i >= len(user_sql_s):
                        append_result("X;0;1;0;0;User didn't finish the task")
                        continue
                    
                    alphaNumPattern = re.compile(r"[\W_]+")

                    solution_command = alphaNumPattern.sub("", solution_sql.split()[0].upper())
                    user_command =  alphaNumPattern.sub("", user_sql_s[i].split()[0].upper()) 
                    log("Execute","cmd", solution_command, user_command)
                    if solution_command != user_command:
                        append_result("-;0;1;0;0;Different command")
                        continue
                    
                    try:
                        if solution_command == "SELECT":
                            result = select_compare(grader_cursor, solution_sql, user_sql_s[i], solution_db, user_db, problem_sql_tags[i])
                        elif solution_command == "CREATE":
                            result = create_compare(grader_cursor, solution_sql, user_sql_s[i], solution_db, user_db, problem_sql_tags[i])
                        else:   # didn't compare the result yet

                            is_solution_error = False

                            grader_cursor.execute(f"USE {solution_db}")
                            if is_ignore_error:
                                try:
                                    grader_cursor.execute(solution_sql)
                                except:
                                    is_solution_error = True
                                    pass
                            else:
                                grader_cursor.execute(solution_sql)
                            

                            grader_cursor.execute(f"USE {user_db}")
                            start_time = time.time()
                            try:
                                grader_cursor.execute(user_sql_s[i])
                            except:
                                if is_ignore_error and is_solution_error:
                                    result = ResultDto("P", 1, 1, 0, "Correct with ignore Error")
                                else:
                                    result = ResultDto("X", 0, 1, 0, str(e))
                            else:
                                elapsed = int((time.time() - start_time) * 1000)

                                if is_ignore_error and is_solution_error:
                                    result = ResultDto("-", 0, 1, elapsed, "This is not an error")
                                else:
                                    result = ResultDto("P", 1, 1, elapsed, "Correct result")
                    except Exception as e:
                        append_result(f"!;0;1;0;0;{e}")
                        break
                    append_result(result.to_string_result())

    log("Execute","Results", results)
    for case, result  in enumerate(results):
        with open(f"{result_path}_{case}", 'w') as file:
                file.write(result)
            
    log("Execute","Drop DB...")
    with mysql.connector.connect(**admin_config_connection) as admin_connection:
        with admin_connection.cursor() as admin_cursor:
            drop_db(admin_cursor, solution_db)
            drop_db(admin_cursor, user_db)

    log("Execute","Done")


if __name__ == "__main__":
    generateResultReport(None, "testSolution.sql", "testUser.sql", "result.txt")
