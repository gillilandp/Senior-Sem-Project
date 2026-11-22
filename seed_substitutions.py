import sqlite3

DB_NAME = 'safeplate.db'

# Sample substitution data covering a wide range of tag categories in filter_tags.py
substitutions_data = [
    # --- 1. DAIRY ---
    {
        "original": "milk",
        "substitute": "Almond Milk",
        "tag": "dairy",
        "diets": "PCOS, Vegan, Dairy-Free",
        "ratio": "1:1",
        "note": "Low in calories, low GI, helps control insulin very well for PCOS."
    },
    {
        "original": "milk",
        "substitute": "Coconut Milk",
        "tag": "dairy",
        "diets": "Vegan, Dairy-Free, Keto",
        "ratio": "1:1",
        "note": "Naturally creamy, suitable for soups, curries, or baked dishes."
    },
    {
        "original": "milk",
        "substitute": "Oat Milk",
        "tag": "dairy",
        "diets": "Vegan, Dairy-Free",
        "ratio": "1:1",
        "note": "Mildly sweet, suitable for baking and beverages."
    },
    {
        "original": "butter",
        "substitute": "Olive Oil",
        "tag": "dairy",
        "diets": "PCOS, Heart-Health, Vegan",
        "ratio": "3:4",
        "note": "Contains monounsaturated fats, helps reduce inflammation in the body."
    },
    {
        "original": "butter",
        "substitute": "Vegan Butter",
        "tag": "dairy",
        "diets": "Vegan, Dairy-Free",
        "ratio": "1:1",
        "note": "Directly replace 1:1 in baking recipes."
    },
    # (Thêm các loại Dairy phổ biến khác)
    {
        "original": "cream",
        "substitute": "Coconut Cream",
        "tag": "dairy",
        "diets": "Vegan, Dairy-Free",
        "ratio": "1:1",
        "note": "Rich and creamy, perfect substitute for heavy cream in soups and curries."
    },
    {
        "original": "sour cream",
        "substitute": "Cashew Cream",
        "tag": "dairy",
        "diets": "Vegan, Dairy-Free",
        "ratio": "1:1",
        "note": "Blended cashews with lemon juice create a creamy, tangy substitute."
    },
    {
        "original": "parmesan cheese",
        "substitute": "Nutritional Yeast",
        "tag": "dairy",
        "diets": "Vegan, Dairy-Free, Low-Sodium",
        "ratio": "1:1",
        "note": "Adds a savory, cheesy flavor without dairy or excessive sodium."
    },
    {
        "original": "cheddar cheese",
        "substitute": "Vegan Cheddar",
        "tag": "dairy",
        "diets": "Vegan, Dairy-Free",
        "ratio": "1:1",
        "note": "Plant-based cheese alternative that melts easily."
    },
    {
        "original": "greek yogurt",
        "substitute": "Coconut Yogurt",
        "tag": "dairy",
        "diets": "Vegan, Dairy-Free",
        "ratio": "1:1",
        "note": "Probiotic-rich dairy-free yogurt alternative."
    },

    # --- 2. GLUTEN / WHEAT ---
    {
        "original": "flour",
        "substitute": "Almond Flour",
        "tag": "gluten",
        "diets": "PCOS, Gluten-Free, Low-Carb",
        "ratio": "1:1",
        "note": "Rich in fiber and protein, helps stabilize blood sugar levels."
    },
    {
        "original": "plain flour",
        "substitute": "Almond Flour",
        "tag": "gluten",
        "diets": "PCOS, Gluten-Free, Low-Carb",
        "ratio": "1:1",
        "note": "Use almond flour to make sweet cakes, vegan cookies, or fried dishes."
    },
    # (Thêm Gluten / Mì / Bột mì khác)
    {
        "original": "self-raising flour",
        "substitute": "Gluten-Free Flour",
        "tag": "gluten",
        "diets": "Gluten-Free, Wheat-Free",
        "ratio": "1:1",
        "note": "1:1 substitute blend for gluten-free baking."
    },
    {
        "original": "spaghetti",
        "substitute": "Zucchini Noodles",
        "tag": "gluten",
        "diets": "PCOS, Gluten-Free, Low-Carb",
        "ratio": "1:1",
        "note": "Fresh spiralized zucchini noodles, very low in calories and GI."
    },
    {
        "original": "pasta",
        "substitute": "Brown Rice Pasta",
        "tag": "gluten",
        "diets": "Gluten-Free, Wheat-Free",
        "ratio": "1:1",
        "note": "Gluten-free alternative with a texture close to traditional pasta."
    },
    {
        "original": "breadcrumbs",
        "substitute": "Crushed Almonds",
        "tag": "gluten",
        "diets": "Gluten-Free, Low-Carb",
        "ratio": "1:1",
        "note": "Crispy nut coating for fried or baked dishes."
    },

    # --- 3. HIGH GI / RICE / SUGAR ---
    {
        "original": "rice",
        "substitute": "Brown Rice",
        "tag": "high_gi",
        "diets": "PCOS, Low-GI, Diabetes",
        "ratio": "1:1",
        "note": "More fiber than white rice, digests slowly to help maintain stable blood sugar levels."
    },
    {
        "original": "rice",
        "substitute": "Cauliflower",
        "tag": "high_gi",
        "diets": "PCOS, Keto, Low-Carb",
        "ratio": "1:1",
        "note": "Finely grated cauliflower rice, very low in carbs, extremely good for PCOS."
    },
    {
        "original": "sugar",
        "substitute": "Coco Sugar",
        "tag": "sugar",
        "diets": "PCOS, Low-GI",
        "ratio": "1:1",
        "note": "Coco Sugar has a lower glycemic index than refined sugar."
    },
    # (Thêm Sugar & Đường khác)
    {
        "original": "sugar",
        "substitute": "Stevia",
        "tag": "sugar",
        "diets": "PCOS, Low-GI, Diabetes, Keto",
        "ratio": "To taste",
        "note": "Zero-calorie plant sweetener, does not spike blood sugar."
    },
    {
        "original": "brown sugar",
        "substitute": "Coconut Sugar",
        "tag": "sugar",
        "diets": "PCOS, Low-GI",
        "ratio": "1:1",
        "note": "Unrefined natural sweetener with caramel flavor."
    },
    {
        "original": "honey",
        "substitute": "Maple Syrup",
        "tag": "sugar",
        "diets": "Vegan, Low-GI",
        "ratio": "1:1",
        "note": "Plant-based liquid sweetener ideal for vegans."
    },

    # --- 4. EGGS ---
    {
        "original": "eggs",
        "substitute": "Flax Eggs",
        "tag": "egg",
        "diets": "Vegan, Egg-Free, Heart-Health",
        "ratio": "1 egg = 1 tbsp flaxseed + 3 tbsp water",
        "note": "Naturally supplements Omega-3, used as a binding agent in baking."
    },
    # (Thêm Trứng & Sốt Mayonnaise)
    {
        "original": "egg",
        "substitute": "Flax Eggs",
        "tag": "egg",
        "diets": "Vegan, Egg-Free",
        "ratio": "1 egg = 1 tbsp ground flax + 3 tbsp water",
        "note": "Great binder for pancakes and baking."
    },
    {
        "original": "mayonnaise",
        "substitute": "Vegan Mayo",
        "tag": "egg",
        "diets": "Vegan, Egg-Free",
        "ratio": "1:1",
        "note": "Egg-free creamy mayonnaise substitute."
    },

    # --- 5. LAMB / MEAT ---
    {
        "original": "lamb mince",
        "substitute": "Plant-Based Ground Meat",
        "tag": "meat",
        "diets": "Vegetarian, Vegan",
        "ratio": "1:1",
        "note": "Replace ground meat with plant-based alternatives for vegetarians."
    },
    {
        "original": "lamb",
        "substitute": "Jackfruit",
        "tag": "meat",
        "diets": "Vegetarian, Vegan",
        "ratio": "1:1",
        "note": "Young jackfruit stewed to create a meat-like texture."
    },
    # (Thêm Thịt bò, gà, thịt lợn)
    {
        "original": "beef",
        "substitute": "Portobello Mushroom",
        "tag": "meat",
        "diets": "Vegetarian, Vegan, Heart-Health",
        "ratio": "1:1",
        "note": "Meaty texture and savory umami taste perfect for steak or stews."
    },
    {
        "original": "chicken breast",
        "substitute": "Tofu",
        "tag": "meat",
        "diets": "Vegetarian, Vegan, Low-Fat",
        "ratio": "1:1",
        "note": "High-protein plant substitute that easily absorbs flavors."
    },
    {
        "original": "chicken",
        "substitute": "Tofu",
        "tag": "meat",
        "diets": "Vegetarian, Vegan",
        "ratio": "1:1",
        "note": "Classic plant-based protein replacement."
    },
    {
        "original": "bacon",
        "substitute": "Tempeh Bacon",
        "tag": "meat",
        "diets": "Vegetarian, Vegan, Halal, Kosher",
        "ratio": "1:1",
        "note": "Smoky, crispy plant-based bacon alternative."
    },
    {
        "original": "prawns",
        "substitute": "King Oyster Mushroom",
        "tag": "seafood",
        "diets": "Vegetarian, Vegan, Shellfish-Free",
        "ratio": "1:1",
        "note": "Sliced mushroom stems provide a seafood-like chewy texture."
    },

    # --- 6. OILS ---
    {
        "original": "sunflower oil",
        "substitute": "Extra Virgin Olive Oil",
        "tag": "oil",
        "diets": "PCOS, Heart-Health",
        "ratio": "1:1",
        "note": "Rich in anti-inflammatory fats, good for PCOS patients."
    },
    {
        "original": "vegetable oil",
        "substitute": "Olive Oil",
        "tag": "oil",
        "diets": "PCOS, Heart-Health",
        "ratio": "1:1",
        "note": "Healthy unrefined fat source rich in antioxidants."
    },
    {
        "original": "soy sauce",
        "substitute": "Coconut Aminos",
        "tag": "soy",
        "diets": "Soy-Free, Gluten-Free, Low-Sodium",
        "ratio": "1:1",
        "note": "Soy-free seasoning sauce with 65% less sodium than soy sauce."
    }
]

def seed_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ingredient_substitutions;")
    
    for item in substitutions_data:
        img_name = item['substitute'].strip().replace(' ', '%20') + '.png'
        img_url = f"https://www.themealdb.com/images/ingredients/{img_name}"
        
        cursor.execute("""
            INSERT INTO ingredient_substitutions 
            (original_ingredient, substitute_ingredient, tag_category, diet_suitability, ratio, note, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            item['original'].strip().lower(), 
            item['substitute'].strip(), 
            item['tag'], 
            item['diets'], 
            item['ratio'], 
            item['note'], 
            img_url
        ))
        
    conn.commit()
    conn.close()
    print("✅ Uploaded all substitution seed data to the database!")

if __name__ == '__main__':
    seed_db()