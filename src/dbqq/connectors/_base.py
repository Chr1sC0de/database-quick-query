import re
import jinja2.nativetypes
import yaml
import polars as pl
import pathlib as pt
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import uuid1


class Base(ABC):
    to_cache: bool = False
    description_query: str = None

    class RenderedTemplateLoader:
        def __init__(self, query: str, connection: "Base"):
            self.query = query
            self.connection = connection

        def execute(self, *args, **kwargs) -> pl.LazyFrame:
            return self(*args, **kwargs)

        def __call__(self, *args, **kwargs) -> pl.LazyFrame:
            return self.connection(self.query, *args, **kwargs)

        def __repr__(self):
            output = f"<{self.__class__.__name__} object at {hex(id(self))}>\n"
            output += f"with {repr(self.connection)}\n"
            output += self.query
            return output

    @dataclass
    class QueryInfo:
        query: str
        time_taken: timedelta

    @dataclass
    class CacheMetadata:
        date_lower_bound: datetime
        directory: pt.Path
        name: str

    @abstractmethod
    def describe_columns(self, table_name: str) -> pl.LazyFrame:
        ...

    class meta:
        QUERY = "query"
        TIMETAKEN = "time_taken"
        PARQUETFILE = "parquet_file"

    def from_file(self, filepath: pt.Path, *args, **kwargs) -> pl.LazyFrame:
        with open(filepath, "r") as f:
            query = f.read().replace(";", "")
            query = re.sub(r"--!.+\n", "", query)
        return self(query, *args, **kwargs)

    def render_template(
        self, filepath: pt.Path, *args, **kwargs
    ) -> "Base.RenderedTemplateLoader":
        with open(filepath, "r") as f:
            query = f.read().replace(";", "")
            query = re.sub(r"--!.+\n", "", query)

        environment = jinja2.nativetypes.NativeEnvironment(
            trim_blocks=True, lstrip_blocks=True, autoescape=True
        )

        query = environment.from_string(query).render(*args, **kwargs)
        return Base.RenderedTemplateLoader(query, self)

    def execute(
        self, *args, scan_parquet_kwargs=None, **run_query_kwargs
    ) -> pl.LazyFrame:
        return self(
            *args, scan_parquet_kwargs=scan_parquet_kwargs, **run_query_kwargs
        )

    def __call__(
        self, query: str, *args, scan_parquet_kwargs=None, **run_query_kwargs
    ) -> pl.LazyFrame:
        self.query_info = self.QueryInfo(None, None)

        if self.to_cache:
            cached_df = self._load_from_cache(
                query, scan_parquet_kwargs=scan_parquet_kwargs
            )
            if isinstance(cached_df, (pl.DataFrame, pl.LazyFrame)):
                return cached_df

        start_time = datetime.now()
        df = self._run_query(query, *args, **run_query_kwargs)
        end_time = datetime.now()
        df = self._post_query(df)

        self.query_info.query = query
        self.query_info.time_taken = (end_time - start_time).total_seconds()

        if self.to_cache:
            self._cache_df(df, self.query_info)

        return df

    def _load_from_cache(
        self, query: str, *args, scan_parquet_kwargs: dict = None, **kwargs
    ) -> pl.LazyFrame:
        """
        scan_parquet_kwargs are arguments which will be passed to
        https://pola-rs.github.io/polars/py-polars/html/reference/api/polars.scan_parquet.html#polars-scan-parquet
        """
        if scan_parquet_kwargs is None:
            scan_parquet_kwargs = {}

        def to_dt(x):
            return datetime.fromtimestamp(x)

        df = None

        if hasattr(self, "cache_metadata"):
            yaml_files = sorted(
                list(self.cache_metadata.directory.glob("*yaml")),
                key=lambda x: x.stat().st_ctime,
                reverse=True,
            )
            # now filter based off the date_lower_bound
            valid_files = [
                f
                for f in yaml_files
                if to_dt(f.stat().st_ctime)
                >= self.cache_metadata.date_lower_bound
            ]

            [
                (f.unlink(), (f.parent / ("%s.parquet" % f.stem)).unlink())
                for f in yaml_files
                if to_dt(f.stat().st_ctime)
                < self.cache_metadata.date_lower_bound
            ]

            for yaml_file in valid_files:
                with open(yaml_file, "r") as f:
                    metadata = yaml.safe_load(f)

                if query == metadata[self.meta.QUERY]:
                    parquet_file = pt.Path(metadata[self.meta.PARQUETFILE])
                    if parquet_file.exists():
                        df = pl.scan_parquet(
                            parquet_file, **scan_parquet_kwargs
                        )
                        self.query_info.time_taken = metadata[
                            self.meta.TIMETAKEN
                        ]
                        self.query_info.query = metadata[self.meta.QUERY]

        return df

    def cache(
        self,
        date_lower_bound: datetime = datetime.min,
        directory: pt.Path = pt.Path(".temp"),
        name: str = None,
        write_parquet_kwargs: dict = None,
        parents: bool = True,
        exists_ok: bool = True,
    ):
        directory = pt.Path(directory)

        self.to_cache = True
        self.cache_metadata = self.CacheMetadata(
            date_lower_bound, directory, name
        )

        if write_parquet_kwargs is None:
            write_parquet_kwargs = {}

        self.write_parquet_kwargs = write_parquet_kwargs

        directory.mkdir(parents=parents, exist_ok=exists_ok)
        return self

    def _cache_df(self, df: pl.LazyFrame, query_info: "QueryInfo"):
        if self.cache_metadata.name is not None:
            file_name = self.cache_metadata.name
        else:
            file_name = uuid1()

        output_filename = self.cache_metadata.directory / (
            "%s.parquet" % file_name
        )
        metadata_file = self.cache_metadata.directory / ("%s.yaml" % file_name)

        metadata_dict = {}

        metadata_dict = {
            self.meta.QUERY: query_info.query,
            self.meta.TIMETAKEN: query_info.time_taken,
            self.meta.PARQUETFILE: output_filename.absolute().as_posix(),
        }

        with open(metadata_file, "w") as f:
            yaml.dump(metadata_dict, f)

        df.collect().write_parquet(
            output_filename, **self.write_parquet_kwargs
        )

    def _post_query(self, df: pl.LazyFrame) -> pl.LazyFrame:
        return df

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.close()
        return False

    @abstractmethod
    def _run_query(self):
        ...

    @abstractmethod
    def close(self):
        ...

    def get_database(self) -> str:
        return self.__module__.split(".")[-1]

    def get_name(self) -> str:
        return self.__class__.__name__.split(".")[-1]

    def get_db_name(self) -> str:
        return f"{self.get_database()}-{self.get_name()}"
