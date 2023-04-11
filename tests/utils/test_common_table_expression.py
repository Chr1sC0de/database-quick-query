from dbqq import utils
from triple_quote_clean import TripleQuoteCleaner

tqc = TripleQuoteCleaner(skip_top_lines=1)


def test_cte():
    cte = utils.CommonTableExpression()

    cte.add_query(
        "query_1",
        """--sql
            select *
            from table_1
        """
        >> tqc,
    )

    cte.add_query(
        "query_2",
        """--sql
            select
                *
            from
                table_2 t2
            inner join table_1 t1
                on t1.col1 = t2.col2

        """
        >> tqc,
    )

    print(cte("select * from table_2"))

    return


if __name__ == "__main__":
    test_cte()
