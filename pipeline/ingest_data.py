#!/usr/bin/env python
# coding: utf-8

# In[2]:


import pandas as pd
from sqlalchemy import create_engine
from tqdm.auto import tqdm
import click

@click.command()
@click.option('--pg-user', default='root', help='PostgreSQL user')
@click.option('--pg-pass', default='root', help='PostgreSQL password')
@click.option('--pg-host', default='localhost', help='PostgreSQL host')
@click.option('--pg-port', default=5432, type=int, help='PostgreSQL port')
@click.option('--pg-db', default='ny_taxi', help='PostgreSQL database name')
@click.option('--target-table', default='yellow_taxi_data', help='Target table name')
def run(pg_user, pg_pass, pg_host, pg_port, pg_db, target_table):

    year = 2026
    month = 4
    url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{year}-{month:02d}.parquet"

    #df = pd.read_parquet(url)
    df = pd.read_parquet("yellow_tripdata_2026-04.parquet")

    engine = create_engine(f'postgresql+psycopg://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}')

    print(pd.io.sql.get_schema(df, name=f'{target_table}', con=engine))

    df.head(0).to_sql(
        name=f'{target_table}',
        con=engine,
        if_exists="replace",
        index=False
    )

    print("Table created")

    df.head(1000).to_sql(
        name=f'{target_table}',
        con=engine,
        if_exists="append",
        index=False
    )

    print("Inserted:", len(df))


if __name__ == "__main__":
    run()

