"""Build superstore.db (SQLite) from the Excel workbook.  Usage: python build_db.py [path/to/file.xlsx]"""
import sys, sqlite3, pandas as pd
src = sys.argv[1] if len(sys.argv) > 1 else "Global_Superstore_-_Tables.xlsx"
x = pd.ExcelFile(src)
f, c, p, l, r = (x.parse(s) for s in ["Fact", "Customer", "Product", "Location", "Returns"])
d = (f.merge(c, on="Customer ID").merge(p, on="Product ID").merge(l, on="Location ID"))
d["returned"] = d["Order ID"].isin(set(r["Order ID"])).astype(int)
d["order_date"] = d["Order Date"].dt.strftime("%Y-%m-%d")
d["year"] = d["Order Date"].dt.year
d["ym"] = d["Order Date"].dt.strftime("%Y-%m")
out = d.rename(columns={"Order ID": "order_id", "Customer ID": "customer_id", "Customer Name": "customer_name",
    "Segment": "segment", "Product ID": "product_id", "Product Name": "product_name", "Category": "category",
    "Sub-Category": "sub_category", "Market": "market", "Region": "region", "Country": "country",
    "Sales": "sales", "Quantity": "quantity", "Profit": "profit", "Order Priority": "priority", "Ship Mode": "ship_mode"})
cols = ["order_id", "order_date", "year", "ym", "customer_id", "customer_name", "segment", "product_id", "product_name",
        "category", "sub_category", "market", "region", "country", "sales", "quantity", "profit", "returned"]
con = sqlite3.connect("superstore.db")
out[cols].to_sql("sales", con, if_exists="replace", index=False)
for col in ["order_date", "year", "customer_id", "product_id", "market", "category", "segment"]:
    con.execute(f"CREATE INDEX IF NOT EXISTS ix_{col} ON sales({col})")
con.commit(); print("rows:", con.execute("select count(*) from sales").fetchone()[0])
