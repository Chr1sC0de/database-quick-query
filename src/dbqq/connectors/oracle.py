import os
import polars as pl
import connectorx as cx
from . _base import Base
from rsa import DecryptionError
from triple_quote_clean import TripleQuoteCleaner
from .. utils import get_connector_details, inject_connector_classes


tqc = TripleQuoteCleaner(skip_top_lines=1)


GENERIC_TYPE_MAP = {
    'CHAR': 'CHARACTER',
    'NCHAR': 'CHARACTER',
    'NVARCHAR2': 'CHARACTER',
    'VARCHAR2': 'CHARACTER',
    'LONG': 'CHARACTER',
    'RAW': 'CHARACTER',
    'NUMBER': 'NUMERIC',
    'SCALE': 'NUMERIC',
    'NUMERIC': 'NUMERIC',
    'FLOAT': 'NUMERIC',
    'DEC': 'NUMERIC',
    'DECIMAL': 'NUMERIC',
    'INTEGER': 'NUMERIC',
    'INT': 'NUMERIC',
    'SMALLINT': 'NUMERIC',
    'REAL': 'NUMERIC',
    'DOUBLE': 'NUMERIC',
    'DATE': 'DATE/TIME',
    'TIMESTAMP': 'DATE/TIME',
    'INTERVAL': 'DATE/TIME',
    'INTERVAL YEAR': 'DATE/TIME',
    'INTERVAL DAY': 'DATE/TIME',
    'BFILE': 'LOB',
    'BLOB': 'LOB',
    'CLOB': 'LOB',
    'NCLOB': 'LOB',
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


class _OracleBase(Base):

    connections = []

    def __init__(
        self,
        username,
        password,
        hostname,
        port,
        database
    ):

        # self.con = 'oracle://username:password@server:port/database'
        self.connection = 'oracle://%s:%s@%s:%s/%s' % (
            username,
            password,
            hostname,
            port,
            database
        )

    def _run_query(
        self, query: str, *args, partition_num=None, **kwargs
    ) -> pl.LazyFrame:
        try:
            if partition_num is None:
                partition_num = os.cpu_count()
            return cx.read_sql(
                self.connection, query, *args,
                return_type="polars", partition_num=partition_num, **kwargs
            ).lazy()
        except RuntimeError:
            raise RuntimeError(query)

    def close(self):
        return

    def describe_columns(self, table_name, owner=None, **kwargs):

        table_name = table_name.upper()

        if owner is not None:
            owner = owner.upper()

        if '.' in table_name:
            owner, table_name = table_name.split(".")

        if owner is not None:

            query = f"""--sql
                select
                    column_name as col_name,
                    data_type,
                    data_length,
                    data_precision,
                    data_scale
                from (
                    select col.column_id,
                        col.owner,
                        col.table_name,
                        col.column_name,
                        col.data_type,
                        col.data_length,
                        col.data_precision,
                        col.data_scale,
                        col.nullable
                    from sys.all_tab_columns col
                    left join sys.all_views v on col.owner = v.owner
                                                and col.table_name = v.view_name
                    order by col.owner, col.table_name, col.column_id
                )
                where lower(owner) = '{owner.lower()}'
                and lower(table_name) = '{table_name.lower()}'
            """ >> tqc
        else:
            query = f"""--sql
                select
                    column_name as col_name,
                    data_type,
                    data_length,
                    data_precision,
                    data_scale
                from (
                    select col.column_id,
                        col.owner,
                        col.table_name,
                        col.column_name,
                        col.data_type,
                        col.data_length,
                        col.data_precision,
                        col.data_scale,
                        col.nullable
                    from sys.all_tab_columns col
                    left join sys.all_views v on col.owner = v.owner
                                                and col.table_name = v.view_name
                    order by col.owner, col.table_name, col.column_id
                )
                and lower(table_name) = '{table_name.lower()}'
            """ >> tqc

        description = self(query, **kwargs)

        description = description.with_columns(
            pl.col("DATA_TYPE").apply(
                generic_type_mapper).alias("GENERIC_TYPE")
        )

        return description


class _general_connector(_OracleBase):
    targets = ["username", "password", "hostname", "port", "database"]
    source: str

    def __init__(self):
        configs = get_connector_details()
        oracle_configs = configs["oracle"]
        connector_config = oracle_configs[self.source]
        args = [connector_config[key] for key in self.targets]
        super().__init__(*args)


#! begin inject regex

#! end inject regex


try:

    configs = get_connector_details()

    inject_connector_classes(__file__, configs, 'oracle')

except DecryptionError:
    pass
except AssertionError:
    pass
except TypeError:
    pass
except Exception as er:
    raise er