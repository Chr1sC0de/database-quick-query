from dbqq import connectors


class TestOracle:
    def test_infoserver_ret(self):
        connection = connectors.oracle.infoserver_gen()

        df = connection.cache()("select * from mms.billingfees")

        assert df is not None, "df is None"

        column_description = connection.describe_columns("mms.billingfees")

        assert column_description is not None, "df is None"

        return


if __name__ == "__main__":
    T = TestOracle()
    T.test_infoserver_ret()
