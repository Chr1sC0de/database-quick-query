import os
from datetime import datetime

import polars as pl
import pyarrow as pa
from databricks import sql as databricks_sql
from triple_quote_clean import TripleQuoteCleaner

from ..utils import get_connector_details
from ._base import Base

tqc = TripleQuoteCleaner(skip_top_lines=1)


GENERIC_TYPE_MAP = {
    "BIGINT": "NUMERIC",
    "BINARY": "NUMERIC",
    "TINYINT": "NUMERIC",
    "DECIMAL": "NUMERIC",
    "DOUBLE": "NUMERIC",
    "FLOAT": "NUMERIC",
    "INT": "NUMERIC",
    "SMALLINT": "NUMERIC",
    "STRING": "CHARACTER",
    "BOOLEAN": "BOOLEAN",
    "DATE": "DATE/TIME",
    "INTERVAL": "DATE/TIME",
    "TIMESTAMP": "DATE/TIME",
    "VOID": "VOID",
    "ARRAY": "COMPLEX",
    "MAP": "COMPLEX",
    "STRUCT": "COMPLEX",
}


def generic_type_mapper(type):
    type = type.upper()
    if type in GENERIC_TYPE_MAP:
        return GENERIC_TYPE_MAP[type]
    else:
        for t in GENERIC_TYPE_MAP.keys():
            if t in type:
                return t
        return "UNIDENTIFIED"


class _DatabricksBase(Base):
    def __new__(cls, *args, **kwargs):
        if "DATABRICKS_RUNTIME_VERSION" in os.environ.keys():
            conn = super().__new__(Cluster, *args, **kwargs)
            conn.__init__()
            return conn

        return super().__new__(cls, *args, **kwargs)

    def __init__(self, hostname: str, http_path: str, access_token: str):
        self.connection_kwargs = dict(
            server_hostname=hostname,
            http_path=http_path,
            access_token=access_token,
        )

    def __call__(self, query: str, scan_parquet_kwargs=None) -> pl.LazyFrame:
        """
        scan_parquet_kwargs are arguments which will be passed to
        https://pola-rs.github.io/polars/py-polars/html/reference/api/polars.scan_parquet.html#polars-scan-parquet
        """
        return super().__call__(query, scan_parquet_kwargs=scan_parquet_kwargs)

    def _run_query(self, query, *args, **kwargs) -> pl.LazyFrame:
        self.connection = databricks_sql.connect(**self.connection_kwargs)
        self.cursor = self.connection.cursor()
        self.cursor.execute(query)
        results = pl.from_arrow(self.cursor.fetchall_arrow()).lazy()
        self.cursor.close()
        self.connection.close()
        return results

    def close(self):
        ...

    def describe_columns(self, table_name: str) -> pl.LazyFrame:
        query = f"describe {table_name}"

        description: pl.LazyFrame = self(query)

        self.description_query = (
            query
            + "\n-- the result of this query is post-processed with polars"
        )

        description = (
            description.filter(
                pl.col("col_name").str.contains(r"^\#").is_not()
            )
            .unique()
            .rename({c: c.upper() for c in description.columns})
            .with_columns(pl.lit(None).alias("DATA_LENGTH"))
            .with_columns(
                pl.col("DATA_TYPE")
                .str.extract(r"[(](\d+),(\d+)[)]", 1)
                .cast(pl.Int32)
                .alias("DATA_PRECISION")
            )
            .with_columns(
                pl.col("DATA_TYPE")
                .str.extract(r"[(](\d+),(\d+)[)]", 2)
                .cast(pl.Int32)
                .alias("DATA_SCALE")
            )
            .with_columns(pl.col("DATA_TYPE").str.extract(r"\w+", 0))
            .with_columns(
                pl.col("DATA_TYPE")
                .apply(generic_type_mapper)
                .alias("GENERIC_TYPE")
            )
            .with_columns(pl.col("DATA_TYPE").str.to_uppercase())
            .select(
                [
                    "COL_NAME",
                    "DATA_TYPE",
                    "DATA_LENGTH",
                    "DATA_PRECISION",
                    "DATA_SCALE",
                    "GENERIC_TYPE",
                ]
            )
        )
        description = description.select(
            [pl.col(c) for c in description.columns if c != "COMMENT"]
        )

        return description


class _general_connector(_DatabricksBase):
    targets = ["server_hostname", "http_path", "access_token"]
    source: str

    def __init__(self):
        configs = get_connector_details()
        databricks_configs = configs["databricks"]
        connector_config = databricks_configs[self.source]
        args = [connector_config[key] for key in self.targets]
        super().__init__(*args)


class Cluster(_DatabricksBase):
    def __init__(self, *args, **kwargs):
        try:
            from pyspark.sql import SparkSession  # type: ignore

            self.spark = SparkSession.builder.getOrCreate()
        except ImportError:
            self.spark = None

    def _load_from_cache(*args, **kwargs) -> pl.LazyFrame:
        return

    def cache(self, *args, **kwargs):
        return self

    def _cache_df(self):
        return

    def __call__(self, query: str, *args, **kwargs) -> pl.LazyFrame:
        self.query_info = self.QueryInfo(None, None)

        start_time = datetime.now()
        df = self._run_query(query, *args, **kwargs)
        end_time = datetime.now()
        df = self._post_query(df)

        self.query_info.query = query
        self.query_info.time_taken = (end_time - start_time).total_seconds()

        return df

    def _run_query(self, query, **kwargs) -> pl.LazyFrame:
        assert self.spark is not None, "spark attribute must be set"
        df = self.spark.sql(query)
        return pl.from_arrow(
            pa.Table.from_batches(df._collect_as_arrow())
        ).lazy()


#! begin inject regex

#! end inject regex
