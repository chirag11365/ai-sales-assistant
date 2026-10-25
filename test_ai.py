from ai_sql import question_to_sql, is_safe, run_query

sql = question_to_sql("Which region has the lowest profit?")
print(sql)
print("Safe:", is_safe(sql))
print(run_query(sql))