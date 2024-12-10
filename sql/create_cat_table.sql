DROP TABLE IF EXISTS cats;
CREATE TABLE cats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    breed TEXT NOT NULL,
    age INTEGER NOT NULL CHECK(age >= 0),
    weight REAL NOT NULL CHECK(weight > 0),
    affection_level INTEGER,
    description TEXT,
    deleted BOOLEAN DEFAULT FALSE
);