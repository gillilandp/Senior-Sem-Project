import sqlite3
import time
import requests

DB_NAME = "safeplate.db"

# List of popular product categories
TARGET_CATEGORIES = [
    "milks",
    "plant-based-milks",
    "beverages",
    "fruit-juices",
    "teas",
    "coffees",
    "groceries",
    "sauces",
    "condiments",
    "canned-foods",
    "biscuits",
    "snacks",
    "sweet-snacks",
    "salty-snacks",
    "chocolates",
    "candies",
    "cheeses",
    "yogurts",
    "desserts",
    "ice-creams",
    "breakfast-cereals",
    "pastas",
    "noodle-dishes",
]


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS grocery_products (
            code TEXT PRIMARY KEY,
            product_name TEXT,
            brands TEXT,
            allergens_tags TEXT,
            labels_tags TEXT,
            image_url TEXT
        )
    """
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_name ON grocery_products(product_name);"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_brands ON grocery_products(brands);"
    )
    conn.commit()
    conn.close()


def fetch_and_save():
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    total_added = 0
    # Change the User-Agent to be more explicit to avoid being considered a malicious bot
    headers = {
        "User-Agent": (
            "SafePlateApp - StudentProject - Contact: admin@safeplate.com"
        )
    }

    print(
        "🚀 Starting safe data download (avoiding 429 Rate-limit) into safeplate.db...\n"
    )

    for category in TARGET_CATEGORIES:
        print(f"📦 Downloading category: '{category}'...")

        # Use the standard Open Food Facts API v2 Search
        url = "https://world.openfoodfacts.org/cgi/search.pl"
        params = {
            "action": "process",
            "tagtype_0": "categories",
            "tag_contains_0": "contains",
            "tag_0": category,
            "json": "1",
            "page_size": "50",
            "page": "1",
        }

        try:
            res = requests.get(
                url, params=params, headers=headers, timeout=12
            )

            if res.status_code == 429:
                print(
                    "   ⚠️ Rate-limited (429)! Pausing for 5 seconds before retrying..."
                )
                time.sleep(5)
                res = requests.get(
                    url, params=params, headers=headers, timeout=12
                )

            if res.status_code != 200:
                print(f"   ❌ Access failed (Status code: {res.status_code})")
                time.sleep(2)
                continue

            data = res.json()
            products = data.get("products", [])

            if not products:
                print("   -> No products found.")
                continue

            batch = []
            for p in products:
                code = p.get("code")
                name = (
                    p.get("product_name")
                    or p.get("product_name_en")
                    or p.get("product_name_fr")
                )

                if not code or not name:
                    continue

                allergens = ", ".join(
                    [
                        t.replace("en:", "").capitalize()
                        for t in p.get("allergens_tags", [])
                    ]
                )
                labels = ", ".join(
                    [
                        t.replace("en:", "").capitalize()
                        for t in p.get("labels_tags", [])
                    ]
                )
                image = p.get("image_front_small_url") or p.get("image_url", "")
                brands = p.get("brands", "N/A")

                batch.append(
                    (
                        str(code),
                        name.strip(),
                        brands.strip(),
                        allergens,
                        labels,
                        image,
                    )
                )

            cursor.executemany(
                """
                INSERT OR REPLACE INTO grocery_products 
                (code, product_name, brands, allergens_tags, labels_tags, image_url)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                batch,
            )
            conn.commit()

            total_added += len(batch)
            print(f"   -> Successfully added {len(batch)} products.")

            # Relax 3 seconds between requests to avoid server IP lock
            time.sleep(3)

        except Exception as e:
            print(f"❌ Error fetching category {category}: {e}")
            time.sleep(5)

    conn.close()
    print(
        f"\n Finished! Total products added to safeplate.db: {total_added}"
    )


if __name__ == "__main__":
    fetch_and_save()