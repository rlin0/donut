import flask

import pymysql.cursors


def get_member_data(user_id, fields=None):
    """
    Queries the database and returns member data for the specified user_id
    or list of user_id's.

    Arguments:
        user_id: The member (or list of members) to look up
        fields:  The fields to return. If None specified, then default_fields
                 are used.
    Returns:
        result: The fields and corresponding values of member with user_id. In
                the form of a dict with key:value of columnname:columnvalue.
                For lists of user_id's result will be a list of dicts.
    """
    all_returnable_fields = [
        "user_id", "uid", "last_name", "first_name", "middle_name", "email",
        "phone", "gender", "gender_custom", "birthday", "entry_year",
        "graduation_year", "msc", "building", "room_num", "address", "city",
        "state", "zip", "country"
    ]
    default_fields = [
        "user_id", "first_name", "last_name", "email", "uid", "entry_year",
        "graduation_year"
    ]
    if fields == None:
        fields = default_fields
    else:
        if any(f not in all_returnable_fields for f in fields):
            return "Invalid field"

    if not isinstance(user_id, list):
        user_id = [user_id]

    # edge case: user_id is empty list
    if len(user_id) == 0:
        return {}

    query = "SELECT " + ', '.join(fields) + " FROM members WHERE "
    query += ' OR '.join(["user_id=%s" for _ in user_id])

    # Execute the query
    with flask.g.pymysql_db.cursor() as cursor:
        cursor.execute(query, user_id)
        result = cursor.fetchall()

    if len(result) == 0:
        return {}
    elif len(result) == 1:
        return result[0]
    return result


def get_member_list_data(fields=None, attrs={}):
    """
    Queries the database and returns list of member data constrained by the
    specified attributes.

    Arguments:
        fields: The fields to return. If None specified, then default_fields
                are used.
        attrs:  The attributes of the members to filter for.
    Returns:
        result: The fields and corresponding values of members with desired
                attributes. In the form of a list of dicts with key:value of
                columnname:columnvalue.
    """
    all_returnable_fields = [
        "user_id", "uid", "last_name", "first_name", "middle_name", "email",
        "phone", "gender", "gender_custom", "birthday", "entry_year",
        "graduation_year", "msc", "building", "room_num", "address", "city",
        "state", "zip", "country"
    ]
    default_fields = [
        "user_id", "first_name", "last_name", "email", "uid", "entry_year",
        "graduation_year"
    ]
    if fields == None:
        fields = default_fields
    else:
        if any(f not in all_returnable_fields for f in fields):
            return "Invalid field"

    query = "SELECT " + ', '.join(fields) + " FROM members"

    if attrs:
        query += " WHERE "
        query += ' AND '.join([key + "= %s" for key, value in attrs.items()])
    values = [value for key, value in attrs.items()]

    # Execute the query
    with flask.g.pymysql_db.cursor() as cursor:
        cursor.execute(query, values)
        return cursor.fetchall()


def get_name_and_email(user_id):
    """
    Queries the database and returns the full_name and email corresponding to the
    user_id.

    Arguments:
        user_id:            The user_id to match.
    Returns:
        (full_name, email): The full_name and email corresponding, in a tuple.
    """
    query = """SELECT full_name, email 
    FROM members NATURAL LEFT JOIN members_full_name 
    WHERE user_id=%s"""

    with flask.g.pymysql_db.cursor() as cursor:
        cursor.execute(query, [user_id])
        result = cursor.fetchall()

    return (result[0]["full_name"], result[0]["email"])


def get_group_list_of_member(user_id):
    """
    Queries the database and returns list of groups and admin status 
    for a given id
    Arguments:
        user_id: The user_id for query.
    Returns:
        result: All the groups that an user_id is a part of
    """
    query = """SELECT group_id, group_name, control 
    FROM group_members NATURAL JOIN groups NATURAL JOIN members 
    WHERE user_id = %s"""

    with flask.g.pymysql_db.cursor() as cursor:
        cursor.execute(query, [user_id])
        return list(cursor.fetchall())
