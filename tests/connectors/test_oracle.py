from dbqq import connectors


class TestOracle:
    def test_infoserver_ret(self):
        connection = connectors.oracle.infoserver_gen()

        df = connection(
            "select * from mms.billingfees fetch first 100 rows only"
        )

        assert df is not None, "df is None"

        column_description = connection.describe_columns("mms.billingfees")

        assert column_description is not None, "df is None"

        return


if __name__ == "__main__":
    T = TestOracle()
    T.test_infoserver_ret()
