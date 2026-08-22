-- Reference schema for the CampusEats SQLite database
-- (app.py creates these automatically via init_db(), this file is just
--  for documentation / manual inspection with a SQLite client)

CREATE TABLE menu_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    image_url TEXT,
    category TEXT DEFAULT 'Snacks',
    veg INTEGER DEFAULT 1,
    available INTEGER DEFAULT 1
);

-- One row per order. Which dishes were ordered now lives in order_items,
-- so a single order can hold several different items instead of just one.
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name TEXT NOT NULL,
    hostel_block TEXT NOT NULL,
    time_slot TEXT NOT NULL,
    status TEXT DEFAULT 'Placed',
    est_time INTEGER DEFAULT 10,
    orders_ahead INTEGER DEFAULT 3,
    created_at TEXT
);

-- Line items for each order (the actual food-item + quantity + price pairs).
CREATE TABLE order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    item_name TEXT NOT NULL,
    quantity INTEGER DEFAULT 1,
    price REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders (id)
);
