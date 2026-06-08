import sys
import pandas as pd

print("arguments", sys.argv)

df = pd.DataFrame({"A": [1, 2, 3], "c": [4, 5, 6]})
print(df)

day = int(sys.argv[1])
print(f"Running pipeline for day {day}")

df.to_parquet(f"output_day_{sys.argv[1]}.parquet")
