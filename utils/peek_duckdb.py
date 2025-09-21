
import duckdb
conn = duckdb.connect('db/all_nbinfo_v3.db')
result = conn.execute("SELECT COUNT(*) FROM nbtypes").fetchone()
print(f"Total rows: {result[0]}")
conn.close()