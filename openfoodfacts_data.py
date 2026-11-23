import sqlite3
import time
import requests

DB_NAME = "safeplate.db"

# Number of pages to fetch (each page has 100 products -> 50 pages = 5,000 most popular products across all categories)
TOTAL_PAGES_TO_FETCH = 50
PAGE_SIZE = 100


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
        "CREATE INDEX IF NOT EXISTS idx_grocery_name ON grocery_products(product_name);"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_grocery_brands ON grocery_products(brands);"
    )
    conn.commit()
    conn.close()


def fetch_all_products():
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    total_added = 0
    headers = {
        "User-Agent": "SafePlateApp/1.0 (StudentProject; Contact: admin@safeplate.com)"
    }

    print(f"🚀 Starting to fetch {TOTAL_PAGES_TO_FETCH} pages of products via Open Food Facts API v2...\n")

    # Official Open Food Facts API v2 Search endpoint
    url = "https://world.openfoodfacts.org/api/v2/search"

    for page in range(1, TOTAL_PAGES_TO_FETCH + 1):
        print(f"📦 Fetching page {page}/{TOTAL_PAGES_TO_FETCH}...")

        params = {
            "sort_by": "unique_scans_n",  # Take the most popular products across all categories
            "page_size": PAGE_SIZE,
            "page": page,
            "fields": "code,product_name,product_name_en,product_name_fr,brands,allergens_tags,labels_tags,image_front_small_url,image_url",
        }

        res = None
        # Retry up to 3 times if server returns 429 or 503
        for attempt in range(3):
            try:
                res = requests.get(url, params=params, headers=headers, timeout=20)
                if res.status_code == 200:
                    break
                print(f"   ⚠️ HTTP Error {res.status_code} (Attempt {attempt + 1}/3). Pausing for 5 seconds...")
                time.sleep(5)
            except Exception as e:
                print(f"   ⚠️ Network error at page {page} (Attempt {attempt + 1}/3): {e}")
                time.sleep(5)

        if not res or res.status_code != 200:
            print(f"   ❌ Failed to fetch page {page} after 3 attempts, skipping.")
            continue

        try:
            data = res.json()
            products = data.get("products", [])

            if not products:
                print("   -> No more data from API.")
                break

            batch = []
            for p in products:
                code = p.get("code")
                # Take the English product name if available for easier searching in English
                name = (
                    p.get("product_name_en")
                    or p.get("product_name")
                    or p.get("product_name_fr")
                )
                image = p.get("image_front_small_url") or p.get("image_url", "")
                brands = (p.get("brands") or "").strip()

                # Just save products with complete information
                if not code or not name or not image or not brands:
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

                batch.append(
                    (
                        str(code),
                        name.strip(),
                        brands,
                        allergens,
                        labels,
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
                total_added += len(batch)
                print(f"   -> ✅ Saved {len(batch)} clean products (Total: {total_added}).")
            else:
                print("   -> ℹ️ No complete products on this page.")

            # Pause for 2 seconds between pages to avoid rate limiting
            time.sleep(2)

        except Exception as e:
            print(f"   ❌ Error parsing page {page}: {e}")
            time.sleep(5)

    conn.close()
    print(f"\n🎉 Finished! Added a total of {total_added} products to safeplate.db.")


if __name__ == "__main__":
    fetch_all_products()