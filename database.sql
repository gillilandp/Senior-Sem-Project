PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS users;

-- user table
CREATE TABLE users ( 
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL UNIQUE,
    user_password_hash VARCHAR(255) NOT NULL,   
    display_name VARCHAR(255) NOT NULL,
    zip_code VARCHAR(10) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);  

-- dietary restrictions table
CREATE TABLE dietary_restrictions (
    restriction_id INT AUTO_INCREMENT PRIMARY KEY,
    restriction_name VARCHAR(255) NOT NULL UNIQUE,
    category VARCHAR(255) NOT NULL CHECK (category IN ('allergy', 'medical', 'lifestyle', 'other'))  
);

-- table that links user to dietary restcrictions
CREATE TABLE user_dietary_restrictions (
    user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    restriction_id INT REFERENCES dietary_restrictions(restriction_id) ON DELETE CASCADE,
    severity VARCHAR(255) NOT NULL CHECK 9severity IN ('mild', 'moderate', 'severe')),
    PRIMARY KEY (user_id, restriction_id)
    FOREIGN KEY (user_email) REFERENCES users(user_email) ON DELETE CASCADE,
    FOREIGN KEY (restriction_id) REFERENCES dietary_restrictions(restriction_id) ON DELETE CASCADE
);

-- ingredients table
CREATE TABLE ingredients (
    ingredient_id INT AUTO_INCREMENT PRIMARY KEY,
    ingredient_name VARCHAR(255) NOT NULL UNIQUE,
    category VARCHAR(255) NOT NULL CHECK (category IN ('vegetable', 'fruit', 'grain', 'protein', 'dairy', 'spice', 'other'))
);

-- table that links ingredients to dietary restrictions
CREATE TABLE ingredient_dietary_restrictions (
    ingredient_id INT REFERENCES ingredients(ingredient_id) ON DELETE CASCADE,
    restriction_id INT REFERENCES dietary_restrictions(restriction_id) ON DELETE CASCADE,
    PRIMARY KEY (ingredient_id, restriction_id)
);

-- recipe table
CREATE TABLE recipes (
    recipe_id INT AUTO_INCREMENT PRIMARY KEY,
    recipe_name VARCHAR(255) NOT NULL,
    instructions TEXT NOT NULL,
    created_by INT REFERENCES users(user_id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    source_url VARCHAR(255)
);

-- table that links recipes to ingredients
CREATE TABLE recipe_ingredients (
    recipe_id INT REFERENCES recipes(recipe_id) ON DELETE CASCADE,
    ingredient_id INT REFERENCES ingredients(ingredient_id) ON DELETE CASCADE,
    quantity VARCHAR(255) NOT NULL,
    PRIMARY KEY (recipe_id, ingredient_id)
);  

-- brands table
CREATE TABLE brands (
    brand_id INT AUTO_INCREMENT PRIMARY KEY,
    brand_name VARCHAR(255) NOT NULL UNIQUE,
    website_url VARCHAR(255)
);  

-- products table
CREATE TABLE products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    brand_id INT REFERENCES brands(brand_id) ON DELETE SET NULL,
    ingredients TEXT NOT NULL,
    nutrition_facts TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- table that links products to dietary restrictions
CREATE TABLE product_dietary_restrictions (
    product_id INT REFERENCES products(product_id) ON DELETE CASCADE,
    restriction_id INT REFERENCES dietary_restrictions(restriction_id) ON DELETE CASCADE,
    PRIMARY KEY (product_id, restriction_id)
);  

-- restaurant/grocery store table
CREATE TABLE establishments (
    establishment_id INT AUTO_INCREMENT PRIMARY KEY,
    establishment_name VARCHAR(255) NOT NULL,
    establishment_type VARCHAR(255) NOT NULL CHECK (establishment_type IN ('restaurant', 'grocery store', 'other')),
    address VARCHAR(255) NOT NULL,
    city VARCHAR(255) NOT NULL,
    state VARCHAR(255) NOT NULL,
    zip_code VARCHAR(10) NOT NULL,
    phone_number VARCHAR(20),
    website_url VARCHAR(255)
);  




