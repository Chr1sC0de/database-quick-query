from ._base import Base
from ._polar_connector import PolarsConnector
from . import databricks, mssql, oracle, redshift

from pathlib import Path as _Path
from typing import Tuple as _Tuple


def from_file(filepath: _Path) -> _Tuple[Base, str]:
    from .. import utils, data

    parsed = utils.parse_file(filepath)

    connection_map = {
        data.parsed.sql.NameQueryModule: lambda: parsed.module(),
        data.parsed.sql.NameQueryModuleCache: lambda: parsed.module().cache(
            directory=parsed.cache_directory, name=parsed.name
        ),
        data.parsed.sql.NameQueryModuleCacheDate: lambda: parsed.module().cache(
            directory=parsed.cache_directory,
            name=parsed.name,
            date_lower_bound=parsed.date_lower_bound,
        ),
    }
    connection = connection_map[parsed.__class__]()
    return connection, parsed.query


__all__ = [
    "Base",
    "PolarsConnector",
    "databricks",
    "mssql",
    "oracle",
    "from_file",
    "redshift",
]
