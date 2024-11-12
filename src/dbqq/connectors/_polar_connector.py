import os
import polars as pl
from ._base import Base
import connectorx as cx
from typing import Dict
from typing import Tuple


class PolarsConnector(Base):
    run_mode = "read_sql"

    def __call__(
        self,
        query: str,
        *args,
        scan_parquet_kwargs: Dict[str, str] = None,
        protocol: str = "binary",
        partition_on: str = None,
        partition_range: Tuple[int, int] = None,
        partition_num: int = None,
    ) -> pl.LazyFrame:
        """
        scan_parquet_kwargs are arguments which will be passed to
        https://pola-rs.github.io/polars/py-polars/html/reference/api/polars.scan_parquet.html#polars-scan-parquet
        """
        return super().__call__(
            query,
            scan_parquet_kwargs=scan_parquet_kwargs,
            partition_num=partition_num,
            protocol=protocol,
            partition_on=partition_on,
            partition_range=partition_range,
        )

    def _run_query(
        self,
        query: str,
        *args,
        protocol: str = "binary",
        partition_on: str = None,
        partition_range: Tuple[int, int] = None,
        partition_num: int = None,
        login_timeout_sec: int = 150,
        **kwargs,
    ) -> pl.LazyFrame:
        try:
            if partition_num is None:
                partition_num = os.cpu_count()

            if self.run_mode == "read_sql":
                return cx.read_sql(
                    self.connection,
                    query,
                    *args,
                    return_type="polars",
                    partition_num=partition_num,
                    protocol=protocol,
                    partition_on=partition_on,
                    partition_range=partition_range,
                    **kwargs,
                ).lazy()
            elif self.run_mode == "read_database":
                return pl.read_database(
                    query,
                    self.connection,
                    execute_options={"login_timeout_sec": login_timeout_sec},
                    **kwargs,
                ).lazy()

        except RuntimeError:
            raise RuntimeError(query)

    def close(self):
        return
