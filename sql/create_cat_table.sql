DROP TABLE IF EXISTS cats;
CREATE TABLE cats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    breed TEXT NOT NULL,
    age INTEGER NOT NULL CHECK(year >= 0),
    weight INTEGER NOT NULL CHECK(year > 0),
    deleted BOOLEAN DEFAULT FALSE,
    UNIQUE(artist, title, year)
);