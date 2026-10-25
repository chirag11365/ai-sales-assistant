import sqlite3, pandas as pd

con = sqlite3.connect("sales.db")

def q(title, sql):
    print("\n==", title)
    print(pd.read_sql(sql, con).to_string(index=False))

q("Profit by region", """
SELECT region, ROUND(SUM(profit),2) AS total_profit
FROM sales GROUP BY region ORDER BY total_profit""")

q("Loss-making sub-categories", """
SELECT sub_category, ROUND(SUM(profit),2) AS total_profit
FROM sales GROUP BY sub_category HAVING total_profit < 0""")

q("Top 5 states by sales", """
SELECT state, ROUND(SUM(sales),2) AS total_sales
FROM sales GROUP BY state ORDER BY total_sales DESC LIMIT 5""")

q("Monthly revenue (first 12 months)", """
SELECT substr(order_date,1,7) AS month, ROUND(SUM(sales),2) AS revenue
FROM sales GROUP BY month ORDER BY month LIMIT 12""")

q("Profit margin % by category", """
SELECT category, ROUND(SUM(profit)*100.0/SUM(sales),1) AS margin_pct
FROM sales GROUP BY category""")

q("Effect of discount on profit", """
SELECT discount, COUNT(*) AS orders, ROUND(AVG(profit),2) AS avg_profit
FROM sales GROUP BY discount ORDER BY discount""")

q("Avg discount and profit by sub-category", """
SELECT sub_category, ROUND(AVG(discount),2) AS avg_discount,
       ROUND(SUM(profit),2) AS total_profit
FROM sales GROUP BY sub_category ORDER BY total_profit""")

q("Tables: profit by discount level", """
SELECT discount, COUNT(*) AS orders, ROUND(SUM(profit),2) AS total_profit
FROM sales WHERE sub_category = 'Tables'
GROUP BY discount ORDER BY discount""")