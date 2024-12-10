DROP TABLE IF EXISTS pets;
CREATE TABLE pets (
    """
    this is the template used in meal_max, we can to figure out the 
    parameters of cat_curious, then we can create the the db table
    """
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    breed TEXT NOT NULL,
    age REAL NOT NULL,
    weight REAL NOT NULL
);