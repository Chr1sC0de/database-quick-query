from . import databricks, mssql, oracle
from ._base import Base

from pathlib import Path as _Path
from typing import Tuple as _Tuple


def from_file(filepath: _Path) -> _Tuple[Base, str]:
    from .. import utils, enums

    parsed = utils.parse_file(filepath)

    connection_map = {
        enums.parsed.sql.NameQueryModule: lambda: parsed.module(),
        enums.parsed.sql.NameQueryModuleCache: lambda: parsed.module().cache(
            directory=parsed.cache_directory, name=parsed.name
        ),
        enums.parsed.sql.NameQueryModuleCacheDate: lambda: parsed.module().cache(
            directory=parsed.cache_directory,
            name=parsed.name,
            date_lower_bound=parsed.date_lower_bound,
        ),
    }
    connection = connection_map[parsed.__class__]()
    return connection, parsed.query


__all__ = ["databricks", "mssql", "oracle", "Base", "from_file"]
