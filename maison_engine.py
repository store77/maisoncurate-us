import os
import re
import json
import hashlib
from datetime import datetime, timezone
from urllib.parse import quote_plus
import requests

# Konfigurasi Environment Variables dari GitHub Secrets / Vars
AMAZON_TAG = os.environ.get("AMAZON_TAG", "maisoncurate-20").strip()
SITE_URL = os.environ.get("SITE_URL", "https://username.github.io/maisoncurate-us").rstrip("/")
REPO_NAME = os.environ.get("GITHUB_REPOSITORY", "user/maisoncurate-us")

# Kunci verifikasi IndexNow deterministik
INDEXNOW_KEY = hashlib.md5(f"{REPO_NAME}_{AMAZON_TAG}_maison12h".encode("utf-8")).hexdigest()

DATA_DIR = "data"
STATE_FILE = os.path.join(DATA_DIR, "catalog_state.json")
DOCS_DIR = "docs"
PRODUCTS_DIR = os.path.join(DOCS_DIR, "products")
REVIEWS_DIR = os.path.join(DOCS_DIR, "reviews")
CATEGORIES_DIR = os.path.join(DOCS_DIR, "categories")

# Taksonomi Lengkap Kategori, Subkategori, Merek & Spesifikasi Amazon Best-Sellers
TAXONOMY = [
    {
        "category": "Air Fryers & Countertop Ovens",
        "cat_slug": "air-fryers-countertop-ovens",
        "icon": "🔥",
        "subcategories": [
            {
                "name": "Dual-Zone Air Fryers",
                "slug": "dual-zone-air-fryers",
                "brands": ["Ninja", "Instant Vortex", "Cosori", "Gourmia", "Chefman"],
                "models": ["Foodi DualZone XL 10-Qt", "Plus Dual-Basket 8.5-Qt", "TurboBlaze Dual 9-Qt", "SmartSync 11-Qt MegaZone", "ClearView Dual-Window 8-Qt"],
                "specs": {"Capacity": "8.5-Qt to 11-Qt Dual Independent Baskets", "Temp Range": "90°F – 450°F Digital PID", "Heating Element": "1800W Dual High-Velocity Cyclonic Fans", "Basket Coating": "PTFE/PFOA-Free Ceramic Nonstick, Dishwasher Safe"},
                "buy_if": "You cook two separate dishes simultaneously (e.g., salmon and crispy potatoes) and want synchronized finish times.",
                "skip_if": "You have very limited apartment counter width or regularly roast whole 14-lb holiday turkeys."
            },
            {
                "name": "Stainless Convection Ovens",
                "slug": "stainless-convection-ovens",
                "brands": ["Breville", "Cuisinart", "KitchenAid", "Calphalon", "Ninja"],
                "models": ["Smart Oven Air Fryer Pro BOV900", "Chef's Convection TOB-260N1", "Digital Countertop Dual-Convection", "Quartz Heat Air Fry Oven", "Foodi 10-in-1 XL Pro Roast"],
                "specs": {"Interior Volume": "1.0 cu. ft. (Fits 9x13 Pan / 14-lb Turkey)", "Element System": "5-to-6 Independent Quartz IQ Heating Elements", "Modes": "13 Presets Including Dehydrate, Proof & Air Fry", "Construction": "Brushed 304 Stainless Steel Chassis"},
                "buy_if": "You want a true second oven that preheats in 60 seconds and replaces a toaster, dehydrator, and air fryer.",
                "skip_if": "You only reheat single-serving frozen snacks and don't need sheet-pan baking capacity."
            },
            {
                "name": "Indoor 850°F Pizza Ovens",
                "slug": "indoor-pizza-ovens",
                "brands": ["Ooni", "Breville", "Chefman", "Cuisinart", "Piezano"],
                "models": ["Volt 12 Electric Indoor/Outdoor", "Pizzaiolo Smart Deck Oven", "HomeSlice 800°F Countertop", "Indoor Cordierite Stone Pizza Oven", "CrispyCrust Dual-Thermostat 12-Inch"],
                "specs": {"Max Temperature": "750°F – 850°F Neapolitan Deck Heat", "Bake Time": "90 Seconds per 12-Inch Artisan Pie", "Deck Material": "Removable Cordierite Baking Stone", "Ventilation": "Smokeless Low-Emission Indoor Insulation"},
                "buy_if": "You want authentic leopard-spotted Neapolitan crust indoors year-round without propane tanks or wood pellets.",
                "skip_if": "You only bake thick frozen supermarket pizzas that cook at standard 400°F oven temperatures."
            }
        ]
    },
    {
        "category": "Chef Cookware & Cast Iron",
        "cat_slug": "chef-cookware-cast-iron",
        "icon": "🍳",
        "subcategories": [
            {
                "name": "5-Ply Clad Stainless Sets",
                "slug": "clad-stainless-cookware-sets",
                "brands": ["All-Clad", "Tramontina", "Made In", "Cuisinart", "Calphalon"],
                "models": ["D5 Brushed 10-Piece Set", "Tri-Ply Clad 12-Piece Gourmet", "5-Ply Stainless Chef Collection", "MultiClad Pro Triple-Ply 12-Pc", "Premier Stainless 11-Piece Set"],
                "specs": {"Cladding Layers": "3-Ply to 5-Ply Alternating Aluminum & 18/10 Stainless", "Oven Safe Rating": "Up to 600°F (Broiler & Induction Compatible)", "Handles": "Riveted Stay-Cool Stainless Ergonomic Grips", "Rim Profile": "Flared Drip-Free Pouring Edges"},
                "buy_if": "You want lifetime heirloom cookware capable of high-heat steak searing, fond deglazing, and induction compatibility.",
                "skip_if": "You refuse to preheat pans properly with cooking oil and want zero-oil egg release without technique."
            },
            {
                "name": "Enameled Dutch Ovens",
                "slug": "enameled-cast-iron-dutch-ovens",
                "brands": ["Le Creuset", "Staub", "Lodge", "Cuisinart", "Amazon Basics"],
                "models": ["Signature 5.5-Qt Round Cocotte", "Cast Iron 7-Qt Self-Basting Oven", "6-Qt Dual-Handle Enameled Dutch Oven", "Chef's Classic 7-Qt Casserole", "Heavy-Duty 6-Qt Porcelain Cast Iron"],
                "specs": {"Core Material": "Sand-Cast Heavy Gauge Iron with 3-Layer Porcelain Enamel", "Lid Engineering": "Self-Basting Moisture-Return Spikes / Rings", "Thermal Limit": "500°F Oven, Stovetop & Induction Safe", "Maintenance": "No Seasoning Required, Acid-Resistant Enamel"},
                "buy_if": "You bake crusty sourdough boules, braise short ribs, or simmer tomato sauces for hours.",
                "skip_if": "You have wrist mobility issues that make lifting a 13-lb cast iron pot out of the oven difficult."
            },
            {
                "name": "PFAS-Free Ceramic Skillets",
                "slug": "pfas-free-ceramic-skillets",
                "brands": ["Caraway", "GreenPan", "Our Place", "ZWILLING", "Sensarte"],
                "models": ["Non-Toxic Ceramic Fry & Sauté Duo", "Valencia Pro Hard-Anodized 11-Pc", "Always Pan 2.0 Oven-Safe Edition", "Madura Plus Forged Ceramic Set", "Swiss Granite Nonstick Skillet Trio"],
                "specs": {"Coating Chemistry": "Thermolon / Sol-Gel Silica Ceramic (100% PTFE, PFOA, Lead & Cadmium Free)", "Base Plate": "Magneto Induction Forged Aluminum Base", "Oven Safe": "Up to 450°F – 550°F", "Cleaning": "Effortless Warm Water Wipe-Clean Surface"},
                "buy_if": "You prioritize non-toxic PFAS-free cooking for eggs, pancakes, and delicate fish fillets using minimal butter or oil.",
                "skip_if": "You use metal spatulas and blast empty pans on maximum burner heat."
            }
        ]
    },
    {
        "category": "Water Filtration & Ice Makers",
        "cat_slug": "water-filtration-ice-makers",
        "icon": "💧",
        "subcategories": [
            {
                "name": "Tankless Reverse Osmosis (RO)",
                "slug": "tankless-reverse-osmosis-systems",
                "brands": ["Waterdrop", "APEC Water", "iSpring", "Frizzlife", "Express Water"],
                "models": ["G3P800 UV 800GPD Tankless RO", "ROES-PH75 Alkaline 6-Stage", "RCC7AK-UV 7-Stage Under-Sink", "PD600-TAM3 Remineralization RO", "ALK10D Smart Digital RO System"],
                "specs": {"Filtration Accuracy": "0.0001 Micron RO Membrane (Reduces TDS, PFAS, Lead, Fluoride)", "Flow Rate": "600 to 800 Gallons Per Day (Fills 8oz Cup in 6 Secs)", "Pure-to-Drain Ratio": "3:1 Ultra-Low Wastewater Efficiency", "Smart Faucet": "Real-Time Digital TDS & Filter Life LED Display"},
                "buy_if": "You want bottled-quality remineralized drinking water directly from your kitchen sink while reclaiming 70% under-sink cabinet space.",
                "skip_if": "You Do Not have a standard 110V electrical outlet under your kitchen sink (required for tankless booster pumps)."
            },
            {
                "name": "Chewable Nugget Ice Makers",
                "slug": "chewable-nugget-ice-makers",
                "brands": ["GE Profile", "Frigidaire", "Euhomy", "Silonow", "NewAir"],
                "models": ["Opal 2.0 Ultra with Side Tank", "Gallery 44-lb Crunchy Sonic Ice Maker", "Countertop Pebble Ice Machine 40-lb", "Self-Cleaning Chewable Nugget Pro", "NIM044BS00 Stainless Pellet Ice Maker"],
                "specs": {"Daily Ice Output": "34 lbs to 44 lbs per 24 Hours", "First Batch Speed": "Fresh Chewable Pellet Ice in 7–10 Minutes", "Water Supply": "Dual-Mode: Manual Reservoir + Side Refill Tank", "Sanitization": "One-Touch UV & Descaling Self-Clean Cycle"},
                "buy_if": "You love soft, airy, chewable restaurant-style pellet ice for iced coffee, cocktails, and smoothies.",
                "skip_if": "You want rock-hard slow-melting whiskey spheres rather than crunchable nugget ice."
            },
            {
                "name": "Countertop NSF-53 Filters",
                "slug": "countertop-water-filter-dispensers",
                "brands": ["AquaTru", "Bluevua", "Brita", "ZeroWater", "LifeStraw"],
                "models": ["Carafe 4-Stage Countertop RO", "RO100ROPOT Glass Reverse Osmosis", "Hub Instant Countertop Filtration", "5-Stage 40-Cup Ready-Pour Ion Exchange", "Home 10-Cup Glass Pitcher Dispenser"],
                "specs": {"Installation": "Zero Plumbing Required — Plug & Pour Countertop Design", "Certification": "Tested to NSF/ANSI 42, 53 & 58 Standards", "Carafe Material": "Borosilicate Glass / BPA-Free Tritan", "Filter Lifespan": "6 to 24 Months per Cartridge Set"},
                "buy_if": "You rent an apartment or dorm where drilling into granite countertops or under-sink pipes is prohibited.",
                "skip_if": "You have a family of 6+ and don't want to refill a countertop water tank daily."
            }
        ]
    },
    {
        "category": "HEPA Air Purifiers & Climate",
        "cat_slug": "hepa-air-purifiers-climate",
        "icon": "🌬️",
        "subcategories": [
            {
                "name": "True HEPA H14 Purifiers",
                "slug": "true-hepa-air-purifiers",
                "brands": ["Coway", "Levoit", "Blueair", "Winix", "Shark"],
                "models": ["Airmega 400 Smart Dual-Intake", "EverestAir / Core 600S Smart HEPA", "Blue Pure 211i Max WhisperSilent", "5500-2 PlasmaWave True HEPA", "NeverChange MAX 5-Year HEPA"],
                "specs": {"Particle Capture": "99.97% – 99.99% Down to 0.1 Microns (Wildfire Smoke, Pollen, Mold)", "Coverage Area": "1,500 to 3,100 Sq. Ft. (1 ACH Rating)", "Noise Floor": "21 dB Whisper-Quiet Sleep Mode", "Air Quality Sensor": "Laser PM2.5 + VOC Auto-Speed Adjustment"},
                "buy_if": "You suffer from seasonal allergies, pet dander sensitivity, or wildfire smoke intrusion in open-concept living spaces.",
                "skip_if": "You expect an air purifier to cool down room temperature like an air conditioner."
            },
            {
                "name": "Evaporative Humidifiers",
                "slug": "evaporative-ultrasonic-humidifiers",
                "brands": ["Carepod", "Canopy", "Levoit", "Dyson", "Venta"],
                "models": ["One Stainless Steel Boil-Sterilizable", "Bedside & Nursery Mold-Inhibited", "OasisMist 1000S Tower 10L", "Purifier Humidify+Cool Formaldehyde", "LW25 Original German Airwasher"],
                "specs": {"Tank Capacity": "4.0L to 10.0L Top-Fill Reservoir (Up to 60 Hrs Runtime)", "Hygiene Design": "Zero-White-Dust Evaporative / Boil-Safe Stainless Interior", "Humidity Control": "Built-In Humidistat Auto-Target (40%–60% RH)", "Maintenance": "Dishwasher-Safe Tank & Filter-Free / Washable Parts"},
                "buy_if": "You wake up with dry sinuses, cracked winter skin, or static electricity when central heating runs.",
                "skip_if": "Your home already sits above 60% relative humidity (use a dehumidifier instead)."
            },
            {
                "name": "Energy-Star Dehumidifiers",
                "slug": "energy-star-home-dehumidifiers",
                "brands": ["Midea", "hOmeLabs", "Frigidaire", "Vellgoo", "Waykar"],
                "models": ["Cube 50-Pint Smart Wi-Fi", "4,500 Sq. Ft. Energy Star Basement", "High-Humidity 50-Pint Built-In Pump", "DryTank 52-Pint Whisper Basement", "120-Pint Commercial Crawlspace"],
                "specs": {"Moisture Removal": "50 Pints per Day (DOE Standard) / Up to 4,500 Sq. Ft.", "Drainage Options": "Auto-Shutoff Bucket + Continuous Gravity Hose + Built-In Vertical Pump", "Efficiency": "2026 ENERGY STAR Most Efficient CertifiedCompressor", "Defrost": "Auto-Defrost Low-Temp Basement Operation"},
                "buy_if": "You want to prevent musty odors, dust mites, and structural mold in basements, crawlspaces, or coastal homes.",
                "skip_if": "You only need a tiny closet desiccant packet for a shoe cabinet."
            }
        ]
    },
    {
        "category": "Blenders, Juicers & Mixers",
        "cat_slug": "blenders-juicers-mixers",
        "icon": "🥤",
        "subcategories": [
            {
                "name": "Commercial High-Speed Blenders",
                "slug": "commercial-high-speed-blenders",
                "brands": ["Vitamix", "Blendtec", "Ninja", "Breville", "Nutribullet"],
                "models": ["5200 Professional / A3500 Ascent", "Total Classic Original 75-Oz", "Detect Kitchen System PowerBlender", "Super Q Brushed Stainless Commercial", "Smart Touch Combo 1500W"],
                "specs": {"Motor Rating": "2.2 to 3.0 Peak Horsepower High-Torque Copper Motor", "Blade Assembly": "Laser-Cut Hardened Aircraft Stainless Steel (Friction-Heats Soup in 6 Mins)", "Container": "64-Oz BPA-Free Eastman Tritan Copolyester", "Warranty": "Up to 7–10 Year Full Machine Warranty"},
                "buy_if": "You want velvety-smooth green smoothies, homemade almond butter, hot pureed soups, and crushed ice in 30 seconds.",
                "skip_if": "You only mix protein powder into water once a week."
            },
            {
                "name": "Cold-Press Masticating Juicers",
                "slug": "cold-press-masticating-juicers",
                "brands": ["Nama", "Hurom", "Kuvings", "Omega", "Ninja"],
                "models": ["J2 Hands-Free Batch Cold Press", "H400 Easy Clean Slow Juicer", "AUTO10 Hands-Free 3L Hopper", "Effortless Batch Cube Masticating", "NeverClog Cold Press Pro"],
                "specs": {"Auger Speed": "43 to 60 RPM Low-Oxidation Cold Press Extraction", "Feed Chute": "Wide 4.5-Inch Whole-Apple Batch Hopper", "Nutrient Retention": "Zero Heat Build-Up — 72-Hour Cold Storage Shelf Life", "Cleanup": "Mesh-Free Scrub-Free Easy Rinse Strainer"},
                "buy_if": "You juice celery, kale, ginger shots, and root vegetables daily and want maximum dry-pulp juice yield.",
                "skip_if": "You don't want to wash a hopper and auger after making fresh juice."
            },
            {
                "name": "Bowl-Lift Stand Mixers",
                "slug": "bowl-lift-tilt-head-stand-mixers",
                "brands": ["KitchenAid", "Ankarsrum", "Bosch", "Cuisinart", "Kenwood"],
                "models": ["Artisan 5-Qt / Commercial 7-Qt Bowl-Lift", "Original 7.4-Qt Swedish Bread Mixer", "Universal Plus 800W Dough Mixer", "Precision Master 5.5-Qt Die-Cast", "Chef XL Titanium 6.7-Qt"],
                "specs": {"Transmission": "All-Metal High-Torque Planetary / Roller Gear Drive", "Bowl Capacity": "5.0-Qt to 7.4-Qt Brushed Stainless Steel", "Power Hub": "10+ Attachment Hub (Pasta Roller, Meat Grinder, Ice Cream)", "Kneading Capacity": "Up to 8–14 Loaves of Dense Sourdough / Pizza Dough"},
                "buy_if": "You bake bread, whip meringue, shred chicken, or batch-mix holiday cookie dough hands-free.",
                "skip_if": "You only whisk pancake batter twice a year."
            }
        ]
    },
    {
        "category": "Mattresses, Bedding & Sleep",
        "cat_slug": "mattresses-bedding-sleep",
        "icon": "🛏️",
        "subcategories": [
            {
                "name": "CertiPUR-US Hybrid Mattresses",
                "slug": "certipur-us-hybrid-mattresses",
                "brands": ["Nectar", "DreamCloud", "Casper", "Tuft & Needle", "Novilla"],
                "models": ["Premier Copper Hybrid 13-Inch Queen", "Luxury Hybrid Cashmere Top 14-Inch", "Snow Cooling Hybrid Medium-Firm", "Mint Adaptive Foam + Pocket Coil", "Bliss Gel-Infused Euro-Top Hybrid"],
                "specs": {"Construction": "Individually Wrapped 8-Inch Pocket Coils + Gel Memory Foam", "Certifications": "CertiPUR-US & OEKO-TEX 100 Fiberglass-Free Barrier", "Motion Isolation": "Zero Partner Roll-Together Edge Support", "Cooling": "Phase-Change Polyethylene Cover"},
                "buy_if": "You want balanced lumbar spinal alignment for side and back sleeping with high edge support and zero fiberglass.",
                "skip_if": "You prefer ultra-firm traditional Japanese floor futons with zero cushion give."
            },
            {
                "name": "Mulberry Silk & Bamboo Sheets",
                "slug": "mulberry-silk-bamboo-sheet-sets",
                "brands": ["Cozy Earth", "Hotel Sheets Direct", "Quince", "Bedsure", "LuxClub"],
                "models": ["100% Viscose from Bamboo 4-Pc Queen", "160 GSM Organic Bamboo Cooling Set", "22-Momme Mulberry Silk Luxury Set", "Breescape Cooling Weave Deep-Pocket", "6-Piece Oeko-Tex Bamboo Eco Sheets"],
                "specs": {"Fiber Grade": "100% Organic Viscose from Bamboo / 6A 22-Momme Mulberry Silk", "Pocket Depth": "16-Inch to 18-Inch All-Around Elastic Deep Pockets", "Thermoregulation": "Moisture-Wicking 3°F Cooler Than Percale Cotton", "Safety Standard": "OEKO-TEX Standard 100 Certified Dye-Safe"},
                "buy_if": "You are a hot sleeper or experience night sweats and want buttery-soft, friction-free drape.",
                "skip_if": "You prefer crisp, stiff, starched hotel percale cotton sheets."
            },
            {
                "name": "Ergonomic Memory Pillows",
                "slug": "ergonomic-memory-foam-pillows",
                "brands": ["Coop Home Goods", "Tempur-Pedic", "Purple", "Beckham Hotel", "Osteo"],
                "models": ["EdenCool+ Adjustable Cross-Cut Fill", "TEMPUR-Neck Contoured Ergonomic", "Harmony Hex-Grid Talalay Latex", "Luxury Gel Fiber 2-Pack Gusseted", "Cervical Hollow-Center Neck Relief"],
                "specs": {"Loft Adjustability": "Customizable Cross-Cut Memory Foam + Microfiber Blend", "Cover Fabric": "Machine-Washable Cooling Tencel / Bamboo Zippered Case", "Orthopedic Profile": "Dual-Height Cervical Curve Alignment", "Certification": "GREENGUARD Gold & CertiPUR-US Certified"},
                "buy_if": "You wake up with stiff neck muscles or shoulder tension and need a pillow tailored to your exact shoulder width.",
                "skip_if": "You never adjust your pillow loft and prefer ultra-flat down feathers."
            }
        ]
    }
]

