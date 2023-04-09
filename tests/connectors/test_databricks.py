import os

from triple_quote_clean import TripleQuoteCleaner

from dbqq import connectors

tqc = TripleQuoteCleaner(skip_top_lines=1)


class TestDatabricks:
    def test_dev_env(self):
        connection: connectors.databricks = connectors.databricks.dev()
        assert connection is not None, "connection is None"
        df = connection.cache()(
            """--sql
                select *
                from  hive_metastore.dev5_trading_eds.fact_discount_curve
            """
            >> tqc
        )
        assert df is not None, "df is None"
        column_description = connection.describe_columns(
            "hive_metastore.dev5_trading_eds.fact_discount_curve"
        )
        assert column_description.collect() is not None, "df is None"

        return

    def test_cluster(self):
        old_environ = dict(os.environ)

        new_values = {"DATABRICKS_RUNTIME_VERSION": "0.1.1"}

        os.environ.update(new_values)

        connection = connectors.databricks.dev()

        assert (
            connection.__class__ == connectors.databricks.Cluster
        ), "cluster is not initialized"

        os.environ.clear()

        os.environ.update(old_environ)

        return


if __name__ == "__main__":
    T = TestDatabricks()
    T.test_cluster()
