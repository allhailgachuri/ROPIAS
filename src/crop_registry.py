"""
crop_registry.py
================
Contains agronomic thresholds and metadata for all major crops
in active agricultural production across Kenya.
"""

KENYA_CROPS = {
    # ── CEREALS ──────────────────────────────────────────────────────────────
    "maize": {
        "display_name": "Maize (Mahindi)",
        "category": "Cereals",
        "onset_threshold_mm": 20.0,
        "onset_window_days": 2,
        "dry_spell_days": 7,
        "critical_moisture": 0.30,
        "optimal_moisture_min": 0.40,
        "optimal_moisture_max": 0.70,
        "planting_season": ["long_rains", "short_rains"],
        "germination_days": 7,
        "water_sensitive_stages": ["germination", "tasseling", "grain_fill"],
        "description": "Kenya's primary staple. High water sensitivity at germination and tasseling."
    },
    "wheat": {
        "display_name": "Wheat (Ngano)",
        "category": "Cereals",
        "onset_threshold_mm": 15.0,
        "onset_window_days": 3,
        "dry_spell_days": 10,
        "critical_moisture": 0.25,
        "optimal_moisture_min": 0.35,
        "optimal_moisture_max": 0.65,
        "planting_season": ["long_rains"],
        "germination_days": 10,
        "water_sensitive_stages": ["tillering", "grain_fill"],
        "description": "Grown in cooler highlands. More drought-tolerant than maize at vegetative stage."
    },
    "rice": {
        "display_name": "Rice (Mchele)",
        "category": "Cereals",
        "onset_threshold_mm": 30.0,
        "onset_window_days": 3,
        "dry_spell_days": 5,
        "critical_moisture": 0.60,
        "optimal_moisture_min": 0.75,
        "optimal_moisture_max": 1.0,
        "planting_season": ["long_rains"],
        "germination_days": 5,
        "water_sensitive_stages": ["transplanting", "flowering", "grain_fill"],
        "description": "Requires consistently high moisture. Grown in Mwea and Ahero irrigation schemes."
    },
    "sorghum": {
        "display_name": "Sorghum (Mtama)",
        "category": "Cereals",
        "onset_threshold_mm": 15.0,
        "onset_window_days": 3,
        "dry_spell_days": 14,
        "critical_moisture": 0.20,
        "optimal_moisture_min": 0.30,
        "optimal_moisture_max": 0.60,
        "planting_season": ["long_rains", "short_rains"],
        "germination_days": 7,
        "water_sensitive_stages": ["flowering", "grain_fill"],
        "description": "Highly drought-tolerant. Suitable for ASAL regions. Can survive extended dry spells."
    },
    "millet": {
        "display_name": "Finger Millet (Wimbi)",
        "category": "Cereals",
        "onset_threshold_mm": 12.0,
        "onset_window_days": 3,
        "dry_spell_days": 14,
        "critical_moisture": 0.18,
        "optimal_moisture_min": 0.28,
        "optimal_moisture_max": 0.55,
        "planting_season": ["long_rains", "short_rains"],
        "germination_days": 6,
        "water_sensitive_stages": ["germination", "heading"],
        "description": "Extremely drought-tolerant. Widely grown in western Kenya for food security."
    },
    "barley": {
        "display_name": "Barley (Shayiri)",
        "category": "Cereals",
        "onset_threshold_mm": 14.0,
        "onset_window_days": 3,
        "dry_spell_days": 10,
        "critical_moisture": 0.22,
        "optimal_moisture_min": 0.32,
        "optimal_moisture_max": 0.60,
        "planting_season": ["long_rains"],
        "germination_days": 8,
        "water_sensitive_stages": ["tillering", "heading"],
        "description": "Grown in highland areas. Used for brewing and animal feed."
    },

    # ── LEGUMES ───────────────────────────────────────────────────────────────
    "beans": {
        "display_name": "Common Beans (Maharagwe)",
        "category": "Legumes",
        "onset_threshold_mm": 18.0,
        "onset_window_days": 2,
        "dry_spell_days": 7,
        "critical_moisture": 0.30,
        "optimal_moisture_min": 0.40,
        "optimal_moisture_max": 0.65,
        "planting_season": ["long_rains", "short_rains"],
        "germination_days": 6,
        "water_sensitive_stages": ["flowering", "pod_fill"],
        "description": "Primary protein source for rural households. Moderate water requirements."
    },
    "cowpea": {
        "display_name": "Cowpea (Kunde)",
        "category": "Legumes",
        "onset_threshold_mm": 12.0,
        "onset_window_days": 3,
        "dry_spell_days": 12,
        "critical_moisture": 0.22,
        "optimal_moisture_min": 0.32,
        "optimal_moisture_max": 0.60,
        "planting_season": ["long_rains", "short_rains"],
        "germination_days": 5,
        "water_sensitive_stages": ["flowering", "pod_fill"],
        "description": "Drought-tolerant legume widely grown in coastal and semi-arid regions."
    },
    "green_gram": {
        "display_name": "Green Gram (Ndengu)",
        "category": "Legumes",
        "onset_threshold_mm": 12.0,
        "onset_window_days": 2,
        "dry_spell_days": 10,
        "critical_moisture": 0.22,
        "optimal_moisture_min": 0.30,
        "optimal_moisture_max": 0.58,
        "planting_season": ["short_rains"],
        "germination_days": 5,
        "water_sensitive_stages": ["flowering", "pod_fill"],
        "description": "Popular in Eastern and Coastal Kenya. Short season crop, drought tolerant."
    },
    "pigeon_pea": {
        "display_name": "Pigeon Pea (Mbaazi)",
        "category": "Legumes",
        "onset_threshold_mm": 14.0,
        "onset_window_days": 3,
        "dry_spell_days": 14,
        "critical_moisture": 0.20,
        "optimal_moisture_min": 0.30,
        "optimal_moisture_max": 0.60,
        "planting_season": ["long_rains"],
        "germination_days": 7,
        "water_sensitive_stages": ["flowering", "pod_fill"],
        "description": "Perennial legume, excellent for ASAL regions. Deep roots access subsoil moisture."
    },
    "groundnuts": {
        "display_name": "Groundnuts (Karanga)",
        "category": "Legumes",
        "onset_threshold_mm": 16.0,
        "onset_window_days": 2,
        "dry_spell_days": 10,
        "critical_moisture": 0.28,
        "optimal_moisture_min": 0.38,
        "optimal_moisture_max": 0.62,
        "planting_season": ["long_rains"],
        "germination_days": 7,
        "water_sensitive_stages": ["pegging", "pod_fill"],
        "description": "Grown in western Kenya and Rift Valley. Critical moisture needed during pegging."
    },
    "soybean": {
        "display_name": "Soybean (Soya)",
        "category": "Legumes",
        "onset_threshold_mm": 20.0,
        "onset_window_days": 2,
        "dry_spell_days": 8,
        "critical_moisture": 0.32,
        "optimal_moisture_min": 0.42,
        "optimal_moisture_max": 0.68,
        "planting_season": ["long_rains"],
        "germination_days": 7,
        "water_sensitive_stages": ["flowering", "pod_fill", "seed_fill"],
        "description": "High-value legume grown in western Kenya. Used for oil and animal feed."
    },

    # ── ROOT CROPS ────────────────────────────────────────────────────────────
    "cassava": {
        "display_name": "Cassava (Muhogo)",
        "category": "Root Crops",
        "onset_threshold_mm": 10.0,
        "onset_window_days": 3,
        "dry_spell_days": 21,
        "critical_moisture": 0.15,
        "optimal_moisture_min": 0.25,
        "optimal_moisture_max": 0.55,
        "planting_season": ["long_rains", "short_rains"],
        "germination_days": 14,
        "water_sensitive_stages": ["establishment"],
        "description": "Highly drought-tolerant. Coastal and western staple. Survives extended dry spells once established."
    },
    "sweet_potato": {
        "display_name": "Sweet Potato (Viazi Vitamu)",
        "category": "Root Crops",
        "onset_threshold_mm": 16.0,
        "onset_window_days": 2,
        "dry_spell_days": 10,
        "critical_moisture": 0.28,
        "optimal_moisture_min": 0.38,
        "optimal_moisture_max": 0.65,
        "planting_season": ["long_rains", "short_rains"],
        "germination_days": 10,
        "water_sensitive_stages": ["vine_establishment", "tuber_bulking"],
        "description": "Popular food security crop. High beta-carotene varieties promoted across Kenya."
    },
    "irish_potato": {
        "display_name": "Irish Potato (Viazi)",
        "category": "Root Crops",
        "onset_threshold_mm": 20.0,
        "onset_window_days": 2,
        "dry_spell_days": 7,
        "critical_moisture": 0.35,
        "optimal_moisture_min": 0.45,
        "optimal_moisture_max": 0.70,
        "planting_season": ["long_rains"],
        "germination_days": 14,
        "water_sensitive_stages": ["tuber_initiation", "tuber_bulking"],
        "description": "Highland crop, very sensitive to moisture stress during tuber development."
    },
    "yam": {
        "display_name": "Yam (Nduma ya Pwani)",
        "category": "Root Crops",
        "onset_threshold_mm": 18.0,
        "onset_window_days": 3,
        "dry_spell_days": 14,
        "critical_moisture": 0.25,
        "optimal_moisture_min": 0.35,
        "optimal_moisture_max": 0.65,
        "planting_season": ["long_rains"],
        "germination_days": 21,
        "water_sensitive_stages": ["establishment", "tuber_bulking"],
        "description": "Traditional root crop grown in western and coastal Kenya."
    },
    "arrow_root": {
        "display_name": "Arrow Root (Nduma)",
        "category": "Root Crops",
        "onset_threshold_mm": 22.0,
        "onset_window_days": 2,
        "dry_spell_days": 7,
        "critical_moisture": 0.40,
        "optimal_moisture_min": 0.55,
        "optimal_moisture_max": 0.80,
        "planting_season": ["long_rains"],
        "germination_days": 21,
        "water_sensitive_stages": ["establishment", "corm_bulking"],
        "description": "Requires consistently high moisture. Grown near wetlands and river valleys."
    },

    # ── VEGETABLES ────────────────────────────────────────────────────────────
    "kale": {
        "display_name": "Kale / Sukuma Wiki",
        "category": "Vegetables",
        "onset_threshold_mm": 18.0,
        "onset_window_days": 2,
        "dry_spell_days": 6,
        "critical_moisture": 0.35,
        "optimal_moisture_min": 0.45,
        "optimal_moisture_max": 0.70,
        "planting_season": ["long_rains", "short_rains"],
        "germination_days": 5,
        "water_sensitive_stages": ["germination", "rapid_growth"],
        "description": "Most widely grown vegetable in Kenya. Year-round production near urban areas."
    },
    "tomato": {
        "display_name": "Tomato (Nyanya)",
        "category": "Vegetables",
        "onset_threshold_mm": 20.0,
        "onset_window_days": 2,
        "dry_spell_days": 5,
        "critical_moisture": 0.38,
        "optimal_moisture_min": 0.48,
        "optimal_moisture_max": 0.70,
        "planting_season": ["long_rains", "short_rains"],
        "germination_days": 7,
        "water_sensitive_stages": ["flowering", "fruit_set", "fruit_fill"],
        "description": "High-value commercial crop. Very sensitive to moisture fluctuation at fruit set."
    },
    "onion": {
        "display_name": "Onion (Kitunguu)",
        "category": "Vegetables",
        "onset_threshold_mm": 15.0,
        "onset_window_days": 3,
        "dry_spell_days": 8,
        "critical_moisture": 0.30,
        "optimal_moisture_min": 0.40,
        "optimal_moisture_max": 0.65,
        "planting_season": ["long_rains"],
        "germination_days": 10,
        "water_sensitive_stages": ["bulb_formation"],
        "description": "Grown in Kajiado, Narok and rift valley. Bulb formation stage is most critical."
    },
    "cabbage": {
        "display_name": "Cabbage (Kabichi)",
        "category": "Vegetables",
        "onset_threshold_mm": 18.0,
        "onset_window_days": 2,
        "dry_spell_days": 6,
        "critical_moisture": 0.35,
        "optimal_moisture_min": 0.45,
        "optimal_moisture_max": 0.70,
        "planting_season": ["long_rains", "short_rains"],
        "germination_days": 7,
        "water_sensitive_stages": ["head_formation"],
        "description": "Highland vegetable widely grown in Kiambu, Nyandarua and Meru."
    },
    "spinach": {
        "display_name": "Spinach (Mchicha)",
        "category": "Vegetables",
        "onset_threshold_mm": 16.0,
        "onset_window_days": 2,
        "dry_spell_days": 5,
        "critical_moisture": 0.35,
        "optimal_moisture_min": 0.45,
        "optimal_moisture_max": 0.70,
        "planting_season": ["long_rains", "short_rains"],
        "germination_days": 5,
        "water_sensitive_stages": ["germination", "leaf_expansion"],
        "description": "Fast-growing leafy vegetable. Widely grown peri-urban for daily market."
    },
    "carrot": {
        "display_name": "Carrot (Karoti)",
        "category": "Vegetables",
        "onset_threshold_mm": 16.0,
        "onset_window_days": 3,
        "dry_spell_days": 7,
        "critical_moisture": 0.30,
        "optimal_moisture_min": 0.40,
        "optimal_moisture_max": 0.65,
        "planting_season": ["long_rains"],
        "germination_days": 12,
        "water_sensitive_stages": ["root_bulking"],
        "description": "Grown in highland cool areas. Root cracking occurs with irregular moisture."
    },
    "capsicum": {
        "display_name": "Capsicum / Pilipili Hoho",
        "category": "Vegetables",
        "onset_threshold_mm": 18.0,
        "onset_window_days": 2,
        "dry_spell_days": 6,
        "critical_moisture": 0.35,
        "optimal_moisture_min": 0.45,
        "optimal_moisture_max": 0.68,
        "planting_season": ["long_rains", "short_rains"],
        "germination_days": 10,
        "water_sensitive_stages": ["flowering", "fruit_set"],
        "description": "High-value export vegetable. Grown under irrigation in Rift Valley."
    },
    "eggplant": {
        "display_name": "Eggplant (Biringanya)",
        "category": "Vegetables",
        "onset_threshold_mm": 16.0,
        "onset_window_days": 2,
        "dry_spell_days": 7,
        "critical_moisture": 0.32,
        "optimal_moisture_min": 0.42,
        "optimal_moisture_max": 0.65,
        "planting_season": ["long_rains", "short_rains"],
        "germination_days": 10,
        "water_sensitive_stages": ["flowering", "fruit_fill"],
        "description": "Widely grown in warmer lowland areas and coastal region."
    },

    # ── CASH CROPS ────────────────────────────────────────────────────────────
    "coffee": {
        "display_name": "Coffee (Kahawa)",
        "category": "Cash Crops",
        "onset_threshold_mm": 20.0,
        "onset_window_days": 3,
        "dry_spell_days": 14,
        "critical_moisture": 0.30,
        "optimal_moisture_min": 0.40,
        "optimal_moisture_max": 0.68,
        "planting_season": ["long_rains"],
        "germination_days": 60,
        "water_sensitive_stages": ["flowering", "cherry_development"],
        "description": "Major export crop. Central highlands. Flower induction requires a dry period then rain."
    },
    "tea": {
        "display_name": "Tea (Chai)",
        "category": "Cash Crops",
        "onset_threshold_mm": 25.0,
        "onset_window_days": 3,
        "dry_spell_days": 10,
        "critical_moisture": 0.40,
        "optimal_moisture_min": 0.55,
        "optimal_moisture_max": 0.80,
        "planting_season": ["long_rains"],
        "germination_days": 30,
        "water_sensitive_stages": ["flush_growth"],
        "description": "Kenya's top export earner. Requires consistent high rainfall. Western highlands."
    },
    "sugarcane": {
        "display_name": "Sugarcane (Miwa)",
        "category": "Cash Crops",
        "onset_threshold_mm": 25.0,
        "onset_window_days": 3,
        "dry_spell_days": 14,
        "critical_moisture": 0.35,
        "optimal_moisture_min": 0.50,
        "optimal_moisture_max": 0.75,
        "planting_season": ["long_rains"],
        "germination_days": 21,
        "water_sensitive_stages": ["germination", "grand_growth", "ripening"],
        "description": "Western Kenya (Kisumu, Kakamega, Bungoma). High water demand during grand growth."
    },
    "sunflower": {
        "display_name": "Sunflower (Alizeti)",
        "category": "Cash Crops",
        "onset_threshold_mm": 16.0,
        "onset_window_days": 3,
        "dry_spell_days": 12,
        "critical_moisture": 0.25,
        "optimal_moisture_min": 0.35,
        "optimal_moisture_max": 0.62,
        "planting_season": ["long_rains", "short_rains"],
        "germination_days": 7,
        "water_sensitive_stages": ["head_formation", "seed_fill"],
        "description": "Drought-tolerant oilseed crop. Grown in Rift Valley and eastern Kenya."
    },
    "cotton": {
        "display_name": "Cotton (Pamba)",
        "category": "Cash Crops",
        "onset_threshold_mm": 18.0,
        "onset_window_days": 3,
        "dry_spell_days": 14,
        "critical_moisture": 0.25,
        "optimal_moisture_min": 0.35,
        "optimal_moisture_max": 0.62,
        "planting_season": ["long_rains"],
        "germination_days": 7,
        "water_sensitive_stages": ["squaring", "flowering", "boll_fill"],
        "description": "Grown in Nyanza, Coast and Eastern. Needs dry period at harvest for fibre quality."
    },
    "sisal": {
        "display_name": "Sisal (Katani)",
        "category": "Cash Crops",
        "onset_threshold_mm": 10.0,
        "onset_window_days": 5,
        "dry_spell_days": 30,
        "critical_moisture": 0.12,
        "optimal_moisture_min": 0.20,
        "optimal_moisture_max": 0.50,
        "planting_season": ["long_rains"],
        "germination_days": 30,
        "water_sensitive_stages": ["establishment"],
        "description": "Extremely drought-tolerant perennial. Grown in semi-arid eastern Kenya."
    },

    # ── FRUITS ────────────────────────────────────────────────────────────────
    "banana": {
        "display_name": "Banana (Ndizi)",
        "category": "Fruits",
        "onset_threshold_mm": 22.0,
        "onset_window_days": 3,
        "dry_spell_days": 10,
        "critical_moisture": 0.40,
        "optimal_moisture_min": 0.55,
        "optimal_moisture_max": 0.80,
        "planting_season": ["long_rains"],
        "germination_days": 21,
        "water_sensitive_stages": ["bunch_emergence", "fruit_fill"],
        "description": "Grown in Central, Western and Mt. Kenya region. Requires consistently high moisture."
    },
    "mango": {
        "display_name": "Mango (Embe)",
        "category": "Fruits",
        "onset_threshold_mm": 15.0,
        "onset_window_days": 3,
        "dry_spell_days": 21,
        "critical_moisture": 0.22,
        "optimal_moisture_min": 0.32,
        "optimal_moisture_max": 0.60,
        "planting_season": ["long_rains"],
        "germination_days": 14,
        "water_sensitive_stages": ["flowering", "fruit_development"],
        "description": "Coastal and Eastern Kenya. Dry period needed to induce flowering then rain for fruit."
    },
    "avocado": {
        "display_name": "Avocado (Parachichi)",
        "category": "Fruits",
        "onset_threshold_mm": 20.0,
        "onset_window_days": 3,
        "dry_spell_days": 14,
        "critical_moisture": 0.32,
        "optimal_moisture_min": 0.42,
        "optimal_moisture_max": 0.68,
        "planting_season": ["long_rains"],
        "germination_days": 21,
        "water_sensitive_stages": ["flowering", "fruit_set", "fruit_fill"],
        "description": "Major export crop. Central highlands. Very sensitive to waterlogging."
    },
    "passion_fruit": {
        "display_name": "Passion Fruit (Matunda ya Passion)",
        "category": "Fruits",
        "onset_threshold_mm": 20.0,
        "onset_window_days": 2,
        "dry_spell_days": 10,
        "critical_moisture": 0.35,
        "optimal_moisture_min": 0.45,
        "optimal_moisture_max": 0.70,
        "planting_season": ["long_rains"],
        "germination_days": 21,
        "water_sensitive_stages": ["flowering", "fruit_fill"],
        "description": "Highland Kenya. Purple variety most common. Export potential growing rapidly."
    },
    "watermelon": {
        "display_name": "Watermelon (Tikiti Maji)",
        "category": "Fruits",
        "onset_threshold_mm": 18.0,
        "onset_window_days": 2,
        "dry_spell_days": 8,
        "critical_moisture": 0.30,
        "optimal_moisture_min": 0.40,
        "optimal_moisture_max": 0.65,
        "planting_season": ["long_rains", "short_rains"],
        "germination_days": 7,
        "water_sensitive_stages": ["fruit_set", "fruit_fill"],
        "description": "Grown in lowland warm areas. High water demand at fruit fill. Reduce at ripening."
    },
    "pineapple": {
        "display_name": "Pineapple (Nanasi)",
        "category": "Fruits",
        "onset_threshold_mm": 16.0,
        "onset_window_days": 3,
        "dry_spell_days": 21,
        "critical_moisture": 0.22,
        "optimal_moisture_min": 0.32,
        "optimal_moisture_max": 0.58,
        "planting_season": ["long_rains"],
        "germination_days": 30,
        "water_sensitive_stages": ["fruit_development"],
        "description": "Coastal and Thika region. Drought-tolerant once established. Kericho highland variety popular."
    },

    # ── FODDER & PASTURE ──────────────────────────────────────────────────────
    "napier_grass": {
        "display_name": "Napier Grass (Bana Grass)",
        "category": "Fodder",
        "onset_threshold_mm": 18.0,
        "onset_window_days": 3,
        "dry_spell_days": 14,
        "critical_moisture": 0.28,
        "optimal_moisture_min": 0.38,
        "optimal_moisture_max": 0.68,
        "planting_season": ["long_rains"],
        "germination_days": 14,
        "water_sensitive_stages": ["establishment"],
        "description": "Primary fodder crop for zero-grazing dairy farmers. Western and Central Kenya."
    },
    "rhodes_grass": {
        "display_name": "Rhodes Grass",
        "category": "Fodder",
        "onset_threshold_mm": 14.0,
        "onset_window_days": 3,
        "dry_spell_days": 21,
        "critical_moisture": 0.20,
        "optimal_moisture_min": 0.30,
        "optimal_moisture_max": 0.60,
        "planting_season": ["long_rains"],
        "germination_days": 10,
        "water_sensitive_stages": ["establishment"],
        "description": "Drought-tolerant pasture grass for semi-arid rangelands and dairy farms."
    }
}