EDITIONS = [
    ("2026 Pro Series", "updated 2026 flagship model featuring reinforced thermal controls and quieter acoustic operation"),
    ("Culinary Studio Bundle", "complete chef bundle packaged with essential starter accessories and extended coverage"),
    ("Brushed Stainless Edition", "fingerprint-resistant 304 stainless steel architectural finish for modern kitchens"),
    ("Smart Sense Revision", "precision digital sensor edition engineered for repeatable daily performance")
]


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def make_amazon_url(query: str) -> str:
    """
    Membuat tautan afiliasi Amazon US dengan Tracking ID otomatis,
    diurutkan berdasarkan Best-Sellers (exact-aware-popularity-rank) dan rating 4 bintang ke atas.
    """
    encoded = quote_plus(query)
    return (
        f"https://www.amazon.com/s?k={encoded}"
        f"&s=exact-aware-popularity-rank&rh=p_72%3A1248873011&tag={AMAZON_TAG}"
    )


def init_or_load_state() -> dict:
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
                if state.get("products"):
                    return state
        except Exception:
            pass

    # Bangun antrean awal 360+ produk terlaris jika belum ada
    products = []
    idx = 1
    for cat in TAXONOMY:
        for sub in cat["subcategories"]:
            for brand in sub["brands"]:
                for model in sub["models"]:
                    for ed_name, ed_desc in EDITIONS:
                        title = f"{brand} {model} ({ed_name})"
                        slug = f"{slugify(brand)}-{slugify(model)}-{slugify(ed_name)}-{idx}"
                        products.append({
                            "id": f"MC-{idx:04d}",
                            "slug": slug,
                            "name": title,
                            "brand": brand,
                            "category": cat["category"],
                            "cat_slug": cat["cat_slug"],
                            "cat_icon": cat["icon"],
                            "subcategory": sub["name"],
                            "sub_slug": sub["slug"],
                            "search_query": f"{brand} {model} {sub['name']}",
                            "summary": f"The {title} is an Amazon top-ranked {sub['name'].lower()}—an {ed_desc}.",
                            "specs": sub["specs"],
                            "buy_if": sub["buy_if"],
                            "skip_if": sub["skip_if"],
                            "pros": [
                                f"Authentic {brand} engineering with verified component durability",
                                f"{list(sub['specs'].keys())[0]}: {list(sub['specs'].values())[0]}",
                                f"{list(sub['specs'].keys())[1]}: {list(sub['specs'].values())[1]}"
                            ],
                            "cons": [
                                "High seasonal demand on Amazon can occasionally impact color/finish availability",
                                "Requires dedicated storage or counter footprint matching its capacity class"
                            ],
                            "published": False,
                            "published_at": ""
                        })
                        idx += 1

    state = {"products": products, "reviews": [], "cycle_count": 0}
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    return state


