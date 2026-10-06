# sqlite in flask routes 
import sqlite3
from flask import g

DATABASE = '/path/to/database.sb' # route to database file

def get_db(): # function to get database connection
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext # function to close database connection
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/users')
def index():
    cur = get_db().cursor()
    cur.execute("SELECT * FROM users")
    users = cur.fetchall()
    return str(users)   