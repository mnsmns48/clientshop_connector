from config_import_ import include_path, exclude_path
from engine import fdb_connection


def firebird_data():
    folders: dict = get_folders(include=include_path, exclude=exclude_path)
    final_folders: tuple = get_final_folders(all_folders=folders['folders'])
    products: dict = get_product(folders=folders['folders'])
    # print(products['parents'])
    to_del = list()
    for p in final_folders:
        if (p not in products['parents']) and (p in folders['folders']):
            to_del.append(p)
    print(final_folders)
    # print(products)


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
    return {'products': products,
            'parents': tuple(set(parents))}


def get_final_folders(all_folders: tuple) -> tuple:
    query = f"""
    SELECT
        dg.code
    FROM
        DIR_GOODS dg
    WHERE
        dg.parent is Null
        AND dg.ISPATH = 1;
    """
    cur = fdb_connection.cursor()
    fetch = cur.execute(query)
    result = list()
    [result.append(line[0]) for line in fetch.fetchall()]
    return tuple(result)