def save_state(state: dict):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def get_common_styles() -> str:
    return """
        :root {
            --bg: #ffffff;
            --surface: #f8fafc;
            --border: #e2e8f0;
            --navy: #0f172a;
            --slate: #475569;
            --emerald: #047857;
            --emerald-dark: #065f46;
            --emerald-light: #ecfdf5;
            --amber: #d97706;
            --amber-light: #fffbeb;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: var(--bg); color: var(--navy); line-height: 1.65; }
        .compliance-bar { background: var(--navy); color: #f8fafc; font-size: 0.79rem; text-align: center; padding: 9px 16px; border-bottom: 1px solid #1e293b; }
        .compliance-bar strong { color: #34d399; }
        header { background: rgba(255,255,255,0.97); border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 100; backdrop-filter: blur(8px); }
        .nav-wrap { max-width: 1240px; margin: 0 auto; padding: 14px 20px; display: flex; justify-content: space-between; align-items: center; gap: 18px; flex-wrap: wrap; }
        .brand { font-size: 1.45rem; font-weight: 900; color: var(--navy); text-decoration: none; letter-spacing: -0.5px; display: flex; align-items: center; gap: 8px; }
        .brand span { color: var(--emerald); }
        .nav-links { display: flex; align-items: center; gap: 18px; flex-wrap: wrap; }
        .nav-link { color: var(--navy); text-decoration: none; font-size: 0.9rem; font-weight: 600; padding: 6px 10px; border-radius: 6px; }
        .nav-link:hover { background: var(--surface); color: var(--emerald); }
        .mega-dropdown { position: relative; display: inline-block; }
        .mega-menu { display: none; position: absolute; left: 0; top: 100%; width: 780px; max-width: 92vw; background: #fff; border: 1px solid var(--border); border-radius: 14px; box-shadow: 0 20px 35px rgba(15,23,42,0.12); padding: 22px; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 18px; z-index: 200; }
        .mega-dropdown:hover .mega-menu { display: grid; }
        .mega-col h4 { font-size: 0.88rem; color: var(--emerald-dark); margin-bottom: 8px; border-bottom: 1px solid var(--border); padding-bottom: 4px; }
        .mega-col a { display: block; color: var(--slate); text-decoration: none; font-size: 0.82rem; padding: 4px 0; }
        .mega-col a:hover { color: var(--emerald); font-weight: 600; }
        .container { max-width: 1240px; margin: 36px auto; padding: 0 20px; }
        .btn-amz { display: inline-block; background: var(--emerald); color: #ffffff; font-weight: 700; text-decoration: none; padding: 12px 20px; border-radius: 8px; font-size: 0.9rem; text-align: center; transition: background 0.15s; border: none; cursor: pointer; }
        .btn-amz:hover { background: var(--emerald-dark); }
        .btn-outline { display: inline-block; background: #fff; color: var(--navy); border: 1px solid var(--border); font-weight: 600; text-decoration: none; padding: 11px 16px; border-radius: 8px; font-size: 0.88rem; text-align: center; }
        .btn-outline:hover { border-color: var(--emerald); color: var(--emerald); }
        .grid-3 { display: grid; grid-template-columns: repeat(auto-fill, minmax(310px, 1fr)); gap: 22px; }
        .card { background: #fff; border: 1px solid var(--border); border-radius: 14px; padding: 22px; display: flex; flex-direction: column; justify-content: space-between; transition: transform 0.15s, box-shadow 0.15s; }
        .card:hover { transform: translateY(-3px); box-shadow: 0 12px 24px rgba(15,23,42,0.06); border-color: #cbd5e1; }
        .pill { display: inline-block; background: var(--emerald-light); color: var(--emerald-dark); font-size: 0.74rem; font-weight: 700; padding: 4px 10px; border-radius: 999px; margin-bottom: 10px; width: fit-content; }
        .micro-disclosure { font-size: 0.73rem; color: #64748b; margin: 10px 0 6px; }
        footer { background: var(--surface); border-top: 1px solid var(--border); margin-top: 70px; padding: 48px 20px; color: var(--slate); font-size: 0.85rem; }
        .footer-inner { max-width: 1240px; margin: 0 auto; display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 28px; }
        .footer-inner h4 { color: var(--navy); margin-bottom: 10px; font-size: 0.95rem; }
        .footer-inner a { display: block; color: var(--slate); text-decoration: none; padding: 3px 0; }
        .footer-inner a:hover { color: var(--emerald); }
    """


