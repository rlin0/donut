import flask
import sqlalchemy
import re
from math import ceil

from donut.modules.core.helpers import get_member_data

from . import routes

# taken from donut-legacy, which was apparently taken from a CS11
# C++ assignment by dkong
SKIP_WORDS = [
    "a", "all", "am", "an", "and", "are", "as", "at", "be", "been", "but",
    "by", "did", "do", "for", "from", "had", "has", "have", "he", "her",
    "hers", "him", "his", "i", "if", "in", "into", "is", "it", "its", "me",
    "my", "not", "of", "on", "or", "so", "that", "the", "their", "them",
    "they", "this", "to", "up", "us", "was", "we", "what", "who", "why",
    "will", "with", "you", "your"
]


def render_with_top_marketplace_bar(template_url, **kwargs):
    """
    Provides an easy way for routing functions to pass the variables required for
    rendering the marketplace's top bar to render_template.  Basically chains
    some other arguments on to the render call, namely the list of marketplace
    categories, the list urls to categories, and the width of each url column.

    Arguments:
        template_url: The url which is being rendered.
        **kwargs: The variables which are used to render the rest of the page.

    Returns:
        The result of render_template(): Whatever magic Flask does to render the
                                         final page.
    """
    # Get category titles

    fields = ["cat_title"]
    categories = list(get_table_list_data("marketplace_categories", fields))
    # get_table_list_data always returns a list of lists, but we know that
    # each list is only one element long, and we only want a list of strings.
    for i in range(len(categories)):
        categories[i] = categories[i][0]

    # Get number of rows and columns to display categories nicely. This is a
    # little tricky - we want to aim for a table with either 4 categories or 5
    # categories per row, with the last row catching the remainder. However, we
    # want to avoid having exactly 1 category in the remainder row if possible.
    # Thus we do our best to prevent num_cats % num_cols from being 1.
    num_cats = len(categories)
    if num_cats <= 5:
        num_cols = num_cats
    elif num_cats % 5 != 1:
        num_cols = 5
    elif num_cats % 4 != 1:
        num_cols = 4
    else:
        num_cols = 5

    cats2d = [[]]
    width = ""
    if num_cols != 0:
        # if there's nothing in categories, just return default values for cats2d and width
        num_rows = ceil(num_cats / num_cols)

        # Break categories into a 2d array so that it's easy to arrange in rows
        # in the html file.
        cats2d = [[]] * num_rows
        for cat_index in range(len(categories)):
            cats2d[cat_index // num_cols].append(categories[cat_index])

        # This is simpler than a bootstrap col-sm-something, since we want a variable number of columns.
        width = "width: " + str(100.0 / (num_cols)) + "%"

        # Pass the 2d category array, urls array, and width string, along with the arguments passed in to this
        # function, on to Flask in order to render the top bar and the rest of the content.
        return flask.render_template(
            template_url, cats=cats2d, width=width, **kwargs)


def generate_search_table(fields=None, attrs={}, query=""):
    """
    Provides a centralized way to generate the 2d array of cells that is displayed
    in a table, along with all the stuff that needs to be packaged with it.  Calls
    a few functions further down to get the data, merge some columns, and rename
    the headers.

    Arguments:
    fields: A list of the fields that are requested to be in the table.  For
        example: ["cat_id", "item_title", "textbook_title", "item_price",
            ...]

        attrs: A map of fields to values that make up conditions on the fields.
               For example, {"cat_id":1} will only return results for which the
               category id is 1.

        query: The query we want to filter our results by.  If "", no
               filtering happens.

    Returns:
        result: The 2d array that was requested.

        headers: The English-ified headers for each column.

        links: A 2d array that, in each cell, gives the url of the link that
               clicking on the corresponding cell in result should yield.  If none,
               the cell will contain the number 0 instead.
    """

    # We need the item_id to generate the urls that clicking on the item title
    # should go to.
    # Also, we add it to the front so that we can get the id before we need to use
    # it (i.e., when we're adding it to links)
    fields = ["item_id"] + fields

    if query != "":
        # and add cat_id, textbook_author and textbook_isbn to the end so
        # that we can use those fields in search_datalist
        fields = fields + ["textbook_author", "textbook_isbn", "cat_id"]

    result = get_table_list_data(
        ["marketplace_items", "marketplace_textbooks"], fields, attrs)

    if query != "":
        # filter by query
        result = search_datalist(fields, result, query)
        # take textbook_author, textbook_isbn, and cat_id (the last 3
        # columns) back out
        fields = fields[:-3]
        for i in range(len(result)):
            result[i] = result[i][:-3]

    (result, fields) = merge_titles(result, fields)

    sanitized_res = []
    links = []

    # Format the data, parsing the timestamps, converting the ids to actual
    # information, and adding links
    for item_listing in result:
        temp_res_row = []
        temp_link_row = []
        item_listing = list(item_listing)
        field_index = 0
        item_id = -1
        for data in item_listing:
            added_link = False
            if data == None:
                temp_res_row.append("")
            else:
                if fields[field_index] == "item_id":
                    # store the item_id (which will be the first item in each row
                    # [because we added it to the front of the fields list])
                    # so that we can use it to generate the links for each item
                    item_id = int(data)
                    temp_res_row.append(data)

                elif fields[field_index] == "item_timestamp":
                    temp_res_row.append(data.strftime("%m/%d/%y"))

                elif fields[field_index] == "user_id":
                    temp_link_row.append(
                        flask.url_for("core.get_members", user_id=int(data)))
                    # TODO: update when stalker is working
                    added_link = True

                    temp_res_row.append(get_name_from_user_id(int(data)))

                elif fields[field_index] == "textbook_edition":
                    temp_res_row.append(process_edition(data))

                elif fields[field_index] == "cat_id":
                    temp_res_row.append(get_category_name_from_id(int(data)))

                elif fields[field_index] == "item_title" or fields[field_index] == "textbook_title":
                    temp_link_row.append(
                        flask.url_for(".view_item", item_id=item_id))
                    added_link = True
                    temp_res_row.append(data)

                else:
                    temp_res_row.append(data)

            if not added_link:
                temp_link_row.append(0)
            field_index += 1

        # strip off the item_id column we added at the beginning of the function
        temp_res_row = temp_res_row[1:]
        temp_link_row = temp_link_row[1:]

        # add our temporary rows to the real 2d arrays that we'll return
        sanitized_res.append(temp_res_row)
        links.append(temp_link_row)

    fields = fields[
        1:]  # strip off the item_id column we added at the beginning

    headers = process_category_headers(fields)

    return (sanitized_res, headers, links)


def get_table_columns(tables):
    """
    Get all the columns in a table or tables.
    """
    # if there's only one table in the form of a string, we wrap it
    # in a list so that TABLE_NAME IN :tables works
    if type(tables) == str:
        tables = [tables]
    column_query = sqlalchemy.sql.select([
        sqlalchemy.text("COLUMN_NAME")
    ]).select_from(sqlalchemy.text("INFORMATION_SCHEMA.COLUMNS"))
    column_query = column_query.where(sqlalchemy.text("TABLE_NAME IN :tables"))
    columns_temp = list(flask.g.db.execute(column_query, tables=tuple(tables)))
    columns = []
    for field in columns_temp:
        columns += list(field)
    return columns


def get_table_list_data(tables, fields=None, attrs={}):
    """
    Queries the database (specifically, table <table>) and returns list of member data
    constrained by the specified attributes.

    Arguments:
        tables: The tables to query.  If it's only one, it can be just a string,
                but if it's more than one, it can be in a list, whereupon they will
                be <method>ed in order to query all of them at the same time.
        fields: The fields to return. If None specified, then default_fields
                are used.
        attrs:  The attributes of the members to filter for.
    Returns:
        result: The fields and corresponding values of members with desired
                attributes. In the form of a list of lists.
    """
    if type(tables) == str:
        tables = [tables]

    all_returnable_fields = get_table_columns(tables)

    if fields == None:
        fields = all_returnable_fields
    else:
        if any(f not in all_returnable_fields for f in fields):
            return "Invalid field"

    # have spaces around method to make the query work
    method = " NATURAL LEFT JOIN "
    # Build the SELECT and FROM clauses
    s = sqlalchemy.sql.select(fields).select_from(
        sqlalchemy.text(method.join(tables)))

    # Build the WHERE clause
    for key, value in list(attrs.items()):
        s = s.where(sqlalchemy.text(key + "= :" + key))

    # Execute the query
    result = flask.g.db.execute(s, attrs).fetchall()
    # Return the list of lists
    for i in range(len(result)):
        result[i] = list(result[i])
    return result


def merge_titles(datalist, fields):
    """
    Takes datalist and merges the two columns, item_title and textbook_title.

    Arguments:
        datalist: a 2d list of data, with columns determined by fields
        fields: the column titles from the SQL tables

    Returns:
        datalist: the original table, but with the two columns merged
        fields: the column titles similarly merged together into item_title
    """
    item_index = None
    textbook_index = None
    for i in range(len(fields)):
        if fields[i] == "item_title":
            item_index = i
        if fields[i] == "textbook_title":
            textbook_index = i

    if item_index is None or textbook_index is None:
        # can't merge, since the two columns aren't there
        return (datalist, fields)

    for row_index in range(len(datalist)):
        row = datalist[row_index]
        if row[item_index] == "":
            row[item_index] = row[textbook_index]
        del row[textbook_index]
        datalist[row_index] = row
    del fields[textbook_index]
    return (datalist, fields)


def process_category_headers(fields):
    """
    Converts fields from sql headers to English.

    Arguments:
        fields: the list of fields that will be changed into the headers that are returned

    Returns:
        headers: the list of headers that will become the headers of the tables
    """
    headers = []
    for i in fields:
        if i == "item_title":
            headers.append("Item")
        elif i == "item_price":
            headers.append("Price")
        elif i == "user_id":
            headers.append("Sold by")
        elif i == "item_timestamp":
            headers.append("Date")
        elif i == "textbook_title":
            headers.append("Title")
        elif i == "textbook_author":
            headers.append("Author")
        elif i == "textbook_edition":
            headers.append("Edition")
        elif i == "cat_id":
            headers.append("Category")
    return headers


def generate_hidden_form_elements(skip_fields):
    """
    Creates a list of names of parameters and values, gathered from flask.request.form, to be passed into sell_*.html.
    There, they will be turned into hidden form elements and passed into the request form.
    Some fields are skipped because including them would overwrite other fields.

    Arguments:
        skip_fields: The fields to skip.
    Returns:
        to_return: The list of parameters and values, in a 2d list where each row is of the form ["parameter", value]
    """
    parameters = [
        "cat_id", "item_title", "item_condition", "item_details", "item_price",
        "textbook_id", "textbook_edition", "textbook_isbn", "state"
    ]

    to_return = []
    for parameter in parameters:
        if parameter in skip_fields:
            continue
        if parameter in flask.request.form:
            to_return.append([parameter, flask.request.form[parameter]])

    if not "item_image" in skip_fields:
        if "item_image" in flask.request.form:
            for img in flask.request.form["item_image"]:
                to_return.append(["item_image[]", img])

    return to_return


def validate_data():
    """
    Validates the data submitted in the sell form.

    Returns:
        A list of all the validation errors; an empty list if no errors.
    """
    errors = []
    try:
        category_id = int(flask.request.form["cat_id"])
    except ValueError:
        # this should never happen through normal form use
        errors.append("Somehow the category got all messed up.")
        return errors

    cat_title = get_table_list_data(
        "marketplace_categories",
        fields=["cat_title"],
        attrs={"cat_id": category_id})
    if len(cat_title) == 0:
        # the category id doesn't correspond to any category
        errors.append("Somehow the category got all messed up.")
        return errors
    else:
        # 2d array to a single element
        # [["Furniture"]] -> "Furniture"
        cat_title = cat_title[0][0]

    if cat_title == "Textbooks":
        # regex to make sure the textbook edition is valid
        if "textbook_edition" in flask.request.form:
            edition_regex = "^([0-9]+|international)$"
            if re.match(edition_regex,
                        str(flask.request.form["textbook_edition"]),
                        re.IGNORECASE) == None:
                errors.append(
                    "Textbook edition is invalid. Try providing a number or 'International'."
                )

        # validate the isbn too, if it's present
        if "textbook_isbn" in flask.request.form and flask.request.form["textbook_isbn"] != "":
            if not validate_isbn(flask.request.form["textbook_isbn"]):
                errors.append(
                    "Textbook ISBN appears to be invalid. Please check that you typed it in correctly."
                )

    else:
        # just need to make sure the item_title exists
        if not "item_title" in flask.request.form or flask.request.form["item_title"] == "":
            errors.append("Item title cannot be empty.")

    # condition is mandatory
    if not "item_condition" in flask.request.form or flask.request.form["item_condition"] == "":
        errors.append("Item condition must be set.")

    # price must be present and valid
    if not "item_price" in flask.request.form or flask.request.form["item_price"] == "":
        errors.append("Price cannot be left blank.")
    else:
        price_regex = "^([0-9]{1,4}\.[0-9]{0,2}|[0-9]{1,4}|\.[0-9]{1,2})$"
        # matches prices of the form ****.**, ****, and .**
        # examples:
        # first capture group:
        # 123.98
        # 1234.9
        # 12.
        # second capture group:
        # 12
        # 123
        # third capture group:
        # .9
        # .98
        if re.match(price_regex, flask.request.form["item_price"]) == None:
            errors.append(
                "Price must be between 0 (inclusive) and 10,000 (exclusive) with at most 2 decimal places."
            )

    # TODO: image link verification

    return errors


def create_new_listing(stored):
    """
    Inserts into the database!

    Arguments:
        stored: a map with the info
    Returns:
        the item_id, or -1 if it fails
    """
    user_id = int(stored["user_id"])
    cat_id = int(stored["cat_id"])
    cat_title = stored["cat_title"]
    item_condition = stored["item_condition"]
    item_details = stored["item_details"]
    item_price = stored["item_price"]
    item_images = []
    #item_images = stored["item_images"] # TODO: images
    result = []
    if cat_title == "Textbooks":
        textbook_id = int(stored["textbook_id"])
        textbook_edition = stored["textbook_edition"]
        textbook_isbn = stored["textbook_isbn"].replace("-", "")
        query = sqlalchemy.sql.text("""INSERT INTO marketplace_items
                (user_id, cat_id, item_condition, item_details, item_price, textbook_id, textbook_edition, textbook_isbn)
                VALUES (:user_id, :cat_id, :item_condition, :item_details, :item_price, :textbook_id, :textbook_edition, :textbook_isbn)"""
                                    )
        result = flask.g.db.execute(
            query,
            user_id=user_id,
            cat_id=cat_id,
            item_condition=item_condition,
            item_details=item_details,
            item_price=item_price,
            textbook_id=textbook_id,
            textbook_edition=textbook_edition,
            textbook_isbn=textbook_isbn)
    else:
        item_title = stored["item_title"]
        query = sqlalchemy.sql.text(
            """INSERT INTO marketplace_items (user_id, cat_id, item_title, item_condition, item_details, item_price) VALUES (:user_id, :cat_id, :item_title, :item_condition, :item_details, :item_price)"""
        )
        result = flask.g.db.execute(
            query,
            user_id=user_id,
            cat_id=cat_id,
            item_title=item_title,
            item_condition=item_condition,
            item_details=item_details,
            item_price=item_price)

    query = sqlalchemy.sql.text("SELECT LAST_INSERT_ID()")
    result = list(flask.g.db.execute(query))
    item_id = -1
    if result[0][0] != 0:
        item_id = result[0][0]
    else:
        return -1

    # TODO: images
    """
    for image in item_images:
        query = sqlalchemy.sql.text(" ""INSERT INTO marketplace.images (item_id, img_link) VALUES (:item_id, :image);"" ")
        result = flask.g.db.execute(query, item_id=item_id, image=image)
    """
    return item_id


def search_datalist(fields, datalist, query):
    """
    Searches in datalist (which has columns denoted in fields) to
    create a new datalist, sorted first by relevance and then by date
    created.
    """
    # map column names to indices
    # we need to map item_title and category_title to the same index
    # because datalist has already been merged
    field_index_map = {}
    for i in range(len(fields)):
        field_index_map[fields[i]] = i
    # add a special column at the end: score
    field_index_map["score"] = len(fields)

    query_tokens = tokenize_query(query)
    perfect_matches = []
    imperfect_matches = []

    query_isbns = []
    # ISBNs instantly make listings a perfect match
    for token in query_tokens:
        if validate_isbn(token):
            query_isbns.append(token)

    for listing in datalist:
        item_tokens = []
        if get_category_name_from_id(
                listing[field_index_map["cat_id"]]) == "Textbooks":
            # if it's a textbook, include the author's name and the
            # book title in the item tokens
            item_tokens = tokenize_query(
                listing[field_index_map["textbook_title"]])
            item_tokens += tokenize_query(
                listing[field_index_map["textbook_author"]])
        else:
            # only include the item title
            item_tokens = tokenize_query(
                listing[field_index_map["item_title"]])

        # does the isbn match any of the query's isbns?
        is_isbn_match = False
        for isbn in query_isbns:
            if listing[field_index_map["textbook_isbn"]] == isbn:
                is_isbn_match = True

        score = get_matches(query_tokens, item_tokens)

        # if it's an isbn match, give it a perfect score as well
        # so that it doesn't get placed after all of the other perfect
        # matches
        if is_isbn_match:
            score = len(query_tokens)

        listing.append(score)
        if score == 0:
            continue

        if score == len(query_tokens):
            perfect_matches.append(listing)
        else:
            imperfect_matches.append(listing)

    search_results = []
    # if we have any perfect matches, don't include the imperfect ones
    if len(perfect_matches) > 0:
        search_results = perfect_matches
    else:
        search_results = imperfect_matches

    # define a custom comparison function to use in python's sort
    # -1 if item1 goes above item2, i.e. either item1's score is higher
    # or item1 was posted earlier.
    def compare(item1, item2):
        if item1[field_index_map["score"]] < item2[field_index_map["score"]]:
            return 1
        elif item1[field_index_map["score"]] > item2[field_index_map["score"]]:
            return -1
        # they have the same number of matches, so we sort by timestamp
        if item1[field_index_map["item_timestamp"]] < item2[field_index_map["item_timestamp"]]:
            return 1
        elif item1[field_index_map["item_timestamp"]] == item2[field_index_map[
                "item_timestamp"]]:
            return 0
        else:
            return -1

    search_results = sorted(search_results, cmp=compare)

    # chop off the last column, which holds the score
    for i in range(len(search_results)):
        search_results[i] = search_results[i][:-1]

    return search_results


def get_matches(l1, l2):
    """
    Returns the number of matches between list 1 and list 2.
    """
    if len(l1) < len(l2):
        return len([x for x in l1 if x in l2])
    else:
        return len([x for x in l2 if x in l1])


def tokenize_query(query):
    """
    Turns a string with a query into a list of tokens that represent the query.
    """
    tokens = []

    query = query.split()
    # Validate ISBNs before we remove hyphens
    for token_index in range(len(query)):
        token = query[token_index]
        if (validate_isbn(token)):
            tokens.append(token)
            del query[token_index]

    query = " ".join(query)
    # Remove punctuation
    punctuation = [",", ".", "-", "_", "!", ";", ":", "/", "\\"]
    for p in punctuation:
        query = query.replace(p, " ")
    query = query.split()

    # if any of the words in query are in our SKIP_WORDS, don't add them
    # to tokens
    for token in query:
        token = token.lower()
        if not token in SKIP_WORDS:
            tokens.append(token)

    return tokens


def validate_isbn(isbn):
    """
    Determines whether an ISBN is valid or not.  Works with ISBN-10 and ISBN-13,
    validating the length of the string and the check digit as well.

    Arguments:
        isbn: The ISBN, in the form of a string.
    Returns:
        valid: Whether or not the isbn is valid (a boolean).
    """
    if type(isbn) != str:
        return False

    # hyphens are annoying but there should never be one at start or end,
    # nor should there be two in a row.
    if isbn[0] == "-" or isbn[-1] == "-" or "--" in isbn:
        return False

    # now that we've done that we can remove them
    isbn.replace("-", "")

    # regexes shamelessly copypasted
    # the ISBN-10 can have an x at the end (but the ISBN-13 can't)
    if re.match("^[0-9]{9}[0-9x]$", isbn, re.IGNORECASE) != None:
        return True
    elif re.match("^[0-9]{13}$", isbn, re.IGNORECASE) != None:
        return True
    return False


def process_edition(edition):
    """
    Turns a string with an edition in it into a processed string.
    Turns "1.0" into "1st", "2017.0" into "2017", and "International"
    into "International".  So it doesn't do a whole lot, but what it
    does do, it does well.

    Arguments:
        edition: The edition string.
    Returns:
        edition: The processed edition string.
    """

    try:
        edition = int(edition)
        if edition < 1000:
            # it's probably an edition, not a year

            # if the tens digit is 1, it's always "th"
            if (edition / 10) % 10 == 1:
                return str(edition) + "th"
            if edition % 10 == 1:
                return str(edition) + "st"
            if edition % 10 == 2:
                return str(edition) + "nd"
            if edition % 10 == 3:
                return str(edition) + "rd"
            return str(edition) + "th"
        else:
            return str(edition)
    except ValueError:
        return edition


def add_textbook(title, author):
    """
    Adds a textbook to the database, with title <title> and author
    <author>.

    Arguments:
        title: The title.
        author: The author.

    Returns:
        True if the insert succeeds, and False if not (the textbook
        already exists)
    """
    # check if the textbook exists
    query = sqlalchemy.sql.select("1").select_from("marketplace_textbooks")
    query = query.where(sqlalchemy.text("textbook_title = :title"))
    query = query.where(sqlalchemy.text("textbook_author = :author"))
    result = list(flask.g.db.execute(query, title=title, author=author))
    if len(result) != 0:
        # the textbook already exists
        return False

    query = sqlalchemy.sql.text("""INSERT INTO marketplace_textbooks
            (textbook_title, textbook_author) VALUES (:title,
            :author)""")
    flask.g.db.execute(query, title=title, author=author)
    return True


def get_name_from_user_id(user_id):
    """
    Queries the database and returns the full name (first and last) of the user with the specified user id (NOT UID).

    Arguments:
        user_id: The user id of the requested user (NOT UID).
    Returns:
        result: A string of the user's full name.
                (first + " " + last)
    """
    query = sqlalchemy.text(
        """SELECT full_name FROM members_full_name WHERE user_id=:user_id""")
    result = flask.g.db.execute(query, user_id=user_id).first()
    if result == None:
        return None
    return result[0]


def get_textbook_info_from_textbook_id(textbook_id):
    """
    Queries the database and returns the title and author of the textbook with the specified id.

    Arguments:
        textbok_id: The id of the requested textbook.
    Returns:
        result: A list of the textbook title and author.
    """
    query = sqlalchemy.text(
        """SELECT textbook_title, textbook_author FROM marketplace_textbooks WHERE textbook_id=:textbook_id"""
    )
    result = flask.g.db.execute(query, textbook_id=textbook_id).first()
    if result == None:
        return None
    return list(result)


def get_category_name_from_id(cat_id):
    """
    Queries the database and returns the name of the category with the specified id.

    Arguments:
        cat_id: The id of the requested category.
    Returns:
        result: A string with the name of the category.
    """
    query = sqlalchemy.text(
        """SELECT cat_title FROM marketplace_categories WHERE cat_id=:cat_id"""
    )
    result = flask.g.db.execute(query, cat_id=cat_id).first()
    if result == None:
        return None
    return result[0]