def get_crop(crop_key: str) -> dict:
    """Returns the full metadata dictionary for a given crop key. Defaults to maize if not found."""
    return KENYA_CROPS.get(crop_key, KENYA_CROPS["maize"])

def get_crops_by_category() -> dict:
    """Returns a dictionary grouped by category -> list of crops payload."""
    categories = {}
    for key, data in KENYA_CROPS.items():
        cat = data["category"]
        if cat not in categories:
            categories[cat] = []
        
        # Attach the key back to the internal dict for frontend use
        payload = data.copy()
        payload["id"] = key
        categories[cat].append(payload)
    return categories

def get_crop_thresholds(crop_key: str) -> dict:
    """Returns only the specific agronomic thresholds required by the analytical engines."""
    crop = get_crop(crop_key)
    return {
        "onset_threshold_mm": crop["onset_threshold_mm"],
        "onset_window_days": crop["onset_window_days"],
        "dry_spell_days": crop["dry_spell_days"],
        "critical_moisture": crop["critical_moisture"],
        "optimal_moisture_min": crop["optimal_moisture_min"],
        "optimal_moisture_max": crop["optimal_moisture_max"]
    }

def list_all_crops() -> list:
    """Returns a simplified list of exactly all crops available as tuples (key, display_name)."""
    return [(k, v["display_name"]) for k, v in KENYA_CROPS.items()]