def build_header_html() -> str:
    mega_cols = ""
    for cat in TAXONOMY:
        sub_links = "".join(
            f'<a href="{SITE_URL}/categories/{sub["slug"]}.html">&rsaquo; {sub["name"]}</a>'
            for sub in cat["subcategories"]
        )
        mega_cols += f"""
        <div class="mega-col">
            <h4><a href="{SITE_URL}/categories/{cat['cat_slug']}.html" style="color:var(--emerald-dark);font-size:0.88rem;">{cat['icon']} {cat['category']}</a></h4>
            {sub_links}
        </div>
        """

    return f"""
    <div class="compliance-bar">
        <strong>AFFILIATE DISCLOSURE:</strong> As an Amazon Associate I earn from qualifying purchases. All prices & availability are verified directly on Amazon.com.
    </div>
    <header>
        <div class="nav-wrap">
            <a href="{SITE_URL}/" class="brand">🏛️ Maison<span>Curate</span> US</a>
            <nav class="nav-links">
                <a href="{SITE_URL}/" class="nav-link">Storefront</a>
                <div class="mega-dropdown">
                    <a href="#categories" class="nav-link">Categories & Subcategories &#9662;</a>
                    <div class="mega-menu">
                        {mega_cols}
                    </div>
                </div>
                <a href="{SITE_URL}/#reviews" class="nav-link">12H Buying Guides</a>
                <a href="{SITE_URL}/legal.html" class="nav-link">About & Policies</a>
            </nav>
        </div>
    </header>
    """


def build_footer_html(today: str) -> str:
    cat_links = "".join(
        f'<a href="{SITE_URL}/categories/{c["cat_slug"]}.html">{c["icon"]} {c["category"]}</a>'
        for c in TAXONOMY
    )
    return f"""
    <footer>
        <div class="footer-inner">
            <div>
                <h4>MaisonCurate US</h4>
                <p>Independent product discovery & buying-guide publication covering Amazon's #1 best-selling home, kitchen, water filtration, climate, and sleep systems.</p>
                <p style="margin-top:10px;font-weight:600;color:var(--navy);">As an Amazon Associate I earn from qualifying purchases.</p>
            </div>
            <div>
                <h4>Best-Selling Departments</h4>
                {cat_links}
            </div>
            <div>
                <h4>Compliance & Legal</h4>
                <a href="{SITE_URL}/legal.html#about">About Our Editorial Team</a>
                <a href="{SITE_URL}/legal.html#disclosure">Amazon Affiliate Disclosure</a>
                <a href="{SITE_URL}/legal.html#privacy">Privacy Policy</a>
                <a href="{SITE_URL}/legal.html#terms">Terms of Use</a>
                <a href="{SITE_URL}/sitemap.xml">XML Sitemap</a>
                <a href="{SITE_URL}/feed.xml">RSS 2.0 Feed</a>
            </div>
        </div>
        <div style="max-width:1240px;margin:28px auto 0;padding-top:20px;border-top:1px solid var(--border);text-align:center;font-size:0.78rem;">
            &copy; {today[:4]} MaisonCurate US. Not operated, endorsed, or sponsored by Amazon.com, Inc. Last 12-Hour Automated Sync: {today}.
        </div>
    </footer>
    """


