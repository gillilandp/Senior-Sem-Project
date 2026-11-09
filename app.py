import gzip
import json
import os
import random
import re
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from urllib import response

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)
import requests
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
DB_NAME = 'safeplate.db'

login_manager = LoginManager(app)
login_manager.login_view = 'login'


# Function to get a connection to the SQLite3 database
def get_db_connection():
    """Establish a connection to the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    # Help convert query results to dictionary-like objects
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create database tables if they do not exist."""
    conn = get_db_connection()

    # User table with first_name and last_name
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            first_name TEXT,
            last_name TEXT
        )
    """)

    # Dietary profile table with all fields
    conn.execute("""
        CREATE TABLE IF NOT EXISTS dietary_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            restrictions TEXT,
            ingredients_to_avoid TEXT,
            dietary_notes TEXT,
            FOREIGN KEY (user_id) REFERENCES user(id)
        )
    """)

    # Grocery products table (dùng lưu dữ liệu Open Food Facts)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS grocery_products (
            code TEXT PRIMARY KEY,
            product_name TEXT,
            brands TEXT,
            allergens_tags TEXT,
            labels_tags TEXT,
            image_url TEXT
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_grocery_name ON"
        " grocery_products(product_name);"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_grocery_brands ON"
        " grocery_products(brands);"
    )

    try:
        with open("database.sql", "r", encoding="utf-8") as f:
            conn.executescript(f.read())
    except Exception as e:
        print(f"Note: Error or notice while executing database.sql: {e}")

    conn.commit()
    conn.close()


# User Information Table in the Database
class User(UserMixin):

    def __init__(self, id, email, password, first_name="", last_name=""):
        self.id = id
        self.email = email
        self.password = password
        self.first_name = first_name or ""
        self.last_name = last_name or ""


@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM user WHERE id = ?", (int(user_id),)
    ).fetchone()
    conn.close()
    if user:
        return User(
            id=user["id"],
            email=user["email"],
            password=user["password"],
            first_name=user["first_name"] if "first_name" in user.keys() else "",
            last_name=user["last_name"] if "last_name" in user.keys() else "",
        )
    return None


# Rank for recipes based on their tags
def get_cooking_label(instructions_input):
    """Automatically determine the length/complexity label based on the total word count of the instructions.

    The input can be the raw text string or a list of cleaned step sentences.
    """
    if isinstance(instructions_input, list):
        full_text = " ".join(instructions_input)
    else:
        full_text = str(instructions_input or "")

    word_count = len(full_text.split())

    if word_count < 60:
        return "Quick and Easy"
    elif word_count <= 100:
        return "Standard Cooking"
    else:
        return "Home cooked Special (Longer Recipe)"


# Rank for recipes based on their ingredients
def get_prep_label(meal_or_ingredients):
    """Determine the preparation level based on the ingredient count.

    The input can be a 'meal' dictionary from an API or a list of ingredients.
    """
    if isinstance(meal_or_ingredients, list):
        count = len(meal_or_ingredients)
    elif isinstance(meal_or_ingredients, dict):
        count = 0
        for i in range(1, 21):
            ing = meal_or_ingredients.get(f"strIngredient{i}")
            if ing and ing.strip():
                count += 1
    else:
        count = 0

    if count <= 6:
        return "Easy to prepare"
    elif count <= 11:
        return "Standard to prepare"
    else:
        return "Hard to prepare"


def get_flag_emoji(country_code):
    """Change code name of countries 'VN', 'IE' become flag Emoji ."""
    if not country_code or len(country_code) != 2:
        return "🌐"
    return chr(127397 + ord(country_code[0].upper())) + chr(
        127397 + ord(country_code[1].upper())
    )


# Take the list of country from safeplate.DB
def get_countries_from_db():
    """Retrieve a list of countries, including flag information, from the 'areas_cache' table in SQLite."""
    conn = get_db_connection()
    try:
        rows = conn.execute("SELECT * FROM available_countries_view").fetchall()
    except Exception as e:
        print(f"Error executing view: {e}")
        rows = []
    conn.close()

    countries = {}
    for row in rows:
        countries[row["area_name"]] = {
            "code": row["country_code"],
            "name": row["country_name"],
            "flag_url": row["flag_url"],
            "emoji": get_flag_emoji(row["country_code"]),
        }
    return countries


# 1. main.html
@app.route("/")
def home():
    recipes = []
    try:
        conn = get_db_connection()
        rows = conn.execute(
            "SELECT raw_data FROM recipe_cache ORDER BY RANDOM() LIMIT 8"
        ).fetchall()
        conn.close()

        for row in rows:
            meal = json.loads(row["raw_data"])
            raw_tags = meal.get("strTags")
            tags_list = (
                raw_tags.split(",")
                if raw_tags
                else [meal.get("strCategory", "SAFE")]
            )
            raw_instructions = meal.get("strInstructions", "")

            recipes.append({
                "id": meal.get("idMeal"),
                "idMeal": meal.get("idMeal"),
                "name": meal.get("strMeal"),
                "category": meal.get("strCategory"),
                "area": meal.get("strArea"),
                "image": meal.get("strMealThumb"),
                "cooktime": get_cooking_label(raw_instructions),
                "prep_label": get_prep_label(meal),
                "tags": tags_list,
            })
    except Exception as e:
        print(f"Error loading home recipes: {e}")

    diet_info = {}
    diet_ingredients = {}

    info_path = os.path.join(app.static_folder, "diet_info.json")
    if os.path.exists(info_path):
        with open(info_path, "r", encoding="utf-8") as f:
            diet_info = json.load(f)

    ingredients_path = os.path.join(app.static_folder, "diet_ingredients.json")
    if os.path.exists(ingredients_path):
        with open(ingredients_path, "r", encoding="utf-8") as f:
            diet_ingredients = json.load(f)

    return render_template(
        "main.html",
        recipes=recipes,
        diet_info=diet_info,
        diet_ingredients=diet_ingredients,
    )


# 2. Processing Register
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()

        conn = get_db_connection()

        user_exists = conn.execute(
            "SELECT * FROM user WHERE email = ?", (email,)
        ).fetchone()
        if user_exists:
            conn.close()
            return "Email this has already been used!"

        hashed_password = generate_password_hash(password, method="scrypt")
        conn.execute(
            "INSERT INTO user (email, password, first_name, last_name) VALUES"
            " (?, ?, ?, ?)",
            (email, hashed_password, first_name, last_name),
        )
        conn.commit()
        conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")


# 3. Processing Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM user WHERE email = ?", (email,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            user_obj = User(
                id=user["id"],
                email=user["email"],
                password=user["password"],
                first_name=(
                    user["first_name"] if "first_name" in user.keys() else ""
                ),
                last_name=(
                    user["last_name"] if "last_name" in user.keys() else ""
                ),
            )
            login_user(user_obj)
            return redirect(url_for("home"))
        else:
            return "Invalid email or password!"

    return render_template("login.html")


# 4. Forgot Password
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        return f"Sent password reset instructions to email: {email}"
    return render_template("forgot_password.html")


# 5. Log out
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


# Search Recipes
@app.route("/recipes", methods=["GET"])
def search_recipes():
    keyword = request.args.get("keyword", "").strip()
    category_filter = request.args.get("category", "").strip()
    selected_diets = request.args.getlist("diet")
    selected_diets = [diet for diet in selected_diets if diet != "all"]
    prep_filter = request.args.get("prep", "").strip()
    type_filter = request.args.get("type", "").strip()
    match_profile = request.args.get("match_profile", "false").strip()
    page = int(request.args.get("page", 1))
    limit = 15

    offset = (page - 1) * limit

    conn = get_db_connection()

    user_restrictions = []
    user_avoid_ingredients = []

    if match_profile == "true" and current_user.is_authenticated:
        profile = conn.execute(
            "SELECT * FROM dietary_profile WHERE user_id = ?",
            (current_user.id,),
        ).fetchone()

        if profile:
            if profile["restrictions"]:
                user_restrictions = [
                    restriction.strip()
                    for restriction in profile["restrictions"].split(",")
                    if restriction.strip()
                ]
                for restriction in user_restrictions:
                    if restriction not in selected_diets:
                        selected_diets.append(restriction)
            if (
                "ingredients_to_avoid" in profile.keys()
                and profile["ingredients_to_avoid"]
            ):
                user_avoid_ingredients = [
                    i.strip().lower()
                    for i in profile["ingredients_to_avoid"].split(",")
                    if i.strip()
                ]

    conditions = []
    params = []

    if keyword:
        conditions.append("LOWER(name) LIKE ?")
        params.append(f"%{keyword.lower()}%")
    if category_filter:
        conditions.append("LOWER(category) = ?")
        params.append(category_filter.lower())

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

    data_query = f"SELECT raw_data, dietary_tags FROM recipe_cache{where_clause}"
    rows = conn.execute(data_query, params).fetchall()
    conn.close()

    filtered_meals = []
    for row in rows:
        meal = json.loads(row["raw_data"])
        cook_label = get_cooking_label(meal.get("strInstructions", ""))
        prep_label = get_prep_label(meal)
        meal_tags = (row["dietary_tags"] or "").lower()

        if prep_filter == "minimal" and prep_label != "Easy to prepare":
            continue
        if prep_filter == "standard" and prep_label != "Standard to prepare":
            continue
        if prep_filter == "complex" and prep_label != "Hard to prepare":
            continue

        if type_filter == "quick" and cook_label != "Quick and Easy":
            continue
        if type_filter == "standard" and cook_label != "Standard Cooking":
            continue
        if (
            type_filter == "detailed"
            and cook_label != "Home cooked Special (Longer Recipe)"
        ):
            continue

        if match_profile == "true" and current_user.is_authenticated:
            meal_ingredients_list = []
            for i in range(1, 21):
                ing = meal.get(f"strIngredient{i}")
                if ing and ing.strip():
                    meal_ingredients_list.append(ing.strip().lower())
            meal_ingredients_text = " ".join(meal_ingredients_list)

            if user_restrictions:
                has_all_profile_restrictions = all(
                    restriction.lower() in meal_tags
                    for restriction in user_restrictions
                )
                if not has_all_profile_restrictions:
                    continue

            if user_avoid_ingredients:
                has_avoided_ingredients = any(
                    ingredient in meal_ingredients_text
                    for ingredient in user_avoid_ingredients
                )
                if has_avoided_ingredients:
                    continue

        elif selected_diets:
            meal_tags = (row["dietary_tags"] or "").lower()
            has_all_selected_diets = all(
                diet.lower() in meal_tags for diet in selected_diets
            )
            if not has_all_selected_diets:
                continue

        meal["cook_label"] = cook_label
        meal["prep_label"] = prep_label
        filtered_meals.append(meal)

    total_count = len(filtered_meals)
    meals = filtered_meals[offset : offset + limit]
    has_more = total_count > (offset + limit)

    countries = get_countries_from_db()

    return render_template(
        "recipes.html",
        meals=meals,
        countries=countries,
        selected_diets=selected_diets,
        match_profile=match_profile,
        page=page,
        has_more=has_more,
        total_count=total_count,
    )


# Recipe Detail
@app.route("/recipe/<meal_id>")
def recipe_detail(meal_id):
    try:
        conn = get_db_connection()
        row = conn.execute(
            "SELECT raw_data FROM recipe_cache WHERE meal_id = ?", (meal_id,)
        ).fetchone()
        conn.close()

        if not row:
            return redirect(url_for("search_recipes"))

        meal = json.loads(row["raw_data"])

        ingredients = []
        for i in range(1, 21):
            ingredient = meal.get(f"strIngredient{i}")
            measure = meal.get(f"strMeasure{i}")
            if ingredient and ingredient.strip():
                ingredients.append({
                    "name": ingredient.strip(),
                    "measure": measure.strip() if measure else "",
                })

        raw_instructions = meal.get("strInstructions", "")
        lines = (
            raw_instructions.split("\r\n")
            if "\r\n" in raw_instructions
            else raw_instructions.split("\n")
        )
        cleaned_steps = []
        pro_tips = []
        is_tip_section = False

        for line in lines:
            text = line.strip()
            if not text:
                continue

            if re.match(r"^(pro\s*tips?:?|notes?:?|tips?:?)$", text, re.IGNORECASE):
                is_tip_section = True
                continue

            if is_tip_section:
                cleaned_tip = re.sub(r"^[\*\-\d\.]+\s*", "", text).strip()
                if cleaned_tip:
                    pro_tips.append(cleaned_tip)
                continue

            if re.match(r"^(step\s*\d+:?|\d+\.?)$", text, re.IGNORECASE):
                continue

            text = re.sub(
                r"^(step\s*\d+:?|\d+[\.\)]\s*)", "", text, flags=re.IGNORECASE
            ).strip()
            if text:
                cleaned_steps.append(text)

        cook_label = get_cooking_label(cleaned_steps)
        prep_label = get_prep_label(ingredients)

        return render_template(
            "recipeDetails.html",
            meal=meal,
            ingredients=ingredients,
            instructions=cleaned_steps,
            pro_tips=pro_tips,
            cook_label=cook_label,
            prep_label=prep_label,
        )
    except Exception as e:
        print(f"Error fetching recipe details: {e}")

    return redirect(url_for("search_recipes"))


# Recipes by Flag
@app.route("/recipes/flag")
def recipes_by_flag():
    selected_area = request.args.get("area", "Canadian").strip()
    page = int(request.args.get("page", 1))
    limit = 15
    fetch_limit = page * limit
    offset = 0
    meals = []

    countries = get_countries_from_db()
    country_info = countries.get(selected_area, {})
    search_name = country_info.get("name", selected_area)

    try:
        conn = get_db_connection()
        if selected_area.lower() == "international":
            total_count = conn.execute("""
                SELECT COUNT(*) FROM recipe_cache 
                WHERE area IS NULL OR area = '' OR area = 'Unknown' OR area = 'International'
            """).fetchone()[0]

            rows = conn.execute(
                """
                SELECT raw_data, dietary_tags FROM recipe_cache 
                WHERE area IS NULL OR area = '' OR area = 'Unknown' OR area = 'International'
                LIMIT ? OFFSET ?
            """,
                (fetch_limit + 1, offset),
            ).fetchall()
        else:
            total_count = conn.execute(
                """
                SELECT COUNT(*) FROM recipe_cache 
                WHERE area LIKE ? OR area LIKE ?
            """,
                (f"%{selected_area}%", f"%{search_name}%"),
            ).fetchone()[0]

            rows = conn.execute(
                """
                SELECT raw_data, dietary_tags FROM recipe_cache
                WHERE area LIKE ? OR area LIKE ?
                LIMIT ? OFFSET ?
            """,
                (f"%{selected_area}%", f"%{search_name}%", fetch_limit + 1, offset),
            ).fetchall()

        conn.close()

        has_more = len(rows) > fetch_limit
        display_rows = rows[:fetch_limit]

        for row in display_rows:
            meal_data = json.loads(row["raw_data"])
            raw_instructions = meal_data.get("strInstructions", "")
            meal_data["cook_label"] = get_cooking_label(raw_instructions)
            meal_data["prep_label"] = get_prep_label(meal_data)
            meals.append(meal_data)
    except Exception as e:
        print(f"Error fetching area meals from DB: {e}")
        has_more = False
        total_count = 0

    return render_template(
        "recipesFlag.html",
        meals=meals,
        countries=countries,
        selected_area=selected_area,
        page=page,
        has_more=has_more,
        total_count=total_count,
    )


# Dietary Profile
@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    DIET_CATEGORIES = {
        "Dietary Lifestyle": ["Vegetarian", "Vegan"],
        "Religious & Health": ["Halal", "Kosher", "Low-Sodium"],
        "Allergens": [
            "Dairy-Free",
            "Gluten-Free",
            "Wheat-Free",
            "Nut-Free",
            "Soy-Free",
            "Egg-Free",
            "Sesame-Free",
        ],
        "Meat Restrictions": [
            "Fish-Free",
            "Shellfish-Free",
            "No Pork",
            "No Beef",
        ],
    }

    restrictions_list = [
        tag for tags in DIET_CATEGORIES.values() for tag in tags
    ]

    conn = get_db_connection()

    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()

        selected = request.form.getlist("restrictions")
        selected = [r for r in selected if r in restrictions_list]

        restrictions_string = ",".join(selected)

        ingredients_to_avoid = request.form.get(
            "ingredients_to_avoid", ""
        ).strip()
        dietary_notes = request.form.get("dietary_notes", "").strip()

        if first_name or last_name:
            conn.execute(
                """
                UPDATE user
                SET first_name = ?, last_name = ?
                WHERE id = ?
            """,
                (first_name, last_name, current_user.id),
            )

        conn.execute(
            """
            INSERT INTO dietary_profile (
                user_id,
                restrictions,
                ingredients_to_avoid,
                dietary_notes
            )
            VALUES (?, ?, ?, ?)

            ON CONFLICT(user_id)
            DO UPDATE SET
                restrictions = excluded.restrictions,
                ingredients_to_avoid = excluded.ingredients_to_avoid,
                dietary_notes = excluded.dietary_notes
        """,
            (
                current_user.id,
                restrictions_string,
                ingredients_to_avoid,
                dietary_notes,
            ),
        )

        conn.commit()
        conn.close()

        flash("Your profile has been updated successfully!", "success")
        return redirect(url_for("profile"))

    user = conn.execute(
        """
        SELECT first_name, last_name, email
        FROM user
        WHERE id = ?
    """,
        (current_user.id,),
    ).fetchone()

    saved_profile = conn.execute(
        """
        SELECT restrictions, ingredients_to_avoid, dietary_notes
        FROM dietary_profile
        WHERE user_id = ?
    """,
        (current_user.id,),
    ).fetchone()

    conn.close()

    selected_restrictions = []
    ingredients_to_avoid = ""
    dietary_notes = ""

    if saved_profile:
        if (
            "restrictions" in saved_profile.keys()
            and saved_profile["restrictions"]
        ):
            selected_restrictions = saved_profile["restrictions"].split(",")

        if "ingredients_to_avoid" in saved_profile.keys():
            ingredients_to_avoid = saved_profile["ingredients_to_avoid"] or ""

        if "dietary_notes" in saved_profile.keys():
            dietary_notes = saved_profile["dietary_notes"] or ""

    return render_template(
        "profile.html",
        restrictions_list=restrictions_list,
        selected_restrictions=selected_restrictions,
        first_name=(
            user["first_name"] if user and "first_name" in user.keys() else ""
        ),
        last_name=(
            user["last_name"] if user and "last_name" in user.keys() else ""
        ),
        email=user["email"] if user else "",
        ingredients_to_avoid=ingredients_to_avoid,
        dietary_notes=dietary_notes,
    )


# Watch ingredients for Diet
@app.route("/diet-ingredients/<diet_name>")
def diet_ingredients_detail(diet_name):
    diet_ingredients = {}

    ingredients_path = os.path.join(app.static_folder, "diet_ingredients.json")
    if os.path.exists(ingredients_path):
        with open(ingredients_path, "r", encoding="utf-8") as f:
            diet_ingredients = json.load(f)

    ingredients_list = diet_ingredients.get(diet_name, [])

    return render_template(
        "dietIngredients.html",
        diet_name=diet_name,
        ingredients=ingredients_list,
    )


# 6. Grocery Search (read from SQLite safeplate.db)
@app.route("/grocery")
def grocery_search():
    query = request.args.get("q", "").strip()
    products = []

    conn = get_db_connection()
    cursor = conn.cursor()

    if query:
        # Search for products by product name or brand in SQLite
        db_rows = cursor.execute(
            """
            SELECT code, product_name, brands, allergens_tags AS allergens, labels_tags AS labels, image_url
            FROM grocery_products
            WHERE product_name LIKE ? OR brands LIKE ?
            LIMIT 50
        """,
            (f"%{query}%", f"%{query}%"),
        ).fetchall()
    else:
        # If no search query, display 24 sample products with images by default
        db_rows = cursor.execute(
            """
            SELECT code, product_name, brands, allergens_tags AS allergens, labels_tags AS labels, image_url
            FROM grocery_products
            WHERE image_url != '' AND image_url IS NOT NULL
            LIMIT 24
        """
        ).fetchall()

    conn.close()

    for row in db_rows:
        products.append(dict(row))

    return render_template("grocery.html", products=products, query=query)


if __name__ == "__main__":
    init_db()  # Automatically create tables & indexes if they don't exist
    app.run(debug=True)