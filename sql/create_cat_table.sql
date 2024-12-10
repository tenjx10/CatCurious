DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    salt TEXT NOT NULL,
    password TEXT NOT NULL,
    deleted BOOLEAN DEFAULT FALSE,
    UNIQUE(artist, title, year)
);