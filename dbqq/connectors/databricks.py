import polars as pl
from . _base import Base
from rsa import DecryptionError
from .. utils import get_connector_details, inject_connector_classes
from databricks import sql as databricks_sql
from triple_quote_clean import TripleQuoteCleaner


tqc = TripleQuoteCleaner(skip_top_lines=1)


GENERIC_TYPE_MAP = {
    'BIGINT': 'NUMERIC',
    'BINARY': 'NUMERIC',
    'TINYINT': 'NUMERIC',
    'DECIMAL': 'NUMERIC',
    'DOUBLE': 'NUMERIC',
    'FLOAT': 'NUMERIC',
    'INT': 'NUMERIC',
    'SMALLINT': 'NUMERIC',
    'STRING': 'CHARACTER',
    'BOOLEAN': 'BOOLEAN',
    'DATE': 'DATE/TIME',
    'INTERVAL': 'DATE/TIME',
    'TIMESTAMP': 'DATE/TIME',
    'VOID': 'VOID',
    'ARRAY': 'COMPLEX',
    'MAP': 'COMPLEX',
    'STRUCT': 'COMPLEX',
}


def generic_type_mapper(type):
    type = type.upper()
    if type in GENERIC_TYPE_MAP:
        return GENERIC_TYPE_MAP[type]
    else:
        for t in GENERIC_TYPE_MAP.keys():
            if t in type:
                return t
        return 'UNIDENTIFIED'


class _DatabricksBase(Base):

    connections = []

    def __init__(
        self, hostname: str, http_path: str, access_token: str
    ):

        self.connection = databricks_sql.connect(
            server_hostname=hostname,
            http_path=http_path,
            access_token=access_token
        )
        self.cursor = self.connection.cursor()

    def _run_query(self, query, *args, **kwargs) -> pl.LazyFrame:
        self.cursor.execute(query, *args, **kwargs)
        return pl.from_arrow(self.cursor.fetchall_arrow()).lazy()

    def close(self):
        self.connection.close()
        self.cursor.close()

    def describe_columns(self, table_name: str) -> pl.LazyFrame:

        query = f"describe {table_name}"

        description: pl.LazyFrame = self(query)

        description = (
            description
            .filter(
                pl.col("col_name")
                .str
                .contains("^\#")
                .is_not()
            )
            .unique()
            .rename(
                {c: c.upper() for c in description.columns}
            )
            .with_columns(
                pl.lit(None).alias("DATA_LENGTH")
            )
            .with_columns(
                pl.col("DATA_TYPE")
                .str
                .extract('[(](\d+),(\d+)[)]', 1)
                .cast(pl.Int32)
                .alias("DATA_PRECISION")
            )
            .with_column(
                pl.col("DATA_TYPE")
                .str
                .extract('[(](\d+),(\d+)[)]', 2)
                .cast(pl.Int32)
                .alias("DATA_SCALE")
            )
            .with_column(
                pl.col("DATA_TYPE")
                .str
                .extract('\w+', 0)
            )
            .with_column(
                pl.col("DATA_TYPE")
                .apply(generic_type_mapper)
                .alias("GENERIC_TYPE")
            )
            .with_column(
                pl.col("DATA_TYPE").str.to_uppercase()
            )
            .select(
                [
                    "COL_NAME",
                    "DATA_TYPE",
                    "DATA_LENGTH",
                    "DATA_PRECISION",
                    "DATA_SCALE"
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

#! begin inject regex

#! end inject regex


try:

    configs = get_connector_details()

    inject_connector_classes(__file__, configs, 'databricks')

except DecryptionError:
    pass
except AssertionError:
    pass
except TypeError:
    pass
except Exception as er:
    raise er
