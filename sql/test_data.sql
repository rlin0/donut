/* Test data / initial data */
INSERT INTO buildings(building_id, building_name) VALUES
    (1, 'Ruddock House');
INSERT INTO options(option_id, option_name) VALUES
    (1, 'CS'),
    (2, 'MechE');

INSERT INTO members(uid, last_name, first_name, email, phone) VALUES
    ('1957540', 'Qu', 'David', 'davidqu12345@gmail.com', NULL),
    ('1984853', 'Eng', 'Robert', 'reng@caltech.edu', '+11234567890');
INSERT INTO members(
    user_id,
    uid,
    last_name,
    first_name,
    preferred_name,
    middle_name,
    email,
    phone,
    gender,
    gender_custom,
    birthday,
    entry_year,
    graduation_year,
    msc,
    city,
    state,
    building_id,
    room
) VALUES (
    3,
    '2078141',
    'Sander',
    'Caleb',
    'Cleb',
    'Caldwell',
    'csander@caltech.edu',
    '6178003347',
    0,
    'Male',
    '1999-05-08',
    2017,
    2021,
    707,
    'Lincoln',
    'MA',
    1,
    '203'
);

INSERT INTO member_options(user_id, option_id, option_type) VALUES
    (3, 1, 'Major'),
    (3, 2, 'Minor');

INSERT INTO images(user_id, extension, image) VALUES
    (3, 'png', 'NOT_A_REAL_IMAGE');

INSERT INTO marketplace_categories(cat_title, cat_order) VALUES
    ('Furniture', 1),
    ('Textbooks', 2);

INSERT INTO marketplace_items(cat_id, user_id, item_title, item_details, item_condition, item_price) VALUES
    (1, 1, 'A table', "It\'s a pretty cool table, I guess", 'Good', 5.99);

INSERT INTO users(user_id, username) VALUES
    (1, "dqu"),
    (2, "reng"),
    (3, "csander");

INSERT INTO groups(group_id, group_name, type) VALUES
    (1, 'Donut Devteam', ''),
    (2, 'Ruddock House', 'house');

INSERT INTO group_members(user_id, group_id) VALUES
    (1, 1),
    (2, 1);

INSERT INTO positions(group_id, pos_id, pos_name) VALUES
    (1, 1, 'Head'),
    (1, 2, 'Secretary'),
    (2, 3, 'Full Member');

INSERT INTO position_holders(group_id, pos_id, user_id) VALUES
    (1, 1, 1),
    (1, 1, 2),
    (2, 3, 3);

INSERT INTO rooms(room_id, location, title, description) VALUES
    (1, 'SAC 23', 'ASCIT Screening Room', 'A room for watching DVDs and videos');
