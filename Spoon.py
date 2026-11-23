import json
import sqlite3
import time
import requests

DB_NAME = "safeplate.db"
SPOONACULAR_API_KEY = "107b08835bf147b086d5eecd2c25bdfe" 
PROGRESS_FILE = "spoonacular_done.json"  # Tracks completed ingredients to avoid duplicate API calls across sessions


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_grocery_table():
    """Ensure the grocery_products table matches the exact schema used in app.py."""
    conn = get_db_connection()
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
        "CREATE INDEX IF NOT EXISTS idx_grocery_name ON grocery_products(product_name);"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_grocery_brands ON grocery_products(brands);"
    )
    conn.commit()
    conn.close()


def extract_ingredients_from_recipe_cache():
    """Extract all unique ingredients from the recipe_cache table in safeplate.db."""
    conn = get_db_connection()
    rows = conn.execute("SELECT raw_data FROM recipe_cache").fetchall()
    conn.close()

    unique_ingredients = set()
    for row in rows:
        try:
            meal = json.loads(row["raw_data"])
            for i in range(1, 21):
                ing = meal.get(f"strIngredient{i}")
                if ing and ing.strip():
                    # Normalize to lowercase to remove duplicates (e.g., 'Milk' and 'milk')
                    unique_ingredients.add(ing.strip().lower())
        except Exception:
            continue

    return sorted(list(unique_ingredients))


def load_progress():
    try:
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()


def save_progress(done_set):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(list(done_set)), f, ensure_ascii=False, indent=2)


def map_spoonacular_tags(ingredient, title, badges, important_badges):
    """
    Convert Spoonacular badges into allergens_tags and labels_tags formats
    for clean display on SafePlate's /grocery page.
    """
    text = f"{ingredient} {title}".lower()

    # 1. Generate labels_tags (Dietary suitability: Vegan, Gluten-Free, Dairy-Free, etc.)
    clean_labels = []
    for b in badges:
        label_name = b.replace("_", " ").title()
        clean_labels.append(label_name)

    # 2. Infer allergens_tags (Allergen warnings)
    allergens = []
    if "gluten_free" not in important_badges and any(
        w in text
        for w in ["wheat", "flour", "pasta", "bread", "noodle", "soy sauce", "barley"]
    ):
        allergens.append("Gluten")
    if "dairy_free" not in important_badges and any(
        w in text
        for w in ["milk", "cheese", "butter", "cream", "yogurt", "whey"]
    ) and not any(pm in text for pm in ["coconut milk", "almond milk", "soy milk", "oat milk", "peanut butter"]):
        allergens.append("Milk")
    if "peanut" in text:
        allergens.append("Peanuts")
    if any(w in text for w in ["almond", "walnut", "cashew", "pecan", "hazelnut", "pistachio"]):
        allergens.append("Tree nuts")
    if any(w in text for w in ["soy", "tofu", "edamame", "tamari", "miso"]):
        allergens.append("Soybeans")
    if any(w in text for w in ["egg", "mayonnaise", "mayo"]):
        allergens.append("Eggs")
    if any(w in text for w in ["shrimp", "crab", "lobster", "prawn"]):
        allergens.append("Crustaceans")
    if any(w in text for w in ["salmon", "tuna", "cod", "fish", "anchovy"]):
        allergens.append("Fish")
    if any(w in text for w in ["sesame", "tahini"]):
        allergens.append("Sesame")

    return ", ".join(allergens), ", ".join(clean_labels)


def fetch_products_from_spoonacular():
    init_grocery_table()
    all_ingredients = extract_ingredients_from_recipe_cache()
    done_ingredients = load_progress()

    remaining = [ing for ing in all_ingredients if ing not in done_ingredients]
    print(
        f"📦 Found {len(all_ingredients)} unique ingredients in recipe_cache."
    )
    print(
        f"✅ Already fetched: {len(done_ingredients)} | ⏳ Remaining: {len(remaining)}\n"
    )

    conn = get_db_connection()
    cursor = conn.cursor()
    total_saved = 0

    for idx, ingredient in enumerate(remaining, 1):
        print(
            f"[{idx}/{len(remaining)}] 🔍 Searching branded products for: '{ingredient}'..."
        )
        url = "https://api.spoonacular.com/food/products/search"
        params = {
            "apiKey": SPOONACULAR_API_KEY,
            "query": ingredient,
            "number": 8,  # Fetch up to 8 branded products per ingredient
        }

        try:
            res = requests.get(url, params=params, timeout=15)

            # Free tier daily quota exceeded
            if res.status_code == 402:
                print(
                    "\n⚠️ Spoonacular daily free quota reached (HTTP 402)!"
                )
                print(
                    "👉 Progress has been saved to spoonacular_done.json. Swap in a new API key or run again tomorrow to resume."
                )
                break

            if res.status_code == 429:
                print("   ⏳ Rate limited (HTTP 429), pausing for 5 seconds...")
                time.sleep(5)
                continue

            if res.status_code != 200:
                print(f"   ❌ HTTP Error {res.status_code}: {res.text[:100]}")
                continue

            products = res.json().get("products", [])
            batch = []

            for p in products:
                code = f"sp_{p.get('id')}"
                name = (p.get("title") or "").strip()
                brands = (p.get("brand") or "").strip()
                image = (p.get("image") or "").strip()

                # Only save products that have both a title and a clean product image
                if not name or not image:
                    continue
                if not brands:
                    brands = "Standard Brand"

                badges = p.get("badges", [])
                important_badges = p.get("importantBadges", [])
                allergens_str, labels_str = map_spoonacular_tags(
                    ingredient, name, badges, important_badges
                )

                batch.append(
                    (
                        code,
                        name,
                        brands,
                        allergens_str,
                        labels_str,
                        image,
                    )
                )

            if batch:
                cursor.executemany(
                    """
                    INSERT OR REPLACE INTO grocery_products 
                    (code, product_name, brands, allergens_tags, labels_tags, image_url)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    batch,
                )
                conn.commit()
                total_saved += len(batch)
                print(f"   -> ✅ Saved {len(batch)} branded products.")
            else:
                print("   -> ℹ️ No packaged branded products found.")

            # Mark this ingredient as completed and save progress immediately
            done_ingredients.add(ingredient)
            save_progress(done_ingredients)

            # Pause 1.2s between requests to avoid HTTP 429 rate limits
            time.sleep(1.2)

        except Exception as e:
            print(f"   ❌ Error fetching '{ingredient}': {e}")
            time.sleep(3)

    conn.close()
    print(f"\n🎉 Session complete! {total_saved} new products added to safeplate.db.")


if __name__ == "__main__":
    fetch_products_from_spoonacular()