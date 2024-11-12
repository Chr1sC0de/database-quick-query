import urllib
from typing import Optional

import polars as pl
from triple_quote_clean import TripleQuoteCleaner

from ..utils import get_connector_details
from ._polar_connector import PolarsConnector

tqc = TripleQuoteCleaner(skip_top_lines=1)


GENERIC_TYPE_MAP = {
    "CHAR": "CHARACTER",
    "NCHAR": "CHARACTER",
    "NVARCHAR2": "CHARACTER",
    "VARCHAR2": "CHARACTER",
    "LONG": "CHARACTER",
    "RAW": "CHARACTER",
    "NUMBER": "NUMERIC",
    "SCALE": "NUMERIC",
    "NUMERIC": "NUMERIC",
    "FLOAT": "NUMERIC",
    "DEC": "NUMERIC",
    "DECIMAL": "NUMERIC",
    "INTEGER": "NUMERIC",
    "INT": "NUMERIC",
    "SMALLINT": "NUMERIC",
    "REAL": "NUMERIC",
    "DOUBLE": "NUMERIC",
    "DATE": "DATE/TIME",
    "TIMESTAMP": "DATE/TIME",
    "INTERVAL": "DATE/TIME",
    "INTERVAL YEAR": "DATE/TIME",
    "INTERVAL DAY": "DATE/TIME",
    "BFILE": "LOB",
    "BLOB": "LOB",
    "CLOB": "LOB",
    "NCLOB": "LOB",
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


class _MSSQLBase(PolarsConnector):
    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        hostname: Optional[str] = None,
        port: Optional[str] = None,
        database: Optional[str] = None,
        trusted_connection: Optional[bool] = None,
        server: Optional[str] = None,
        driver: Optional[str] = None,
    ):
        if all([v is not None for v in [username, password, hostname, port, database]]):
            self.connection = "mssql://%s:%s@%s:%s/%s" % (
                username,
                urllib.parse.quote_plus(password),
                hostname,
                port,
                database,
            )
        if trusted_connection and all([v is not None for v in [server, driver]]):
            self.connection = (
                f"Driver={driver};\nTrusted_Connection=yes;\nServer={server}"
            )
            if database is not None:
                self.connection += f"\n{database};"

            self.run_mode = "read_database"

    def describe_columns(self, table_name, **kwargs):
        query = (
            f"""--sql
            select
                c.name,
                type_name(c.user_type_id) as data_type,
                c.max_length as data_length,
                c.precision as data_precision,
                c.scale as data_scale
            from sys.tables t
            join sys.columns c on t.object_id = c.object_id
            where t.name = '{table_name.split(".")[-1]}'
        """
            >> tqc
        )

        self.description_query = query

        description = self(query, **kwargs)

        description = description.rename({c: c.upper() for c in description.columns})

        description = description.with_columns(
            pl.col("DATA_TYPE").apply(generic_type_mapper).alias("GENERIC_TYPE")
        )

        return description


class _general_connector(_MSSQLBase):
    targets = ["username", "password", "hostname", "port", "database"]
    source: str

    def __init__(self):
        configs = get_connector_details()
        mssql_configs = configs["mssql"]
        connector_config = mssql_configs[self.source]
        super().__init__(**connector_config)


#! begin inject regex

#! end inject regex
