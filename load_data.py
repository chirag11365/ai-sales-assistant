import pandas as pd, sqlite3

df = pd.read_csv("superstore.csv", encoding="latin-1")
df.columns = df.columns.str.lower().str.replace(r"[ -]", "_", regex=True)
df["order_date"] = pd.to_datetime(df["order_date"]).dt.strftime("%Y-%m-%d")
df = df.drop_duplicates()

con = sqlite3.connect("sales.db")
df.to_sql("sales", con, if_exists="replace", index=False)
print(df.shape, df.isna().sum().sum(), "missing values")