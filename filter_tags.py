
import sqlite3
import json
import re

DB_NAME = 'safeplate.db'


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def contains_any(ingredients, keywords):
    """Check keywords against individual ingredients using word boundaries."""
    for ingredient in ingredients:
        for keyword in keywords:
            pattern = r'(?<![a-z0-9])' + re.escape(keyword.lower()) + r'(?![a-z0-9])'
            if re.search(pattern, ingredient):
                return True
    return False


def check_dietary_labels(meal):
    """Classify dietary labels based on recipe ingredients."""

    # 1. Collect and normalize ingredients
    ingredients = []

    for i in range(1, 21):
        ing = meal.get(f'strIngredient{i}')

        if ing and ing.strip():
            ingredients.append(ing.strip().lower())

    category = (meal.get('strCategory') or '').strip().lower()

    labels = []

    # 2. Meat and animal-derived ingredients
    meat_keywords = [
        'chicken', 'beef', 'pork', 'lamb', 'bacon',
        'fish', 'salmon', 'tuna', 'turkey', 'duck',
        'meat', 'sausage', 'sausages', 'prosciutto',
        'ham', 'parma ham', 'chorizo', 'doner meat',
        'anchovies', 'mackerel', 'sardines',
        'prawn', 'prawns', 'shrimp', 'crab', 'lobster',
        'squid', 'octopus', 'mussels', 'oysters',
        'gelatin', 'lard', 'tallow',
        'chicken stock', 'beef stock', 'fish stock',
        'meat stock', 'bone broth', 'fish sauce',
        'oyster sauce', 'shrimp paste'
    ]

    # 3. Dairy ingredients
    dairy_keywords = [
        'milk', 'butter', 'cheese', 'cream', 'yogurt',
        'ghee', 'sour cream', 'condensed milk',
        'evaporated milk', 'double cream', 'heavy cream',
        'creme fraiche', 'ice cream', 'whey', 'casein',
        'milk powder', 'buttermilk', 'curds',
        'parmesan', 'mozzarella', 'cheddar', 'feta',
        'brie', 'camembert', 'ricotta', 'mascarpone',
        'paneer', 'gouda', 'gruyere', 'pecorino',
        'parmigiano-reggiano'
    ]

    # Plant-based alternatives that should not count as dairy
    plant_milk_keywords = [
        'coconut milk', 'almond milk', 'soy milk',
        'soya milk', 'oat milk', 'rice milk',
        'cashew milk', 'hemp milk'
    ]

    def has_dairy():
        for ingredient in ingredients:

            # Remove plant-based milk names before checking dairy
            clean_ingredient = ingredient

            for plant_milk in plant_milk_keywords:
                clean_ingredient = re.sub(
                    r'(?<![a-z0-9])' + re.escape(plant_milk) +
                    r'(?![a-z0-9])',
                    '',
                    clean_ingredient
                )

            # Peanut butter is not dairy butter
            clean_ingredient = re.sub(
                r'(?<![a-z0-9])peanut butter(?![a-z0-9])',
                '',
                clean_ingredient
            )

            if contains_any([clean_ingredient], dairy_keywords):
                return True

        return False

    # 4. Vegetarian
    meat_categories = [
        'beef', 'chicken', 'pork', 'lamb', 'seafood'
    ]

    has_meat = (
        contains_any(ingredients, meat_keywords)
        or category in meat_categories
    )

    if not has_meat:
        labels.append('Vegetarian')

    # 5. Vegan
    non_vegan_keywords = [
        'egg', 'eggs', 'egg white', 'egg yolk', 'free-range egg', 'free-range eggs',
        'honey', 'royal jelly', 'gelatin', 'whey', 'casein', 'mayonnaise',
        'meringue', 'lard', 'tallow', 'chicken stock', 'beef stock',
        'bone broth', 'fish sauce', 'oyster sauce', 'shrimp paste', 'carmine'
    ]

    # Vegan mayonnaise is an exception
    non_vegan_ingredients = [
        ing for ing in ingredients
        if not re.search(r'\bvegan mayonnaise\b', ing)
    ]

    has_non_vegan = (
        has_meat
        or has_dairy()
        or contains_any(non_vegan_ingredients, non_vegan_keywords)
    )

    if not has_non_vegan:
        labels.append('Vegan')

    # 6. Dairy-Free
    if not has_dairy():
        labels.append('Dairy-Free')

    # 7. Gluten-Free
    gluten_keywords = [
        'wheat', 'wheat flour', 'bread flour',
        'plain flour', 'all-purpose flour',
        'self-raising flour', 'strong flour',
        'barley', 'rye', 'malt', 'semolina',
        'couscous', 'bulgur', 'farro', 'spelt',
        'durum', 'seitan', 'breadcrumbs',
        'bread crumbs', 'panko', 'spaghetti',
        'pasta', 'noodles', 'noodle',
        'macaroni', 'lasagne', 'farfalle',
        'penne', 'rigatoni', 'vermicelli',
        'biscuit', 'biscuits', 'puff pastry',
        'phyllo pastry', 'graham crackers',
        'wheat tortilla', 'flour tortilla',
        'soy sauce', 'dark soy sauce'
    ]

    if not contains_any(ingredients, gluten_keywords):
        labels.append('Gluten-Free')

    # 8. Nut-Free
    nut_keywords = [
        'peanut', 'almond', 'cashew', 'walnut',
        'hazelnut', 'pecan', 'pistachio',
        'macadamia', 'pine nut', 'brazil nut',
        'mixed nuts', 'peanut butter', 'peanut oil',
        'ground almonds', 'flaked almonds',
        'cashew nuts', 'cashews', 'almond flour',
        'almond milk', 'cashew cream',
        'marzipan', 'praline'
    ]

    # Nutmeg is not classified as a tree nut or peanut
    nut_ingredients = [
        ing for ing in ingredients
        if not re.search(r'\bnutmeg\b', ing)
    ]

    if not contains_any(nut_ingredients, nut_keywords):
        labels.append('Nut-Free')

    # 9. Soy-Free
    soy_keywords = [
        'soy', 'soya', 'tofu', 'edamame',
        'tamari', 'miso', 'soy sauce',
        'dark soy sauce', 'soy milk',
        'soya milk', 'soy protein',
        'soy flour', 'soybean', 'tempeh',
        'textured vegetable protein'
    ]

    if not contains_any(ingredients, soy_keywords):
        labels.append('Soy-Free')

    # 10. Halal (Avoid pork, pork fat, and all types of alcohol)
    haram_keywords = [
        'pork', 'bacon', 'ham', 'parma ham', 'chorizo', 'lard', 
        'wine', 'red wine', 'dry white wine', 'white wine', 'beer', 
        'cider', 'rum', 'brandy', 'mirin', 'sake', 'alcohol', 'liqueur'
    ]
    has_haram = (
        contains_any(ingredients, haram_keywords)
        or category == 'pork'
    )
    if not has_haram:
        labels.append('Halal')

    # 11. Kosher (Avoid pork, pork fat, and shellfish)
    non_kosher_keywords = [
        'pork', 'bacon', 'ham', 'parma ham', 'chorizo', 'lard', 
        'shrimp', 'prawn', 'prawns', 'king prawns', 'raw king prawns', 
        'crab', 'lobster', 'mussel', 'mussels', 'squid', 'octopus', 
        'oyster', 'oysters', 'oyster sauce', 'shrimp paste'
    ]
    has_non_kosher = (
        contains_any(ingredients, non_kosher_keywords)
        or category in ['pork', 'seafood']
    )
    if not has_non_kosher:
        labels.append('Kosher')

    # 12. Low-Sodium (Avoid Salt and heavily salty seasonings)
    high_sodium_keywords = [
        'salt', 'sea salt', 'kosher salt', 'celery salt', 'garlic salt', 
        'onion salt', 'soy sauce', 'dark soy sauce', 'fish sauce', 
        'oyster sauce', 'bouillon', 'stock', 'chicken stock', 'beef stock', 
        'hot beef stock', 'cube', 'teriyaki', 'msg', 'bacon', 'ham', 
        'parmesan', 'cheddar', 'pickle', 'anchovies', 'olives', 
        'green olives', 'pitted black olives'
    ]
    if not contains_any(ingredients, high_sodium_keywords):
        labels.append('Low-Sodium')

    return ",".join(labels)


