import datetime
import pathlib as pt
from dataclasses import dataclass


@dataclass
class Base:
    query: str
    module: "dbqq.connectors.Base"


@dataclass
class NameQueryModule:
    name: str
    query: str
    module: "dbqq.connectors.Base"


class _CacheFileNameMixin:
    def __post_init__(self):
        if self.name == "_":
            self.name = None


@dataclass
class NameQueryModuleCache(_CacheFileNameMixin):
    name: str
    query: str
    module: "dbqq.connectors.Base"
    cache_directory: pt.Path


@dataclass
class NameQueryModuleCacheDate(_CacheFileNameMixin):
    name: str
    query: str
    module: "dbqq.connectors.Base"
    cache_directory: pt.Path
    date_lower_bound: datetime.datetime
