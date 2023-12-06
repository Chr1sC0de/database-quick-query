from dbqq import connectors
import pytest


@pytest.mark.skipif(
    condition=not hasattr(connectors.redshift, "reduser"),
    reason="mswmovp1 must exist",
)
class TestRedshift:
    def test_infoserver_ret(self):
        import os

        connection = connectors.redshift.reduser()

        df = connection("select count(*) from dev_lpg_busmod.d_contract")

        assert df is not None, "df is None"

        column_description = connection.cache().describe_columns(
            "dev_lpg_busmod.d_contract"
        )

        assert column_description is not None, "df is None"

        return


if __name__ == "__main__":
    T = TestRedshift()
    T.test_infoserver_ret()
