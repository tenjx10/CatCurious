DROP TABLE IF EXISTS pets;
CREATE TABLE pets (
    """
    this is the template used in meal_max, we can to figure out the 
    parameters of cat_curious, then we can create the the db table
    """


    """
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meal TEXT NOT NULL UNIQUE,
    cuisine TEXT NOT NULL,
    price REAL NOT NULL,
    difficulty TEXT CHECK(difficulty IN ('HIGH', 'MED', 'LOW')),
    battles INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    deleted BOOLEAN DEFAULT FALSE
    """
);