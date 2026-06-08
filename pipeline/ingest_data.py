#!/usr/bin/env python
# coding: utf-8

# In[2]:


import pandas as pd
import pyarrow.parquet as pq
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
@click.option('--batch-size', default=10000, type=int, help='Rows to ingest per batch')
def run(pg_user, pg_pass, pg_host, pg_port, pg_db, target_table, batch_size):

    year = 2026
    month = 4
    url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{year}-{month:02d}.parquet"

    parquet_file = "yellow_tripdata_2026-04.parquet"
    # parquet_file = url

    engine = create_engine(f'postgresql+psycopg://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}')
    reader = pq.ParquetFile(parquet_file)
    batches = reader.iter_batches(batch_size=batch_size)
    first_batch = next(batches, None)

    if first_batch is None:
        print("No rows found in parquet file")
        return

    first_batch_df = first_batch.to_pandas()

    print(pd.io.sql.get_schema(first_batch_df, name=f'{target_table}', con=engine))

    first_batch_df.head(0).to_sql(
        name=f'{target_table}',
        con=engine,
        if_exists="replace",
        index=False
    )

    print("Table created")

    total_rows = len(first_batch_df)

    first_batch_df.to_sql(
        name=f'{target_table}',
        con=engine,
        if_exists="append",
        index=False
    )

    for batch in tqdm(batches, desc="Ingesting batches"):
        batch_df = batch.to_pandas()
        batch_df.to_sql(
            name=f'{target_table}',
            con=engine,
            if_exists="append",
            index=False
        )
        total_rows += len(batch_df)

    print("Inserted:", total_rows)


if __name__ == "__main__":
    run()
