-- code to call database 

DROP TABLE IF EXISTS users;

-- user table
CREATE TABLE users ( 
    user_email VARCHAR(255) NOT NULL PRIMARY KEY,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
);  

-- dietary restrictions table
CREATE TABLE dietary_restrictions (
    restriction_id INT AUTO_INCREMENT PRIMARY KEY,
    restriction_name VARCHAR(255) NOT NULL UNIQUE   
)

-- table that links user to dietary restcrictions
CREATE TABLE user_dietary_restrictions (
    user_email VARCHAR(255) NOT NULL,
    restriction_id INT NOT NULL,
    PRIMARY KEY (user_email, restriction_id),
    FOREIGN KEY (user_email) REFERENCES users(user_email) ON DELETE CASCADE,
    FOREIGN KEY (restriction_id) REFERENCES dietary_restrictions(restriction_id) ON DELETE CASCADE
);

