import gzip
import json
import sqlite3
import time

DB_NAME = "safeplate.db"
GZ_FILE_PATH = "openfoodfacts-products.jsonl.gz"


def init_product_table():
    """Initialize the grocery_products table in safeplate.db if it doesn't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS grocery_products (
            code TEXT PRIMARY KEY,
            product_name TEXT,
            brands TEXT,
            categories TEXT,
            allergens_tags TEXT,
            labels_tags TEXT,
            ingredients_text TEXT,
            image_url TEXT
        )
    """
    )

    # Create indexes for fast searching by Product Name & Brands later on
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_product_name ON grocery_products(product_name);"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_brands ON grocery_products(brands);"
    )

    conn.commit()
    conn.close()
    print("-> Initialized the 'grocery_products' table and indexes in SQLite.")


def import_data_to_sqlite():
    init_product_table()

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    count = 0
    batch = []
    start_time = time.time()

    print(
        f"⏳ Reading the compressed file '{GZ_FILE_PATH}' and loading data into {DB_NAME}..."
    )

    try:
        # Read the .gz file line by line (JSON Lines) without decompressing it to the hard drive
        with gzip.open(GZ_FILE_PATH, "rt", encoding="utf-8") as f:
            for line in f:
                try:
                    item = json.loads(line)

                    code = item.get("code")
                    name = item.get("product_name") or item.get(
                        "product_name_en", ""
                    )

                    # Skip garbage data lines that have no barcode or product name
                    if not code or not name.strip():
                        continue

                    brands = item.get("brands", "")
                    categories = item.get("categories", "")

                    # Convert the tags array to a string for storing in SQLite
                    allergens_tags = ",".join(item.get("allergens_tags", []))
                    labels_tags = ",".join(item.get("labels_tags", []))

                    ingredients_text = item.get("ingredients_text", "")
                    image_url = item.get("image_front_small_url") or item.get(
                        "image_url", ""
                    )

                    batch.append(
                        (
                            str(code),
                            name.strip(),
                            brands.strip(),
                            categories.strip(),
                            allergens_tags,
                            labels_tags,
                            ingredients_text,
                            image_url,
                        )
                    )
                    count += 1

                    # Save in batches (Batch) of 10,000 rows to achieve the best write speed into SQLite
                    if len(batch) >= 10000:
                        cursor.executemany(
                            """
                            INSERT OR REPLACE INTO grocery_products 
                            (code, product_name, brands, categories, allergens_tags, labels_tags, ingredients_text, image_url)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                            batch,
                        )
                        conn.commit()
                        batch = []
                        print(f"   -> Loaded {count:,} products...")

                except (json.JSONDecodeError, Exception):
                    continue

        # Do not forget to load the remaining items in the last batch (if any)
        if batch:
            cursor.executemany(
                """
                INSERT OR REPLACE INTO grocery_products 
                (code, product_name, brands, categories, allergens_tags, labels_tags, ingredients_text, image_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                batch,
            )
            conn.commit()

        elapsed_time = round(time.time() - start_time, 2)
        print(
            f"✅ COMPLETED! Total of {count:,} products loaded into 'safeplate.db' in {elapsed_time} seconds."
        )

    except FileNotFoundError:
        print(
            f"❌ Don't find file '{GZ_FILE_PATH}'! Please make sure you have downloaded the file from Open Food Facts and placed it in the same directory."
        )
    except Exception as e:
        conn.rollback()
        print(f"❌ Error during data loading: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    import_data_to_sqlite()