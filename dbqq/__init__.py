from . import security
from . import utils
from . import connectors

import polars as pl

pl.Config.set_tbl_rows(99)
pl.Config.set_tbl_cols(1000)