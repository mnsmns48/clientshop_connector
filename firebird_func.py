from env_config import imports
from engine import fdb_connection


def firebird_data() -> list:
    folders: dict = get_folders(include=imports.includes, exclude=imports.excludes)
    final_folders: tuple = get_final_folders(include=imports.includes, exclude=imports.excludes)
    products: dict = get_product(folders=folders['folders'])
    to_del = list()
    for p in final_folders:
        if (p not in products['parents']) and (p in folders['folders']):
            to_del.append(p)
    filtered_folders = [line for line in folders['data'] if line['code'] not in to_del]
    return filtered_folders + products['data']


def get_folders(include: tuple, exclude: tuple) -> dict:
    data = list()
    folders = list()
    if not exclude:
        exclude = "('')"
    query = f"""
        WITH RECURSIVE cte AS (
            SELECT
                dg.code, dg.parent, dg.name, dg.ispath
            FROM
                DIR_GOODS dg
            WHERE
                dg.name IN {include}
            UNION ALL
            SELECT
                dg.code, dg.parent, dg.name, dg.ispath
            FROM
                DIR_GOODS dg
            INNER JOIN
                cte ON dg.parent = cte.code
        )
        SELECT
            cte.code,
            cte.parent,
            cte.name
        FROM
            cte
        WHERE
            cte.ispath = 1 AND cte.NAME NOT IN {exclude};
    """
    cur = fdb_connection.cursor()
    fetch = cur.execute(query)
    for line in fetch.fetchall():
        data.append(
            {'code': line[0], 'parent': line[1], 'ispath': True, 'name': line[2], 'quantity': None, 'price': None}
        )
        folders.append(int(line[0]))
    return {'data': data, 'folders': tuple(folders)}


def get_product(folders: tuple) -> dict:
    query = f"""
    SELECT
        SQ.CODE,
        SQ.PARENT,
        SQ.NAME,
        SUM(QUANTITY),
        SQ.PRICE_
    FROM
        (
        SELECT
            dg.CODE,
            dg.parent,
            dg.NAME,
            dst.QUANTITY,
            dg.PRICE_
        FROM
            DIR_GOODS dg
        JOIN 
            DOC_SESSION_TABLE dst ON dg.CODE = dst.GOOD
        JOIN 
            DOC_SESSION ds ON dst.CODE = ds.CODE
        WHERE
            ds.OPENED = 1 AND dg.CODE = dst.GOOD AND dg.PARENT IN {folders}
        UNION ALL
        SELECT
            dg.CODE,
            dg.parent,
            dg.NAME,
            -dst2.QUANTITY,
            dg.PRICE_
        FROM
            DIR_GOODS dg
        JOIN
            DOC_SALE_TABLE dst2 ON dg.CODE = dst2.GOOD
        WHERE
            dg.PARENT IN {folders}
        UNION ALL
        SELECT
            dg.CODE,
            dg.parent,
            dg.NAME,
            -dbt.QUANTITY,
            dg.PRICE_
        FROM
            DIR_GOODS dg
        JOIN
            DOC_BALANCE_TABLE dbt ON dg.CODE = dbt.GOOD
        WHERE
            dg.PARENT IN {folders}
        UNION ALL
        SELECT
            dg.CODE,
            dg.parent,
            dg.NAME,
            +drt.QUANTITY,
            dg.PRICE_
        FROM
            DIR_GOODS dg
        JOIN
            DOC_RETURN_TABLE drt ON dg.CODE = drt.GOOD
        WHERE
            dg.PARENT IN {folders}
        UNION ALL
        SELECT
            dg.CODE,
            dg.parent,
            dg.NAME,
            -det.QUANTITY,
            dg.PRICE_
        FROM
            DIR_GOODS dg
        JOIN
            DOC_EXPSESSION_TABLE det ON dg.CODE = det.GOOD
        WHERE
            dg.PARENT IN {folders}
        ) SQ
    GROUP BY
        SQ.CODE,
        SQ.PARENT,
        SQ.NAME,
        SQ.PRICE_
    HAVING
        SUM(SQ.QUANTITY) >= 1
    ORDER BY
        SQ.PARENT,
        SQ.CODE;
    """
    cur = fdb_connection.cursor()
    fetch = cur.execute(query)
    products = list()
    parents = list()
    for line in fetch.fetchall():
        products.append({'code': line[0], 'parent': line[1], 'ispath': False, 'name': line[2], 'quantity': line[3],
                         'price': line[4]}
                        )
        parents.append(int(line[1]))
    return {'data': products,
            'parents': tuple(set(parents))}


def get_final_folders(include: tuple, exclude: tuple) -> tuple:
    if not exclude:
        exclude = "('')"
    query = f"""
    WITH RECURSIVE cte AS (
        SELECT
            dg.code,
            dg.parent,
            dg.name,
            dg.ispath
        FROM
            DIR_GOODS dg
        WHERE
            dg.name IN {include}
        UNION ALL
        SELECT
            dg.code,
            dg.parent,
            dg.name,
            dg.ispath
        FROM
            DIR_GOODS dg
        INNER JOIN cte ON
            dg.parent = cte.code
    )
    SELECT
        cte.code,
        cte.parent,
        cte.name
    FROM
        cte
    WHERE
        cte.ispath = 1
        AND cte.code NOT IN (
            SELECT
                parent
            FROM
                DIR_GOODS
            WHERE
                ispath = 1 AND name NOT IN {exclude}
        );
    """
    cur = fdb_connection.cursor()
    fetch = cur.execute(query)
    result = [line[0] for line in fetch.fetchall()]
    return tuple(result)


def get_fdb_activity() -> list:
    result = list()
    cur = fdb_connection.cursor()
    cur.execute(
        """
        SELECT ds.CODE, ds.DOC_DATE, dst.GOOD, dg.NAME, dst.QUANTITY, dst.PRICE2, dst.SUMMA2, ds.NONCASH
        FROM DOC_SALE ds, DOC_SALE_TABLE dst, DIR_GOODS dg
        WHERE CAST(ds.DOC_DATE AS DATE) = CAST('now' AS DATE) 
        AND (ds.CODE = dst.CODE)
        AND (dst.GOOD = dg.CODE)
        UNION ALL
        SELECT dr.CODE AS RCODE, dr.DOC_DATE, drt.GOOD, dg.NAME, drt.QUANTITY, drt.PRICE2, drt.SUMMA2, dr.NONCASH
        FROM DOC_RETURN dr, DOC_RETURN_TABLE drt, DIR_GOODS dg
        WHERE CAST(dr.DOC_DATE AS DATE) = CAST('now' AS DATE) 
        AND (dr.CODE = drt.CODE)
        AND (drt.GOOD = dg.CODE)
        ORDER BY 2
        """
    )
    for line in cur.fetchall():
        result.append(
            {
                'operation_code': int(line[0]),
                'time_': str(line[1]),
                'product_code': int(line[2]),
                'product': line[3],
                'quantity': int(line[4]),
                'price': float(line[5]),
                'sum_': float(line[6]),
                'noncash': int(line[7]) == 1 or False,
                'return_': int(line[0]) <= 30000 or False
            }
        )
    return result