def render_product_page(prod: dict, related: list, today: str) -> str:
    os.makedirs(PRODUCTS_DIR, exist_ok=True)
    page_url = f"{SITE_URL}/products/{prod['slug']}.html"
    amz_url = make_amazon_url(prod["search_query"])

    specs_rows = "".join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in prod["specs"].items())
    pros_html = "".join(f"<li style='margin-bottom:6px;color:#065f46;'>&#10004; {p}</li>" for p in prod["pros"])
    cons_html = "".join(f"<li style='margin-bottom:6px;color:#991b1b;'>&#9888; {c}</li>" for c in prod["cons"])

    rel_cards = ""
    for r in related[:3]:
        if r["slug"] == prod["slug"]:
            continue
        r_amz = make_amazon_url(r["search_query"])
        rel_cards += f"""
        <div class="card">
            <div>
                <span class="pill">{r['subcategory']}</span>
                <h3 style="font-size:1.05rem;margin-bottom:8px;"><a href="{SITE_URL}/products/{r['slug']}.html" style="color:var(--navy);text-decoration:none;">{r['name']}</a></h3>
                <p style="font-size:0.86rem;color:var(--slate);">{r['summary']}</p>
            </div>
            <div style="margin-top:14px;">
                <a href="{r_amz}" target="_blank" rel="nofollow sponsored noopener noreferrer" class="btn-amz" style="width:100%;">Check Price on Amazon &rarr;</a>
            </div>
        </div>
        """

    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": f"Who should buy the {prod['name']}?",
                "acceptedAnswer": {"@type": "Answer", "text": prod["buy_if"]}
            },
            {
                "@type": "Question",
                "name": f"Who should skip the {prod['name']}?",
                "acceptedAnswer": {"@type": "Answer", "text": prod["skip_if"]}
            }
        ]
    }

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{prod['name']} Review, Specs & Buying Guide | MaisonCurate US</title>
    <meta name="description" content="{prod['summary']} Compare verified specifications, pros, cons, and check live price & stock on Amazon.">
    <link rel="canonical" href="{page_url}">
    <script type="application/ld+json">{json.dumps(schema)}</script>
    <style>
        {get_common_styles()}
        .breadcrumb {{ font-size: 0.84rem; color: var(--slate); margin-bottom: 18px; }}
        .breadcrumb a {{ color: var(--emerald); text-decoration: none; font-weight: 600; }}
        .hero-box {{ background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 30px; margin-bottom: 32px; display: grid; grid-template-columns: 1fr 320px; gap: 28px; align-items: center; }}
        .spec-table {{ width: 100%; border-collapse: collapse; margin: 20px 0 32px; }}
        .spec-table th, .spec-table td {{ border: 1px solid var(--border); padding: 12px 16px; text-align: left; font-size: 0.92rem; }}
        .spec-table th {{ background: var(--surface); width: 34%; color: var(--navy); }}
        .verdict-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(290px, 1fr)); gap: 20px; margin: 24px 0; }}
        .v-box {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 22px; }}
        @media (max-width: 780px) {{ .hero-box {{ grid-template-columns: 1fr; }} }}
    </style>
</head>
<body>
    {build_header_html()}
    <main class="container">
        <div class="breadcrumb">
            <a href="{SITE_URL}/">Home</a> &rsaquo;
            <a href="{SITE_URL}/categories/{prod['cat_slug']}.html">{prod['category']}</a> &rsaquo;
            <a href="{SITE_URL}/categories/{prod['sub_slug']}.html">{prod['subcategory']}</a> &rsaquo;
            <span>{prod['name']}</span>
        </div>

        <section class="hero-box">
            <div>
                <span class="pill">{prod['cat_icon']} {prod['subcategory']} &bull; Amazon Best-Seller Candidate</span>
                <h1 style="font-size:1.95rem;line-height:1.25;margin-bottom:12px;">{prod['name']}</h1>
                <p style="color:var(--slate);font-size:1.02rem;margin-bottom:16px;">{prod['summary']}</p>
                <div class="micro-disclosure">Affiliate Disclosure: As an Amazon Associate I earn from qualifying purchases when you click our links to Amazon.com.</div>
                <div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:12px;">
                    <a href="{amz_url}" target="_blank" rel="nofollow sponsored noopener noreferrer" class="btn-amz">Check Price on Amazon &rarr;</a>
                    <a href="{amz_url}" target="_blank" rel="nofollow sponsored noopener noreferrer" class="btn-outline">View Customer Reviews on Amazon</a>
                </div>
            </div>
            <div style="background:#fff;border:1px solid var(--border);border-radius:14px;padding:24px;text-align:center;">
                <div style="font-size:3.2rem;margin-bottom:10px;">{prod['cat_icon']}</div>
                <div style="font-weight:800;color:var(--navy);margin-bottom:6px;">{prod['brand']} Official Series</div>
                <div style="font-size:0.82rem;color:var(--slate);margin-bottom:16px;">Verified {prod['subcategory']} Specification Profile</div>
                <a href="{amz_url}" target="_blank" rel="nofollow sponsored noopener noreferrer" class="btn-amz" style="width:100%;">View on Amazon &rarr;</a>
            </div>
        </section>

        <div class="verdict-grid">
            <div class="v-box">
                <h3 style="color:var(--emerald-dark);margin-bottom:8px;">Who Should Buy This</h3>
                <p style="font-size:0.93rem;color:var(--slate);">{prod['buy_if']}</p>
            </div>
            <div class="v-box">
                <h3 style="color:#b91c1c;margin-bottom:8px;">Who Should Skip This</h3>
                <p style="font-size:0.93rem;color:var(--slate);">{prod['skip_if']}</p>
            </div>
        </div>

        <h2 style="font-size:1.4rem;margin-top:32px;">Verified Technical Specifications</h2>
        <table class="spec-table">
            <tbody>{specs_rows}</tbody>
        </table>

        <div class="verdict-grid">
            <div class="v-box">
                <h3 style="margin-bottom:10px;">Key Strengths (Pros)</h3>
                <ul style="list-style:none;">{pros_html}</ul>
            </div>
            <div class="v-box">
                <h3 style="margin-bottom:10px;">Considerations (Cons)</h3>
                <ul style="list-style:none;">{cons_html}</ul>
            </div>
        </div>

        <h2 style="font-size:1.4rem;margin:40px 0 18px;">Compare Similar Best-Selling Alternatives</h2>
        <div class="grid-3">{rel_cards}</div>
    </main>
    {build_footer_html(today)}
