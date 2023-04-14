from dbqq import connectors


class TestMSSQL:
    def test_infoserver_ret(self):
        connection: connectors.mssql = connectors.mssql.mswmovp1()

        df = connection("select top 100 * from pfdb.elec.ppa_hh")

        assert df is not None, "df is None"

        column_description = connection.cache().describe_columns(
            "pfdb.elec.ppa_hh"
        )

        assert column_description is not None, "df is None"

        return


if __name__ == "__main__":
    T = TestMSSQL()
    T.test_infoserver_ret()
