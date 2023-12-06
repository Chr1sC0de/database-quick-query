import polars as pl
from ._polar_connector import PolarsConnector
from triple_quote_clean import TripleQuoteCleaner

from ..utils import get_connector_details

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


class _RedshiftBase(PolarsConnector):
    def __init__(self, username, password, hostname, port, database):
        self.connection = "postgresql://%s:%s@%s:%s/%s" % (
            username,
            password,
            hostname,
            port,
            database,
        )

    def _run_query(self, *args, **kwargs) -> pl.LazyFrame:
        kwargs["protocol"] = "cursor"
        return super()._run_query(*args, **kwargs)

    def describe_columns(
        self, table_name, owner=None, **kwargs
    ) -> pl.LazyFrame:
        table_name = table_name.upper()

        if owner is not None:
            owner = owner.upper()

        if "." in table_name:
            owner, table_name = table_name.split(".")

        if owner is not None:
            query = (
                f"""--sql
                select
                    a.attname as column_name,
                    format_type(a.atttypid, a.atttypmod) as data_type,
                    case
                        when a.atttypid = 1043 then a.atttypmod - 4 -- varchar
                        when a.atttypid = 1082 then 0 -- date
                        when a.atttypid = 23 then 32 -- integer
                        else null
                    end as data_length,
                    case
                        when a.atttypid = 1700 then (a.atttypmod - 4) / 65536 -- numeric (precision)
                        else null
                    end as data_precision,
                    case
                        when a.atttypid = 1700 then (a.atttypmod - 4) % 65536 -- numeric (scale)
                        else null
                    end as data_scale
                from pg_attribute a
                join pg_class c on a.attrelid = c.oid
                join pg_namespace n on c.relnamespace = n.oid
                where n.nspname = '{owner.lower()}'
                and c.relname = '{table_name.lower()}'
                and a.attnum > 0
                and not a.attisdropped
                order by a.attnum
                """
                >> tqc
            )
        else:
            query = (
                f"""--sql
                select
                    a.attname as column_name,
                    format_type(a.atttypid, a.atttypmod) as data_type,
                    case
                        when a.atttypid = 1043 then a.atttypmod - 4 -- varchar
                        when a.atttypid = 1082 then 0 -- date
                        when a.atttypid = 23 then 32 -- integer
                        else null
                    end as data_length,
                    case
                        when a.atttypid = 1700 then (a.atttypmod - 4) / 65536 -- numeric (precision)
                        else null
                    end as data_precision,
                    case
                        when a.atttypid = 1700 then (a.atttypmod - 4) % 65536 -- numeric (scale)
                        else null
                    end as data_scale
                from pg_attribute a
                join pg_class c on a.attrelid = c.oid
                join pg_namespace n on c.relnamespace = n.oid
                where c.relname = '{table_name.lower()}'
                and a.attnum > 0
                and not a.attisdropped
                order by a.attnum
                """
                >> tqc
            )

        self.description_query = query

        description = self(query, **kwargs)

        description = description.rename(
            {c: c.upper() for c in description.columns}
        )

        # TODO: Datatypes don't correctly map
        description = description.with_columns(
            pl.col("DATA_TYPE")
            .apply(generic_type_mapper)
            .alias("GENERIC_TYPE")
        )

        return description


class _general_connector(_RedshiftBase):
    targets = ["username", "password", "hostname", "port", "database"]
    source: str

    def __init__(self):
        configs = get_connector_details()
        redshift_configs = configs["redshift"]
        connector_config = redshift_configs[self.source]
        args = [connector_config[key] for key in self.targets]
        super().__init__(*args)


#! begin inject regex

#! end inject regex