</body>
</html>"""

    with open(os.path.join(PRODUCTS_DIR, f"{prod['slug']}.html"), "w", encoding="utf-8") as f:
        f.write(html)
    return page_url


def render_review_article(group: list, cycle_num: int, art_idx: int, today: str) -> dict:
    os.makedirs(REVIEWS_DIR, exist_ok=True)
    sub = group[0]["subcategory"]
    cat = group[0]["category"]
    slug = f"best-{slugify(sub)}-buying-guide-c{cycle_num}-{art_idx}"
    title = f"Best {sub} in {today[:4]}: Side-by-Side Comparison & Buying Guide"
    page_url = f"{SITE_URL}/reviews/{slug}.html"

    th_cols = "".join(f"<th>{p['name']}</th>" for p in group)
    spec_keys = list(group[0]["specs"].keys())
    matrix_rows = ""
    for k in spec_keys:
        tds = "".join(f"<td>{p['specs'].get(k, 'Standard')}</td>" for p in group)
        matrix_rows += f"<tr><th>{k}</th>{tds}</tr>"

    cta_tds = "".join(
        f'<td><a href="{make_amazon_url(p["search_query"])}" target="_blank" rel="nofollow sponsored noopener noreferrer" class="btn-amz" style="padding:8px 12px;font-size:0.8rem;">Check Price on Amazon</a></td>'
        for p in group
    )

    reviews_body = ""
    for rank, p in enumerate(group, 1):
        amz_url = make_amazon_url(p["search_query"])
        reviews_body += f"""
        <section style="background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:26px;margin-bottom:24px;">
            <span class="pill">Pick #{rank} &bull; {p['brand']}</span>
            <h2 style="font-size:1.35rem;margin-bottom:10px;"><a href="{SITE_URL}/products/{p['slug']}.html" style="color:var(--navy);text-decoration:none;">{p['name']}</a></h2>
            <p style="color:var(--slate);margin-bottom:12px;">{p['summary']}</p>
            <p style="font-size:0.92rem;margin-bottom:8px;"><strong>Best For:</strong> {p['buy_if']}</p>
            <p style="font-size:0.92rem;margin-bottom:12px;"><strong>When to Skip:</strong> {p['skip_if']}</p>
            <div class="micro-disclosure">As an Amazon Associate I earn from qualifying purchases.</div>
            <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:8px;">
                <a href="{amz_url}" target="_blank" rel="nofollow sponsored noopener noreferrer" class="btn-amz">Check Price on Amazon &rarr;</a>
                <a href="{SITE_URL}/products/{p['slug']}.html" class="btn-outline">Full Spec Breakdown</a>
            </div>
        </section>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | MaisonCurate US</title>
    <meta name="description" content="In-depth editorial comparison of the top 4 {sub}: {', '.join(p['name'] for p in group)}.">
    <link rel="canonical" href="{page_url}">
    <style>
        {get_common_styles()}
        .table-scroll {{ overflow-x: auto; margin: 26px 0 36px; }}
        table {{ width: 100%; border-collapse: collapse; min-width: 700px; }}
        th, td {{ border: 1px solid var(--border); padding: 12px 14px; text-align: left; font-size: 0.88rem; }}
        th {{ background: var(--surface); color: var(--navy); }}
    </style>
</head>
<body>
    {build_header_html()}
    <main class="container">
        <span class="pill">{cat} &rsaquo; {sub} Editorial Comparison</span>
        <h1 style="font-size:2.05rem;margin-bottom:12px;">{title}</h1>
        <p style="color:var(--slate);max-width:840px;margin-bottom:24px;">Selecting the right {sub.lower()} requires comparing verified build materials, thermal or filtration tolerances, and daily maintenance requirements. Below is our side-by-side specification matrix and hands-on buyer suitability guide.</p>

        <div class="table-scroll">
            <table>
                <thead>
                    <tr><th>Specification Attribute</th>{th_cols}</tr>
                </thead>
                <tbody>
                    {matrix_rows}
                    <tr><th>Amazon Availability</th>{cta_tds}</tr>
                </tbody>
            </table>
        </div>

        {reviews_body}
    </main>
    {build_footer_html(today)}
</body>
</html>"""

    with open(os.path.join(REVIEWS_DIR, f"{slug}.html"), "w", encoding="utf-8") as f:
        f.write(html)

    return {
        "slug": slug,
        "title": title,
        "category": cat,
        "subcategory": sub,
        "excerpt": f"Side-by-side specification comparison of {group[0]['name']}, {group[1]['name']}, and 2 more top-ranked {sub.lower()}.",
        "published_at": today,
        "url": page_url
    }


def render_category_and_subcategory_pages(published_prods: list, today: str) -> list:
    os.makedirs(CATEGORIES_DIR, exist_ok=True)
    cat_urls = []

    def make_listing_page(slug: str, heading: str, subtitle: str, items: list):
        cards = ""
        for p in items:
            amz_url = make_amazon_url(p["search_query"])
            cards += f"""
            <article class="card">
                <div>
                    <span class="pill">{p['cat_icon']} {p['subcategory']}</span>
                    <h3 style="font-size:1.1rem;margin-bottom:8px;"><a href="{SITE_URL}/products/{p['slug']}.html" style="color:var(--navy);text-decoration:none;">{p['name']}</a></h3>
                    <p style="font-size:0.88rem;color:var(--slate);margin-bottom:12px;">{p['summary']}</p>
                </div>
                <div>
                    <div class="micro-disclosure">As an Amazon Associate I earn from qualifying purchases.</div>
                    <div style="display:flex;gap:8px;">
                        <a href="{amz_url}" target="_blank" rel="nofollow sponsored noopener noreferrer" class="btn-amz" style="flex:1;">Check Price on Amazon</a>
                        <a href="{SITE_URL}/products/{p['slug']}.html" class="btn-outline">Specs</a>
                    </div>
                </div>
            </article>
            """

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{heading} — Best-Selling Buying Guides | MaisonCurate US</title>
    <meta name="description" content="{subtitle}">
    <link rel="canonical" href="{SITE_URL}/categories/{slug}.html">
    <style>{get_common_styles()}</style>
</head>
<body>
    {build_header_html()}
    <main class="container">
        <h1 style="font-size:2rem;margin-bottom:8px;">{heading}</h1>
        <p style="color:var(--slate);margin-bottom:28px;">{subtitle}</p>
        <div class="grid-3">{cards or '<p>New products in this category are queued for the next 12-hour publication cycle.</p>'}</div>
    </main>
    {build_footer_html(today)}
</body>
</html>"""
        with open(os.path.join(CATEGORIES_DIR, f"{slug}.html"), "w", encoding="utf-8") as f:
            f.write(html)
        cat_urls.append(f"{SITE_URL}/categories/{slug}.html")

    for cat in TAXONOMY:
        c_items = [p for p in published_prods if p["cat_slug"] == cat["cat_slug"]]
        make_listing_page(
            cat["cat_slug"],
            f"{cat['icon']} {cat['category']}",
            f"Browse verified specifications and Amazon best-seller links across {', '.join(s['name'] for s in cat['subcategories'])}.",
            c_items
        )
        for sub in cat["subcategories"]:
            s_items = [p for p in published_prods if p["sub_slug"] == sub["slug"]]
            make_listing_page(
                sub["slug"],
                f"{sub['name']} ({cat['category']})",
                f"Compare top-rated {sub['name'].lower()} with verified specifications and direct Amazon availability.",
                s_items
            )

    return cat_urls


def render_legal_page(today: str):
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>About Us, Privacy Policy, Terms & Affiliate Disclosure | MaisonCurate US</title>
    <link rel="canonical" href="{SITE_URL}/legal.html">
    <style>
        {get_common_styles()}
        .legal-sec {{ background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 28px; margin-bottom: 24px; }}
        .legal-sec h2 {{ margin-bottom: 10px; color: var(--navy); }}
        .legal-sec p {{ color: var(--slate); margin-bottom: 10px; }}
    </style>
</head>
<body>
    {build_header_html()}
    <main class="container">
        <div class="legal-sec" id="disclosure">
            <h2>Amazon Associates Affiliate Disclosure</h2>
            <p><strong>As an Amazon Associate I earn from qualifying purchases.</strong></p>
            <p>MaisonCurate US is a participant in the Amazon Services LLC Associates Program, an affiliate advertising program designed to provide a means for sites to earn advertising fees by advertising and linking to Amazon.com. Amazon and the Amazon logo are trademarks of Amazon.com, Inc. or its affiliates.</p>
        </div>
        <div class="legal-sec" id="about">
            <h2>About MaisonCurate US & Contact</h2>
            <p>MaisonCurate US is an independent US consumer product discovery and specification comparison platform focused on high-utility home, kitchen, water filtration, climate, and sleep systems. We do not accept direct payments from manufacturers to alter technical specifications.</p>
            <p>Editorial Contact: editorial@maisoncurate-us.github.io</p>
        </div>
        <div class="legal-sec" id="privacy">
            <h2>Privacy Policy</h2>
            <p>We do not collect personal payment data or process direct checkouts. When you click a "Check Price on Amazon" or "View on Amazon" button, you are directed to Amazon.com where your session is governed by Amazon's Privacy Notice.</p>
        </div>
        <div class="legal-sec" id="terms">
            <h2>Terms of Use</h2>
            <p>All product specifications are provided for informational comparison. Always verify current pricing, warranty documentation, and stock status directly on Amazon.com prior to purchase.</p>
        </div>
    </main>
    {build_footer_html(today)}