def process_and_update_db():
    conn = get_db_connection()

    try:
        cursor = conn.cursor()

        # 1. Check whether dietary_tags already exists
        columns = cursor.execute(
            "PRAGMA table_info(recipe_cache)"
        ).fetchall()

        column_names = [col['name'] for col in columns]

        if 'dietary_tags' not in column_names:
            cursor.execute(
                "ALTER TABLE recipe_cache ADD COLUMN dietary_tags TEXT"
            )
            print("-> Added 'dietary_tags' column.")
  
        # 2. Read recipes from database
        rows = cursor.execute(
            "SELECT meal_id, raw_data FROM recipe_cache"
        ).fetchall()

        count = 0

        # 3. Classify and update each recipe
        for row in rows:
            meal_id = row['meal_id']

            try:
                meal = json.loads(row['raw_data'])

                tags = check_dietary_labels(meal)

                cursor.execute(
                    """
                    UPDATE recipe_cache
                    SET dietary_tags = ?
                    WHERE meal_id = ?
                    """,
                    (tags, meal_id)
                )

                count += 1

            except (json.JSONDecodeError, TypeError) as error:
                print(f"-> Error processing meal {meal_id}: {error}")

        # 4. Save changes
        conn.commit()

        print(
            f" DONE! Successfully updated dietary tags "
            f"for {count} recipes in safeplate.db."
        )

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == '__main__':
    process_and_update_db()