</body>
</html>"""
    with open(os.path.join(DOCS_DIR, "legal.html"), "w", encoding="utf-8") as f:
        f.write(html)


def render_storefront_homepage(published_prods: list, reviews: list, today: str):
    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(os.path.join(DOCS_DIR, ".nojekyll"), "w", encoding="utf-8") as f:
        f.write("")

    latest_prods = list(reversed(published_prods))[:48]
    latest_revs = list(reversed(reviews))[:12]

    cat_tiles = ""
    for c in TAXONOMY:
        sub_pills = " &bull; ".join(s["name"] for s in c["subcategories"])
        cat_tiles += f"""
        <a href="{SITE_URL}/categories/{c['cat_slug']}.html" class="card" style="text-decoration:none;color:inherit;">
            <div>
                <div style="font-size:2rem;margin-bottom:8px;">{c['icon']}</div>
                <h3 style="font-size:1.1rem;color:var(--navy);margin-bottom:6px;">{c['category']}</h3>
                <p style="font-size:0.83rem;color:var(--slate);">{sub_pills}</p>
            </div>
            <span style="margin-top:14px;font-size:0.84rem;font-weight:700;color:var(--emerald);">Explore Department &rarr;</span>
        </a>
        """

    prod_cards = ""
    for p in latest_prods:
        amz_url = make_amazon_url(p["search_query"])
        first_spec_k = list(p["specs"].keys())[0]
        first_spec_v = list(p["specs"].values())[0]
        prod_cards += f"""
        <article class="card prod-item" data-cat="{p['cat_slug']}">
            <div>
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                    <span class="pill" style="margin:0;">{p['cat_icon']} {p['subcategory']}</span>
                    <span style="font-size:0.75rem;font-weight:700;color:var(--amber);">★ Best-Seller Tier</span>
                </div>
                <h3 style="font-size:1.1rem;margin-bottom:8px;"><a href="{SITE_URL}/products/{p['slug']}.html" style="color:var(--navy);text-decoration:none;">{p['name']}</a></h3>
                <p style="font-size:0.87rem;color:var(--slate);margin-bottom:10px;">{p['summary']}</p>
                <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:8px 10px;font-size:0.8rem;color:var(--navy);">
                    <strong>{first_spec_k}:</strong> {first_spec_v}
                </div>
            </div>
            <div style="margin-top:14px;">
                <div class="micro-disclosure">As an Amazon Associate I earn from qualifying purchases.</div>
                <div style="display:flex;gap:8px;">
                    <a href="{amz_url}" target="_blank" rel="nofollow sponsored noopener noreferrer" class="btn-amz" style="flex:1;">Check Price on Amazon</a>
                    <a href="{SITE_URL}/products/{p['slug']}.html" class="btn-outline">Review</a>
                </div>
            </div>
        </article>
        """

    rev_cards = ""
    for r in latest_revs:
        rev_cards += f"""
        <article class="card">
            <div>
                <span class="pill">{r['category']}</span>
                <h3 style="font-size:1.12rem;margin-bottom:8px;"><a href="{SITE_URL}/reviews/{r['slug']}.html" style="color:var(--navy);text-decoration:none;">{r['title']}</a></h3>
                <p style="font-size:0.88rem;color:var(--slate);">{r['excerpt']}</p>
            </div>
            <div style="margin-top:16px;">
                <a href="{SITE_URL}/reviews/{r['slug']}.html" class="btn-outline" style="width:100%;">Read 4-Product Comparison &rarr;</a>
            </div>
        </article>
        """

    filter_buttons = '<button class="f-btn active" onclick="filterDept(\'all\', this)">All Departments</button>'
    for c in TAXONOMY:
        filter_buttons += f'<button class="f-btn" onclick="filterDept(\'{c["cat_slug"]}\', this)">{c["icon"]} {c["category"]}</button>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MaisonCurate US — Home, Kitchen & Smart Living Best-Sellers Storefront</title>
    <meta name="description" content="Discover Amazon's #1 best-selling air fryers, clad stainless cookware, tankless reverse osmosis water filters, True HEPA air purifiers, and hybrid mattresses.">
    <link rel="canonical" href="{SITE_URL}/">
    <style>
        {get_common_styles()}
        .hero-banner {{ background: linear-gradient(135deg, #064e3b 0%, #0f172a 100%); color: #ffffff; padding: 56px 20px; }}
        .hero-inner {{ max-width: 1240px; margin: 0 auto; display: grid; grid-template-columns: 1.3fr 0.7fr; gap: 32px; align-items: center; }}
        .hero-badge {{ display: inline-block; background: rgba(16,185,129,0.2); border: 1px solid #34d399; color: #6ee7b7; font-size: 0.78rem; font-weight: 700; padding: 5px 12px; border-radius: 999px; margin-bottom: 14px; }}
        .hero-banner h1 {{ font-size: 2.4rem; line-height: 1.2; margin-bottom: 14px; }}
        .search-bar {{ display: flex; gap: 10px; margin-top: 22px; max-width: 600px; }}
        .search-bar input {{ flex: 1; padding: 14px 18px; border-radius: 10px; border: none; font-size: 1rem; outline: none; }}
        .filter-row {{ display: flex; gap: 10px; flex-wrap: wrap; margin: 22px 0; }}
        .f-btn {{ background: var(--surface); border: 1px solid var(--border); color: var(--navy); padding: 8px 14px; border-radius: 999px; font-size: 0.84rem; font-weight: 600; cursor: pointer; }}
        .f-btn.active, .f-btn:hover {{ background: var(--emerald); color: #fff; border-color: var(--emerald); }}
        .sec-head {{ display: flex; justify-content: space-between; align-items: baseline; margin: 48px 0 20px; border-bottom: 2px solid var(--border); padding-bottom: 10px; flex-wrap: wrap; gap: 10px; }}
        @media (max-width: 820px) {{ .hero-inner {{ grid-template-columns: 1fr; }} .hero-banner h1 {{ font-size: 1.85rem; }} }}
    </style>
</head>
<body>
    {build_header_html()}
    <section class="hero-banner">
        <div class="hero-inner">
            <div>
                <span class="hero-badge">UPDATED EVERY 12 HOURS &bull; VERIFIED BEST-SELLER CATALOG</span>
                <h1>Curated Home, Culinary & Healthy Living Systems for US Households</h1>
                <p style="color:#cbd5e1;font-size:1.05rem;">Compare verified specifications across Dual-Zone Air Fryers, 5-Ply Stainless Cookware, Tankless Reverse Osmosis Filters, True HEPA Purifiers, and CertiPUR-US Hybrid Mattresses.</p>
                <div class="search-bar">
                    <input type="text" id="liveSearch" placeholder="Search product, brand, or specification (e.g. Ninja, Breville, Reverse Osmosis, HEPA)..." onkeyup="runSearch()">
                </div>
            </div>
            <div style="background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.18);border-radius:16px;padding:24px;">
                <div style="font-size:0.8rem;color:#6ee7b7;font-weight:700;text-transform:uppercase;margin-bottom:6px;">Storefront Telemetry</div>
                <div style="font-size:1.6rem;font-weight:900;margin-bottom:4px;">{len(published_prods)} Verified Products</div>
                <div style="font-size:0.9rem;color:#cbd5e1;margin-bottom:14px;">{len(reviews)} Side-by-Side Buying Guides</div>
                <a href="#featured" class="btn-amz" style="width:100%;background:#10b981;">Browse Featured Best-Sellers &darr;</a>
            </div>
        </div>
    </section>

    <main class="container">
        <div class="sec-head" id="categories">
            <h2>Shop by Department & Subcategory</h2>
            <span style="font-size:0.85rem;color:var(--slate);">6 Core Departments &bull; 18 Specialized Subcategories</span>
        </div>
        <div class="grid-3">{cat_tiles}</div>

        <div class="sec-head" id="featured">
            <h2>Featured Amazon Best-Selling Products</h2>
            <span style="font-size:0.85rem;color:var(--slate);">Auto-Updated Every 12 Hours</span>
        </div>
        <div class="filter-row">{filter_buttons}</div>
        <div class="grid-3" id="productsContainer">{prod_cards}</div>

        <div class="sec-head" id="reviews">
            <h2>Latest 12-Hour Comparative Review Articles</h2>
            <span style="font-size:0.85rem;color:var(--slate);">Side-by-Side 4-Model Buying Guides</span>
        </div>
        <div class="grid-3">{rev_cards}</div>
    </main>

    {build_footer_html(today)}
    <script>
        function runSearch() {{
            const q = document.getElementById('liveSearch').value.toLowerCase();
            document.querySelectorAll('.prod-item').forEach(card => {{
                card.style.display = card.innerText.toLowerCase().includes(q) ? '' : 'none';
            }});
        }}
        function filterDept(catSlug, btn) {{
            document.querySelectorAll('.f-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            document.querySelectorAll('.prod-item').forEach(card => {{
                if (catSlug === 'all' || card.getAttribute('data-cat') === catSlug) {{
                    card.style.display = '';
                }} else {{
                    card.style.display = 'none';
                }}
            }});
        }}
    </script>
</body>
</html>"""

    with open(os.path.join(DOCS_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)


def build_seo_feeds_and_ping(published_prods: list, reviews: list, cat_urls: list, new_urls: list, today: str):
    # 1. Buat Sitemap XML
    urls_xml = f"  <url><loc>{SITE_URL}/</loc><lastmod>{today}</lastmod><changefreq>daily</changefreq><priority>1.0</priority></url>\n"
    urls_xml += f"  <url><loc>{SITE_URL}/legal.html</loc><lastmod>{today}</lastmod><changefreq>monthly</changefreq><priority>0.5</priority></url>\n"

    for c_url in cat_urls:
        urls_xml += f"  <url><loc>{c_url}</loc><lastmod>{today}</lastmod><changefreq>daily</changefreq><priority>0.9</priority></url>\n"
    for r in reviews:
        urls_xml += f"  <url><loc>{r['url']}</loc><lastmod>{r['published_at']}</lastmod><changefreq>weekly</changefreq><priority>0.9</priority></url>\n"
    for p in published_prods:
        urls_xml += f"  <url><loc>{SITE_URL}/products/{p['slug']}.html</loc><lastmod>{p.get('published_at', today)}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>\n"

    sitemap = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls_xml}</urlset>'
    with open(os.path.join(DOCS_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sitemap)

    # 2. Buat RSS 2.0 Feed (feed.xml) dengan hub WebSub untuk Googlebot Instant Discovery
    rss_items = ""
    for r in list(reversed(reviews))[:15]:
        rss_items += f"""    <item>
      <title>{r['title']}</title>
      <link>{r['url']}</link>
      <guid>{r['url']}</guid>
      <description>{r['excerpt']}</description>
    </item>\n"""
    for p in list(reversed(published_prods))[:25]:
        p_url = f"{SITE_URL}/products/{p['slug']}.html"
        rss_items += f"""    <item>
      <title>{p['name']}</title>
      <link>{p_url}</link>
      <guid>{p_url}</guid>
      <description>{p['summary']}</description>
    </item>\n"""

    rss_xml = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>MaisonCurate US — Home &amp; Kitchen Best-Sellers</title>
    <link>{SITE_URL}/</link>
    <description>Automated 12-Hour Home &amp; Kitchen Buying Guides and Product Reviews</description>
    <atom:link href="https://pubsubhubbub.appspot.com/" rel="hub" />
    <atom:link href="{SITE_URL}/feed.xml" rel="self" type="application/rss+xml" />
{rss_items}  </channel>
</rss>"""
    with open(os.path.join(DOCS_DIR, "feed.xml"), "w", encoding="utf-8") as f:
        f.write(rss_xml)

    # 3. Buat robots.txt & kunci verifikasi IndexNow
    with open(os.path.join(DOCS_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")

    with open(os.path.join(DOCS_DIR, f"{INDEXNOW_KEY}.txt"), "w", encoding="utf-8") as f:
        f.write(INDEXNOW_KEY)

    if "username.github.io" in SITE_URL or not new_urls:
        return

    # 4. Ping IndexNow ke Bing, Yahoo, DuckDuckGo, Yandex, Naver & Seznam
    host = SITE_URL.replace("https://", "").replace("http://", "").split("/")[0]
    indexnow_payload = {
        "host": host,
        "key": INDEXNOW_KEY,
        "keyLocation": f"{SITE_URL}/{INDEXNOW_KEY}.txt",
        "urlList": new_urls[:100]
    }
    for endpoint in ["https://api.indexnow.org/indexnow", "https://www.bing.com/indexnow", "https://yandex.com/indexnow"]:
        try:
            r = requests.post(endpoint, json=indexnow_payload, timeout=12)
            print(f"[SEO] IndexNow Ping ({endpoint}) HTTP: {r.status_code}")
        except Exception as e:
            print(f"[WARN] IndexNow Ping gagal pada {endpoint}: {e}")

    # 5. Ping Google WebSub Hub (PubSubHubbub) untuk pengindeksan cepat Googlebot
    try:
        r_google = requests.post(
            "https://pubsubhubbub.appspot.com/",
            data={"hub.mode": "publish", "hub.url": f"{SITE_URL}/feed.xml"},
            timeout=12
        )
        print(f"[SEO] Google WebSub Hub Ping HTTP: {r_google.status_code}")
    except Exception as e:
        print(f"[WARN] Google WebSub Ping gagal: {e}")


def main():
    state = init_or_load_state()
    products = state["products"]
    reviews = state["reviews"]
    cycle = state.get("cycle_count", 0) + 1
    state["cycle_count"] = cycle
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    unpublished = [p for p in products if not p.get("published")]
    # Jika seluruh antrean sudah dipublikasikan setelah berbulan-bulan, reset pointer agar tetap memperbarui edisi
    if len(unpublished) < 20:
        for p in products:
            p["published"] = False
        unpublished = products

    batch_20 = unpublished[:20]
    new_urls = [f"{SITE_URL}/"]

    for p in batch_20:
        p["published"] = True
        p["published_at"] = today

    published_prods = [p for p in products if p.get("published")]

    # Render seluruh halaman produk aktif
    for p in published_prods:
        same_sub = [x for x in published_prods if x["sub_slug"] == p["sub_slug"]]
        url = render_product_page(p, same_sub, today)
        if p in batch_20:
            new_urls.append(url)

    # Buat 5 artikel review komparatif baru (masing-masing membandingkan 4 produk dari batch 20 ini)
    for i in range(0, len(batch_20), 4):
        group = batch_20[i:i + 4]
        if len(group) == 4:
            rev_meta = render_review_article(group, cycle, (i // 4) + 1, today)
            reviews.append(rev_meta)
            new_urls.append(rev_meta["url"])

    cat_urls = render_category_and_subcategory_pages(published_prods, today)
    render_legal_page(today)
    render_storefront_homepage(published_prods, reviews, today)

    save_state(state)
    build_seo_feeds_and_ping(published_prods, reviews, cat_urls, new_urls, today)

    print(f"[SUCCESS] Siklus #{cycle}: +20 Produk Baru & +5 Artikel Review dipublikasikan. Total Katalog Aktif: {len(published_prods)} produk.")


if __name__ == "__main__":
    main()
