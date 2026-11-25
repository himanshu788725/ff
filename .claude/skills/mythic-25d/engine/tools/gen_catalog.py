"""Generate data/characters.json, animals.json, birds.json.

Run:  python tools/gen_catalog.py
Each character = template (by category) + per-character overrides.  Colours for
crowd/generic categories vary deterministically by id so no two look alike.
Edit this file (or add a project-level characters.json) to extend the cast.
"""
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "mythic25d" / "data"

DHOTI_PALETTE = [["vermilion", "dots", "cream"], ["mustard", "dots", "vermilion"], ["saffron", "stripes", "maroon"],
                 ["maroon", "floral", "gold"], ["#2f6a8a", "dots", "cream"], ["#5a7a3a", "checks", "#3a5a2a"],
                 ["#e8d8b4", "stripes", "vermilion"], ["#8a3a6a", "dots", "gold"], ["#c8642a", "zigzag", "cream"],
                 ["#3a5a7a", "chevron", "gold"], ["teal", "dots", "mustard"], ["#a8743a", "floral", "cream"]]
SAREE_PALETTE = [["vermilion", "floral", "gold"], ["maroon", "dots", "gold"], ["#2f6a3a", "floral", "gold"],
                 ["#e8a03a", "dots", "maroon"], ["#3a4a8a", "floral", "gold"], ["#c8467a", "dots", "gold"],
                 ["#f0e0c0", "stripes", "vermilion"], ["#7a2a6a", "floral", "gold"], ["teal", "dots", "gold"],
                 ["saffron", "checks", "maroon"]]
SASH = ["mustard", "vermilion", "teal", "saffron", "cream", "#2f6a8a", "maroon", "leaf"]
SKINS = ["skin_tan", "skin_light", "skin_brown", "skin_tan", "skin_light", "skin_dark"]
RAKSHASA_SKINS = ["#4a5a3a", "#5a4a6a", "#3a3a4a", "#6a2a2a", "#2a4a4a", "#5a3a2a", "#4a2a4a", "#3a4a2a"]
VANARA_SKINS = ["monkey", "#c8843a", "#b8743a", "#d8a85a", "#a86a3a", "#e0b060", "#9a5a2a"]


def pick(lst, key, salt=""):
    h = int(hashlib.md5((key + salt).encode()).hexdigest()[:8], 16)
    return lst[h % len(lst)]


TEMPLATES = {
    "avatar": dict(skin="krishna", crown="kirita", dhoti=["mustard", "dots", "vermilion"], sash="vermilion",
                   tilak="vaishnav", halo=True, pearls=True),
    "deva": dict(skin="skin_light", crown="kirita", dhoti=["saffron", "dots", "cream"], sash="mustard", halo=True),
    "devi": dict(female=True, skin="skin_light", crown="tiara", halo=True, pearls=True),
    "rishi": dict(build="old", skin="skin_light", crown="jata", beard="long", mustache=None, lower="valkal", rudraksha=True,
                  sash=None, necklace=False, tilak="shaiva", items={"f": "danda", "b": "kamandalu"}),
    "muni": dict(build="slim", skin="skin_tan", crown="jata", beard="short", beard_color="black", mustache=None,
                 lower="valkal", rudraksha=True, sash=None, necklace=False, tilak="shaiva", items={"f": "mala"}),
    "brahmin": dict(build="slim", skin="skin_light", crown="shikha", hair="bald", janeu=True, dhoti=["#f0e8d4", "stripes", "vermilion"],
                    sash="cream", tilak="vaishnav", necklace=False, mustache=None, items={"f": "pothi"}),
    "king": dict(crown="kirita", sash="mustard", mustache="curl", pearls=True),
    "queen": dict(female=True, crown="tiara", pearls=True),
    "prince": dict(crown="kirita_low", mustache=None, sash="mustard"),
    "princess": dict(female=True, crown="tiara"),
    "warrior": dict(crown="kirita_low", armor="#b8a070", mustache="curl", items={"f": "khadga", "b": "dhal"}, straps=True),
    "rakshasa": dict(build="giant", crown="horns", fangs=True, eye="round", angry=True, mustache="big",
                     dhoti=["maroon", "scales", "gold"], sash=None, items={"f": "khadga"}),
    "asura": dict(build="heavy", crown="spiky", fangs=True, eye="round", angry=True, mustache="big",
                  dhoti=["#3a2a4a", "zigzag", "gold"], sash="maroon", items={"f": "gada"}),
    "rakshasi": dict(female=True, build="female", crown="spiky", fangs=True, eye="round", angry=True,
                     saree=["#3a2a2a", "zigzag", "#8a2a1a"]),
    "vanara": dict(head="monkey", tail=True, crown="kirita_low", janeu=True, items={"f": "gada"}),
    "riksha": dict(head="bear", skin="bear", crown="kirita_low", beard=True, items={"f": "gada"}),
    "naga": dict(lower="serpent", crown="hoods", hoods=5, skin="#6a9a7a", tail_color="#3f7a48"),
    "nagin": dict(female=True, lower="serpent", crown="hoods", hoods=3, skin="#7aa88a", tail_color="#3f7a48"),
    "apsara": dict(female=True, crown="tiara", saree=["#e89ab0", "floral", "gold"], choli="#f0c0c8", halo=False),
    "gandharva": dict(crown="kirita_low", items={"f": "veena"}, dhoti=["#6a4a8a", "dots", "gold"], sash="mint"),
    "yaksha": dict(build="heavy", crown="turban", dhoti=["mustard", "checks", "maroon"], items={"f": "bag"}),
    "commoner": dict(crown="turban", necklace=False, sash="cream", mustache="plain"),
    "woman": dict(female=True, crown="veil", pearls=False),
    "child": dict(build="child", crown="none", mustache=None, necklace=True),
    "soldier": dict(crown="helmet", armor="#9a9488", mustache="curl", items={"f": "spear", "b": "dhal"}),
    "gana": dict(build="heavy", crown="jata", fangs=True, eye="round", skin="#6a6a8a", lower="tiger", items={"f": "trishul"}),
}

C = []  # (id, hi, en, cat, template, overrides)


def add(cat, tpl, rows):
    for r in rows:
        id_, hi, en = r[:3]
        ov = r[3] if len(r) > 3 else {}
        C.append((id_, hi, en, cat, tpl, ov))


# ------------------------------------------------------------------ Tridev & Tridevi
add("tridev", "deva", [
    ("brahma", "ब्रह्मा", "Brahma", dict(skin="#e0b060", heads=["human", "human"], beard="long", mustache=None, arms=4,
                                        extra_items=["kamandalu", "pothi"], items={"f": "mala", "b": "padma"}, crown="kirita",
                                        dhoti=["#f0e0c0", "dots", "vermilion"])),
    ("vishnu", "विष्णु", "Vishnu", dict(skin="krishna", arms=4, extra_items=["chakra", "shankh"], items={"f": "gada", "b": "padma"},
                                       dhoti=["mustard", "dots", "vermilion"], tilak="vaishnav", pearls=True)),
    ("shiva", "शिव", "Shiva", dict(skin="shiva", crown="jata_shiva", lower="tiger", snake=True, rudraksha=True, mustache=None,
                                  third_eye=True, items={"f": "trishul", "b": "damru"}, sash=None, tilak="shaiva", necklace=False)),
])
add("tridevi", "devi", [
    ("saraswati", "सरस्वती", "Saraswati", dict(skin="#f0dcc0", saree=["#f6efdf", "dots", "gold"], choli="#f0c860", arms=4,
                                               extra_items=["pothi", "mala"], items={"f": "veena"}, crown="tiara")),
    ("lakshmi", "लक्ष्मी", "Lakshmi", dict(skin="#e8b878", saree=["vermilion", "floral", "gold"], arms=4,
                                         extra_items=["padma", "padma"], items={"f": "kalash", "b": "abhaya"})),
    ("parvati", "पार्वती", "Parvati", dict(skin="#e0a878", saree=["#2f6a3a", "floral", "gold"], items={"f": "padma"})),
])
# ------------------------------------------------------------------ Dashavatar & Vishnu forms
add("avatar", "avatar", [
    ("matsya", "मत्स्य अवतार", "Matsya", dict(lower="fish", arms=4, extra_items=["chakra", "shankh"], items={"f": "gada"}, tail_color="#e8833a")),
    ("kurma", "कूर्म अवतार", "Kurma", dict(lower="fish", tail_color="#6a7a3a", arms=4, extra_items=["chakra", "shankh"], items={"f": "gada"})),
    ("varaha", "वराह अवतार", "Varaha", dict(head="boar", skin="#7a6a6a", arms=4, extra_items=["chakra", "shankh"], items={"f": "gada"})),
    ("narasimha", "नरसिंह अवतार", "Narasimha", dict(head="lion", skin="#e0a040", arms=4, extra_items=["chakra", "shankh"],
                                                    items={"f": "abhaya"}, crown="kirita", angry=True)),
    ("vamana", "वामन अवतार", "Vamana", dict(build="child", crown="shikha", hair="bald", janeu=True, items={"f": "chhatra", "b": "kamandalu"},
                                            dhoti=["#f0e8d4", "stripes", "vermilion"], halo=True)),
    ("trivikrama", "त्रिविक्रम", "Trivikrama", dict(scale=1.35, arms=4, extra_items=["chakra", "shankh"], items={"f": "gada"})),
    ("parashurama", "परशुराम", "Parashurama", dict(skin="skin_tan", crown="jata", beard="short", beard_color="black", lower="valkal",
                                                   items={"f": "parashu", "b": "bow"}, halo=False, mustache="curl")),
    ("rama", "श्रीराम", "Shri Ram", dict(skin="rama", items={"f": "bow", "b": "arrow"}, halo=False)),
    ("krishna", "श्रीकृष्ण", "Shri Krishna", dict(skin="krishna", crown="peacock", items={"f": "bansuri"}, halo=False,
                                                  dhoti=["mustard", "dots", "vermilion"], sash="vermilion", mustache=None)),
    ("krishna_chakra", "सुदर्शनधारी कृष्ण", "Krishna with Sudarshan", dict(skin="krishna", crown="peacock", items={"f": "sudarshan"},
                                                                          mustache=None)),
    ("krishna_virat", "विराट रूप कृष्ण", "Krishna Vishwaroop", dict(skin="krishna", crown="peacock", arms=10, scale=1.4,
                                                                   heads=["human", "human", "human", "human"],
                                                                   extra_items=["chakra", "shankh", "gada", "padma", "khadga", "bow",
                                                                                "trishul", "vajra"], mustache=None)),
    ("balarama", "बलराम", "Balarama", dict(skin="#f0e6d0", items={"f": "hala", "b": "gada"}, dhoti=["#2f4a8a", "dots", "cream"], halo=False)),
    ("buddha", "बुद्ध", "Buddha", dict(skin="#e0b070", crown="bun", hair="short", lower="valkal", items={"f": "abhaya"},
                                        sash="saffron", mustache=None, necklace=False)),
    ("kalki", "कल्कि", "Kalki", dict(skin="skin_light", items={"f": "khadga", "b": "dhal"}, armor="#c8b060", halo=False)),
    ("mohini", "मोहिनी", "Mohini", dict(female=True, skin="#e8c898", crown="tiara", saree=["#e89ab0", "floral", "gold"],
                                        items={"f": "kalash"})),
    ("hayagriva", "हयग्रीव", "Hayagriva", dict(head="horse", skin="#f0e6d8", arms=4, extra_items=["chakra", "shankh"], items={"f": "pothi"})),
    ("dhanvantari", "धन्वन्तरि", "Dhanvantari", dict(arms=4, extra_items=["chakra", "shankh"], items={"f": "kalash", "b": "pothi"})),
    ("dattatreya", "दत्तात्रेय", "Dattatreya", dict(skin="skin_light", crown="jata", heads=["human", "human"], arms=6,
                                                    extra_items=["trishul", "chakra", "kamandalu", "damru"], items={"f": "mala"},
                                                    lower="valkal", halo=True)),
    ("venkateswara", "वेंकटेश्वर", "Venkateswara", dict(skin="#2f3a6a", arms=4, extra_items=["chakra", "shankh"], items={"f": "varada"})),
    ("jagannath", "जगन्नाथ", "Jagannath", dict(skin="#1e1a20", build="heavy", crown="kirita_low", eye="round", items={})),
    ("vithoba", "विठोबा", "Vitthal", dict(skin="#2a2a3a", crown="kirita_low", items={}, mustache=None)),
    ("narayana", "नारायण", "Narayana", dict(arms=4, extra_items=["chakra", "shankh"], items={"f": "gada", "b": "padma"})),
    ("bal_krishna", "बाल कृष्ण", "Bal Krishna", dict(build="child", crown="peacock", items={"f": "modak"}, halo=False, mustache=None)),
    ("ram_lalla", "रामलला", "Ram Lalla", dict(build="child", skin="rama", items={"f": "bow"}, halo=False, mustache=None)),
])
# ------------------------------------------------------------------ Shiva family & forms
add("shiva_parivar", "deva", [
    ("nataraja", "नटराज", "Nataraja", dict(skin="shiva", crown="jata_shiva", lower="tiger", arms=4, extra_items=["damru", "abhaya"],
                                         snake=True, third_eye=True, mustache=None, items={})),
    ("rudra", "रुद्र", "Rudra", dict(skin="#7a8aa0", crown="jata_shiva", lower="tiger", angry=True, eye="round", items={"f": "trishul"})),
    ("mahakal", "महाकाल", "Mahakal", dict(skin="#2a2a3a", crown="jata_shiva", lower="tiger", mundamala=True, angry=True, items={"f": "trishul"})),
    ("neelkanth", "नीलकंठ", "Neelkanth", dict(skin="#5a7aa8", crown="jata_shiva", lower="tiger", snake=True, items={"f": "trishul"})),
    ("bhairava", "भैरव", "Bhairava", dict(skin="#2a2a3a", crown="jata", fangs=True, eye="round", angry=True, mundamala=True,
                                          lower="tiger", arms=4, extra_items=["damru", "pasha"], items={"f": "trishul", "b": "khadga"})),
    ("kala_bhairava", "काल भैरव", "Kaal Bhairav", dict(skin="#1e1e28", crown="jata", fangs=True, eye="round", mundamala=True,
                                                     lower="tiger", items={"f": "trishul"})),
    ("virabhadra", "वीरभद्र", "Virabhadra", dict(skin="#3a3a4a", crown="flames", fangs=True, eye="round", angry=True, arms=8,
                                               extra_items=["trishul", "khadga", "damru", "bow", "arrow", "dhal"], items={"f": "gada"})),
    ("dakshinamurti", "दक्षिणामूर्ति", "Dakshinamurti", dict(skin="shiva", crown="jata_shiva", lower="tiger", items={"f": "pothi"})),
    ("pashupati", "पशुपति", "Pashupati", dict(skin="shiva", crown="jata_shiva", lower="tiger", heads=["human", "human"], items={"f": "trishul"})),
    ("ganesha", "गणेश", "Ganesha", dict(head="elephant", skin="#e3a07a", build="heavy", arms=4, extra_items=["pasha", "ankusha"],
                                       items={"f": "modak", "b": "abhaya"}, dhoti=["vermilion", "floral", "gold"])),
    ("bal_ganesha", "बाल गणेश", "Bal Ganesha", dict(head="elephant", skin="#e8b08a", build="child", items={"f": "modak"}, halo=False)),
    ("kartikeya", "कार्तिकेय", "Kartikeya", dict(skin="skin_tan", heads=["human", "human", "human", "human"], items={"f": "shakti", "b": "dhal"},
                                                  mustache=None, armor="#c8a050")),
    ("murugan", "मुरुगन", "Murugan", dict(skin="skin_brown", items={"f": "shakti"}, mustache=None, crown="kirita")),
    ("riddhi", "ऋद्धि", "Riddhi", dict(female=True, saree=["#e8a03a", "dots", "maroon"], halo=False, items={"f": "chamara"})),
    ("siddhi", "सिद्धि", "Siddhi", dict(female=True, saree=["#2f6a3a", "dots", "gold"], halo=False, items={"f": "chamara"})),
    ("ashok_sundari", "अशोक सुंदरी", "Ashok Sundari", dict(female=True, saree=["#f2a2b8", "floral", "gold"], halo=False)),
    ("nandi_gana", "नंदी", "Nandi (gana)", dict(head="buffalo", skin="#f0e8d8", horn="#e8dcc0", crown="kirita_low", items={"f": "trishul"}, halo=False)),
    ("bhringi", "भृंगी", "Bhringi", dict(build="old", skin="#9a8a7a", crown="jata", lower="valkal", items={"f": "trishul"}, halo=False)),
    ("ganas", "शिवगण", "Shiva Gana", dict(build="heavy", crown="jata", fangs=True, eye="round", skin="#6a6a8a", lower="tiger",
                                          items={"f": "trishul"}, halo=False)),
])
# ------------------------------------------------------------------ Devi forms
DEVI = [
    ("durga", "दुर्गा", "Durga", dict(skin="#e8a868", saree=["vermilion", "floral", "gold"], arms=8,
                                     extra_items=["chakra", "shankh", "khadga", "bow", "gada", "padma"], items={"f": "trishul", "b": "abhaya"})),
    ("kali", "काली", "Kali", dict(skin="#1e2030", saree=["#3a1a1a", "zigzag", "#8a1a1a"], mundamala=True, fangs=True, eye="round",
                                   angry=True, arms=4, extra_items=["khadga", "abhaya"], items={"f": "trishul"}, hair="long", crown="tiara")),
    ("mahakali", "महाकाली", "Mahakali", dict(skin="#141826", mundamala=True, fangs=True, eye="round", angry=True, arms=10,
                                           extra_items=["khadga", "trishul", "chakra", "gada", "bow", "arrow", "pasha", "shankh"],
                                           saree=["#2a1010", "zigzag", "maroon"])),
    ("shailaputri", "शैलपुत्री", "Shailaputri", dict(skin="#f0d0a8", items={"f": "trishul", "b": "padma"}, saree=["#f6efdf", "dots", "vermilion"])),
    ("brahmacharini", "ब्रह्मचारिणी", "Brahmacharini", dict(skin="#f0d8b8", items={"f": "mala", "b": "kamandalu"},
                                                          saree=["#f6efdf", "stripes", "saffron"], crown="bun")),
    ("chandraghanta", "चंद्रघंटा", "Chandraghanta", dict(arms=10, extra_items=["trishul", "gada", "khadga", "kamandalu", "bow", "arrow",
                                                                             "padma", "mala"], items={"f": "abhaya"}, saree=["#e8a03a", "dots", "maroon"])),
    ("kushmanda", "कूष्माण्डा", "Kushmanda", dict(arms=8, extra_items=["kamandalu", "bow", "arrow", "padma", "kalash", "chakra"],
                                               items={"f": "gada", "b": "mala"}, saree=["#e8833a", "floral", "gold"])),
    ("skandamata", "स्कंदमाता", "Skandamata", dict(arms=4, extra_items=["padma", "padma"], items={"f": "abhaya"}, saree=["#f6efdf", "floral", "gold"])),
    ("katyayani", "कात्यायनी", "Katyayani", dict(arms=4, extra_items=["khadga", "padma"], items={"f": "abhaya"}, saree=["#c8321f", "floral", "gold"])),
    ("kalaratri", "कालरात्रि", "Kalaratri", dict(skin="#16141e", fangs=True, eye="round", arms=4, extra_items=["khadga", "vajra"],
                                               items={"f": "abhaya"}, saree=["#1e1e2a", "zigzag", "#5a1a1a"], hair="long")),
    ("mahagauri", "महागौरी", "Mahagauri", dict(skin="#f6eee0", arms=4, extra_items=["trishul", "damru"], items={"f": "abhaya"},
                                             saree=["#f6efdf", "dots", "gold"])),
    ("siddhidatri", "सिद्धिदात्री", "Siddhidatri", dict(arms=4, extra_items=["chakra", "gada"], items={"f": "shankh", "b": "padma"},
                                                     saree=["#c8321f", "floral", "gold"])),
    ("tara", "तारा", "Tara (Mahavidya)", dict(skin="#2a4a7a", mundamala=True, fangs=True, arms=4, extra_items=["khadga", "padma"],
                                             items={"f": "kamandalu"}, saree=["#1e2a3a", "dots", "gold"])),
    ("tripura_sundari", "त्रिपुर सुंदरी", "Tripura Sundari", dict(skin="#e8a888", arms=4, extra_items=["pasha", "ankusha"],
                                                                  items={"f": "bow", "b": "arrow"}, saree=["vermilion", "floral", "gold"])),
    ("bhuvaneshwari", "भुवनेश्वरी", "Bhuvaneshwari", dict(skin="#f0c090", arms=4, extra_items=["pasha", "ankusha"], items={"f": "abhaya"},
                                                         saree=["#c8467a", "floral", "gold"])),
    ("bhairavi", "भैरवी", "Bhairavi", dict(skin="#c84a2a", arms=4, extra_items=["mala", "pothi"], items={"f": "abhaya"},
                                         saree=["#8a1a1a", "dots", "gold"], mundamala=True)),
    ("chhinnamasta", "छिन्नमस्ता", "Chhinnamasta", dict(skin="#c8321f", items={"f": "khadga"}, saree=["#8a1a1a", "zigzag", "gold"])),
    ("dhumavati", "धूमावती", "Dhumavati", dict(skin="#8a8a8a", build="old", saree=["#5a5a5a", "stripes", "#3a3a3a"], items={"f": "kalash"},
                                             crown="veil", halo=False)),
    ("bagalamukhi", "बगलामुखी", "Bagalamukhi", dict(skin="#f0c040", saree=["#f2c23a", "floral", "maroon"], items={"f": "gada"})),
    ("matangi", "मातंगी", "Matangi", dict(skin="#3a8a5a", saree=["#2f6a3a", "floral", "gold"], items={"f": "veena"})),
    ("kamala", "कमला", "Kamala", dict(skin="#f0c070", arms=4, extra_items=["padma", "padma"], items={"f": "abhaya"},
                                       saree=["vermilion", "floral", "gold"])),
    ("annapurna", "अन्नपूर्णा", "Annapurna", dict(items={"f": "kalash", "b": "abhaya"}, saree=["#e8a03a", "floral", "maroon"])),
    ("ganga", "गंगा", "Ganga", dict(skin="#f0e8e0", saree=["#9ad0e6", "waves", "#f6efdf"], items={"f": "kalash", "b": "padma"})),
    ("yamuna", "यमुना", "Yamuna", dict(skin="#3a4a7a", saree=["#2a4a7a", "waves", "gold"], items={"f": "kalash"})),
    ("santoshi", "संतोषी माता", "Santoshi Mata", dict(arms=4, extra_items=["khadga", "trishul"], items={"f": "kalash"},
                                                     saree=["vermilion", "dots", "gold"])),
    ("vaishno_devi", "वैष्णो देवी", "Vaishno Devi", dict(arms=8, extra_items=["trishul", "chakra", "shankh", "gada", "khadga", "padma"],
                                                         items={"f": "abhaya"}, saree=["vermilion", "floral", "gold"])),
    ("chamunda", "चामुंडा", "Chamunda", dict(skin="#3a2a2a", build="old", mundamala=True, fangs=True, eye="round", arms=4,
                                          extra_items=["khadga", "trishul"], items={"f": "damru"}, saree=["#2a1a1a", "zigzag", "maroon"])),
    ("ambika", "अम्बिका", "Ambika", dict(arms=8, extra_items=["chakra", "shankh", "khadga", "bow", "gada", "padma"], items={"f": "trishul"})),
    ("bhavani", "भवानी", "Bhavani", dict(arms=8, extra_items=["chakra", "shankh", "khadga", "bow", "gada", "padma"], items={"f": "trishul"},
                                          saree=["#e8833a", "floral", "gold"])),
    ("kamakhya", "कामाख्या", "Kamakhya", dict(saree=["vermilion", "floral", "gold"], items={"f": "padma"})),
    ("meenakshi", "मीनाक्षी", "Meenakshi", dict(skin="#3a7a5a", saree=["#e8833a", "floral", "gold"], items={"f": "padma"})),
    ("kamakshi", "कामाक्षी", "Kamakshi", dict(arms=4, extra_items=["pasha", "ankusha"], items={"f": "bow", "b": "arrow"})),
    ("vishalakshi", "विशालाक्षी", "Vishalakshi", dict(saree=["#c8467a", "floral", "gold"], items={"f": "padma"})),
    ("gayatri", "गायत्री", "Gayatri", dict(heads=["human", "human", "human", "human"], arms=10,
                                           extra_items=["chakra", "shankh", "padma", "pothi", "kamandalu", "mala", "gada", "pasha"],
                                           items={"f": "abhaya"}, saree=["#f2c23a", "floral", "maroon"])),
    ("savitri_devi", "सावित्री देवी", "Savitri Devi", dict(saree=["#f6efdf", "floral", "gold"], items={"f": "pothi"})),
    ("shakambhari", "शाकम्भरी", "Shakambhari", dict(saree=["#3a7a3a", "floral", "gold"], items={"f": "padma"})),
    ("manasa", "मनसा देवी", "Manasa Devi", dict(crown="hoods", hoods=5, saree=["#2f6a4a", "scales", "gold"], items={"f": "kalash"})),
    ("shitala", "शीतला माता", "Shitala Mata", dict(saree=["vermilion", "dots", "gold"], items={"f": "kalash", "b": "chamara"})),
    ("sati", "सती", "Sati", dict(saree=["vermilion", "floral", "gold"], items={"f": "padma"}, halo=False)),
    ("radha", "राधा", "Radha", dict(skin="#f0d0a0", saree=["#e89ab0", "floral", "gold"], choli="#f2c23a", crown="tiara", halo=False,
                                     items={"f": "flower"})),
    ("rukmini", "रुक्मिणी", "Rukmini", dict(saree=["vermilion", "floral", "gold"], halo=False, items={"f": "padma"})),
    ("aditi", "अदिति", "Aditi", dict(saree=["#f2c23a", "floral", "maroon"], halo=True)),
    ("diti", "दिति", "Diti", dict(saree=["#3a2a4a", "dots", "gold"], halo=False)),
    ("prithvi", "पृथ्वी देवी", "Bhudevi", dict(skin="#7a9a5a", saree=["#3a7a3a", "floral", "gold"], items={"f": "kalash"})),
    ("shachi", "शची (इन्द्राणी)", "Shachi Indrani", dict(saree=["#3a4a8a", "floral", "gold"], items={"f": "padma"})),
    ("rati", "रति", "Rati", dict(saree=["#e89ab0", "floral", "gold"], halo=False, items={"f": "mirror"})),
    ("swaha", "स्वाहा", "Swaha", dict(saree=["#e8521e", "floral", "gold"], halo=False)),
    ("usha_devi", "उषा देवी", "Usha (Dawn)", dict(saree=["#f0a070", "floral", "gold"], halo=True)),
    ("ratri_devi", "रात्रि देवी", "Ratri (Night)", dict(skin="#3a3a6a", saree=["#1a2240", "dots", "#f2e2b0"])),
]
ASHTALAKSHMI = [("adi_lakshmi", "आदि लक्ष्मी", "Adi Lakshmi"), ("dhana_lakshmi", "धन लक्ष्मी", "Dhana Lakshmi"),
                ("dhanya_lakshmi", "धान्य लक्ष्मी", "Dhanya Lakshmi"), ("gaja_lakshmi", "गज लक्ष्मी", "Gaja Lakshmi"),
                ("santana_lakshmi", "संतान लक्ष्मी", "Santana Lakshmi"), ("veera_lakshmi", "वीर लक्ष्मी", "Veera Lakshmi"),
                ("vijaya_lakshmi", "विजय लक्ष्मी", "Vijaya Lakshmi"), ("vidya_lakshmi", "विद्या लक्ष्मी", "Vidya Lakshmi")]
for i, (a, b, c) in enumerate(ASHTALAKSHMI):
    DEVI.append((a, b, c, dict(skin="#e8b878", saree=SAREE_PALETTE[i % len(SAREE_PALETTE)], arms=4, extra_items=["padma", "padma"],
                               items={"f": ["kalash", "abhaya", "padma", "chakra", "kalash", "khadga", "abhaya", "pothi"][i]})))
add("devi", "devi", DEVI)
# ------------------------------------------------------------------ Devas, Adityas, Vasus, Navagraha
add("deva", "deva", [
    ("indra", "इन्द्र", "Indra", dict(skin="#f0d8a8", items={"f": "vajra"}, dhoti=["#2f4a8a", "dots", "gold"], armor=None)),
    ("agni", "अग्नि देव", "Agni Dev", dict(skin="#d8582a", crown="flames", heads=["human"], items={"f": "khadga", "b": "kamandalu"},
                                         dhoti=["#e8833a", "zigzag", "#ffcf4a"], beard="short", beard_color="#8a2a1a")),
    ("vayu", "वायु देव", "Vayu Dev", dict(skin="#9ab8c8", items={"f": "dhwaja"}, dhoti=["#cfe3ea", "waves", "#5a8a9a"])),
    ("varuna", "वरुण देव", "Varuna Dev", dict(skin="#5a8ab8", items={"f": "pasha"}, dhoti=["#2f6a8a", "waves", "cream"])),
    ("surya", "सूर्य देव", "Surya Dev", dict(skin="#f0a040", crown="sun", items={"f": "padma", "b": "padma"}, dhoti=["#e8833a", "dots", "gold"])),
    ("chandra", "चंद्र देव", "Chandra Dev", dict(skin="#f0f0e8", items={"f": "padma"}, dhoti=["#cfd6e6", "dots", "#5a6a8a"])),
    ("yama", "यमराज", "Yamaraj", dict(skin="#2a3a4a", crown="kirita", items={"f": "gada", "b": "pasha"}, eye="round", mustache="big",
                                      dhoti=["#1e1e2a", "zigzag", "vermilion"], halo=False)),
    ("chitragupta", "चित्रगुप्त", "Chitragupta", dict(skin="skin_tan", items={"f": "pothi"}, crown="kirita_low", halo=False)),
    ("kubera", "कुबेर", "Kubera", dict(build="heavy", skin="#e8c080", items={"f": "bag", "b": "gada"}, dhoti=["#f2c23a", "floral", "maroon"])),
    ("vishwakarma", "विश्वकर्मा", "Vishwakarma", dict(build="old", beard="long", mustache=None, arms=4, extra_items=["pothi", "kamandalu"],
                                                     items={"f": "parashu", "b": "hala"})),
    ("kamadeva", "कामदेव", "Kamadeva", dict(skin="#3a8a5a", items={"f": "bow", "b": "flower"}, mustache=None, dhoti=["#e89ab0", "floral", "gold"])),
    ("brihaspati", "बृहस्पति", "Brihaspati", dict(build="old", beard="long", mustache=None, skin="#f0c060", crown="kirita",
                                                 items={"f": "pothi", "b": "mala"}, dhoti=["#f2c23a", "dots", "cream"])),
    ("shukracharya", "शुक्राचार्य", "Shukracharya", dict(build="old", beard="long", mustache=None, crown="jata", skin="#f6efdf",
                                                         eye="round", items={"f": "danda", "b": "kamandalu"}, lower="valkal", halo=False)),
    ("narada", "नारद मुनि", "Narada Muni", dict(build="slim", crown="shikha", hair="bald", beard="short", beard_color="black",
                                                 items={"f": "veena", "b": "mala"}, dhoti=["#f6efdf", "stripes", "saffron"], halo=False, mustache=None)),
    ("ashwini_kumar_1", "अश्विनी कुमार (नासत्य)", "Ashwini Kumar 1", dict(skin="#f0d8a8", items={"f": "kalash"}, mustache=None)),
    ("ashwini_kumar_2", "अश्विनी कुमार (दस्र)", "Ashwini Kumar 2", dict(skin="#f0d8a8", items={"f": "pothi"}, mustache=None)),
    ("aruna", "अरुण", "Aruna", dict(skin="#e8583a", items={"f": "dhwaja"}, halo=False)),
    ("mangal", "मंगल", "Mangal (Mars)", dict(skin="#c8321f", items={"f": "gada", "b": "shakti"}, dhoti=["#8a1a1a", "dots", "gold"])),
    ("budh", "बुध", "Budh (Mercury)", dict(skin="#5a9a5a", items={"f": "khadga", "b": "dhal"}, dhoti=["#3a7a3a", "dots", "gold"])),
    ("shukra", "शुक्र", "Shukra (Venus)", dict(skin="#f6efdf", items={"f": "pothi", "b": "danda"}, beard="long", mustache=None)),
    ("shani", "शनि देव", "Shani Dev", dict(skin="#1e1e2a", items={"f": "bow", "b": "trishul"}, dhoti=["#1e1e2a", "dots", "#5a5a8a"], eye="round")),
    ("rahu", "राहु", "Rahu", dict(skin="#2a2a3a", crown="spiky", lower="serpent", fangs=True, eye="round", items={"f": "khadga"}, halo=False)),
    ("ketu", "केतु", "Ketu", dict(skin="#5a4a3a", crown="spiky", lower="serpent", items={"f": "gada"}, halo=False)),
    ("dhata", "धाता (आदित्य)", "Dhata (Aditya)", dict(skin="#f0b050", crown="sun", items={"f": "padma"})),
    ("aryaman", "अर्यमा", "Aryaman (Aditya)", dict(skin="#f0b050", crown="sun", items={"f": "padma"})),
    ("mitra", "मित्र", "Mitra (Aditya)", dict(skin="#f0b050", crown="sun", items={"f": "padma"})),
    ("vivasvan", "विवस्वान", "Vivasvan (Aditya)", dict(skin="#f0a040", crown="sun", items={"f": "padma"})),
    ("tvashta", "त्वष्टा", "Tvashta (Aditya)", dict(skin="#f0b050", crown="sun", items={"f": "parashu"})),
    ("pushan", "पूषा", "Pushan (Aditya)", dict(skin="#f0b050", crown="sun", items={"f": "danda"})),
    ("bhaga", "भग", "Bhaga (Aditya)", dict(skin="#f0b050", crown="sun", items={"f": "kalash"})),
    ("amshuman", "अंशुमान", "Amshuman (Aditya)", dict(skin="#f0b050", crown="sun", items={"f": "padma"})),
    ("parjanya", "पर्जन्य", "Parjanya (Aditya)", dict(skin="#7a9ab8", crown="sun", items={"f": "vajra"})),
    ("dhara_vasu", "धर (वसु)", "Dhara (Vasu)", dict(skin="#d8b080", items={"f": "kalash"})),
    ("dhruva_vasu", "ध्रुव (वसु)", "Dhruva (Vasu)", dict(skin="#d8b080", items={"f": "danda"})),
    ("soma_vasu", "सोम (वसु)", "Soma (Vasu)", dict(skin="#f0f0e8", items={"f": "kalash"})),
    ("apa_vasu", "आप (वसु)", "Apa (Vasu)", dict(skin="#7ab0c8", items={"f": "kalash"})),
    ("anila_vasu", "अनिल (वसु)", "Anila (Vasu)", dict(skin="#9ab8c8", items={"f": "dhwaja"})),
    ("anala_vasu", "अनल (वसु)", "Anala (Vasu)", dict(skin="#d8582a", crown="flames", items={"f": "khadga"})),
    ("pratyusha_vasu", "प्रत्यूष (वसु)", "Pratyusha (Vasu)", dict(skin="#f0a070", items={"f": "padma"})),
    ("prabhasa_vasu", "प्रभास (वसु)", "Prabhasa (Vasu)", dict(skin="#f0d070", items={"f": "padma"})),
    ("dharmaraj", "धर्मराज", "Dharmaraj", dict(skin="#2a3a4a", items={"f": "danda", "b": "pothi"}, halo=False)),
    ("kamadhenu_devi", "कामधेनु (देवी रूप)", "Kamadhenu (divine form)", dict(female=True, skin="#f6efdf", saree=["#f6efdf", "dots", "gold"])),
    ("sanat_kumara", "सनत्कुमार", "Sanat Kumara", dict(build="child", crown="shikha", hair="bald", lower="valkal", items={"f": "pothi"}, halo=True)),
    ("sanaka", "सनक", "Sanaka", dict(build="child", crown="shikha", hair="bald", lower="valkal", items={"f": "mala"}, halo=True)),
    ("sanandana", "सनन्दन", "Sanandana", dict(build="child", crown="shikha", hair="bald", lower="valkal", items={"f": "kamandalu"}, halo=True)),
    ("sanatana", "सनातन", "Sanatana", dict(build="child", crown="shikha", hair="bald", lower="valkal", items={"f": "danda"}, halo=True)),
    ("garuda", "गरुड़", "Garuda", dict(head="eagle", skin="#e8b05a", wings=True, wing_color="#c8642a", items={"f": "abhaya"},
                                       dhoti=["vermilion", "dots", "gold"], halo=False)),
    ("jaya", "जय (द्वारपाल)", "Jaya (Vaikuntha guard)", dict(skin="krishna", items={"f": "gada"}, halo=False, armor="#c8a050")),
    ("vijaya", "विजय (द्वारपाल)", "Vijaya (Vaikuntha guard)", dict(skin="krishna", items={"f": "gada"}, halo=False, armor="#c8a050")),
])
# ------------------------------------------------------------------ Ramayana
add("ramayana", "king", [
    ("lakshmana", "लक्ष्मण", "Lakshmana", dict(skin="#f0d0a0", crown="kirita", items={"f": "bow", "b": "arrow"}, dhoti=["vermilion", "dots", "cream"], mustache=None)),
    ("bharata", "भरत", "Bharata", dict(skin="rama", crown="kirita", items={"f": "abhaya"}, dhoti=["#f2c23a", "dots", "maroon"], mustache=None)),
    ("bharata_tapasvi", "भरत (तपस्वी)", "Bharata as ascetic", dict(skin="rama", crown="jata", lower="valkal", mustache=None, items={"f": "mala"})),
    ("shatrughna", "शत्रुघ्न", "Shatrughna", dict(skin="#f0d0a0", items={"f": "khadga"}, dhoti=["#2f6a8a", "dots", "cream"], mustache=None)),
    ("dasharatha", "राजा दशरथ", "King Dasharatha", dict(build="old", beard="long", beard_color="#e6e0d0", mustache=None, items={"f": "abhaya"})),
    ("janaka", "राजा जनक", "King Janaka", dict(build="old", beard="long", mustache=None, items={"f": "pothi"})),
    ("ram_vanvasi", "वनवासी राम", "Ram in exile", dict(skin="rama", crown="jata", lower="valkal", mustache=None, items={"f": "bow", "b": "arrow"},
                                                      necklace=False, sash=None)),
    ("lakshman_vanvasi", "वनवासी लक्ष्मण", "Lakshman in exile", dict(crown="jata", lower="valkal", mustache=None, items={"f": "bow", "b": "arrow"},
                                                                    necklace=False, sash=None)),
    ("vibhishana", "विभीषण", "Vibhishana", dict(skin="#5a6a7a", crown="kirita", items={"f": "gada"}, mustache="curl")),
    ("guha", "निषादराज गुह", "Nishadraj Guha", dict(skin="skin_dark", crown="turban", items={"f": "bow"}, sash="leaf")),
    ("kevat", "केवट", "Kevat (boatman)", dict(skin="skin_brown", crown="turban", items={"f": "danda"}, dhoti=["#f0e8d4", "stripes", "#3a5a7a"],
                                            necklace=False)),
    ("sumantra", "सुमंत्र", "Sumantra", dict(build="old", beard="short", crown="turban", items={"f": "pothi"})),
    ("lav", "लव", "Lav", dict(build="child", crown="jata", lower="valkal", items={"f": "bow"}, mustache=None)),
    ("kush", "कुश", "Kush", dict(build="child", crown="jata", lower="valkal", items={"f": "bow"}, mustache=None)),
])
add("ramayana", "queen", [
    ("sita", "सीता", "Sita", dict(skin="skin_light", saree=["vermilion", "floral", "gold"], choli="mustard", items={"f": "padma"})),
    ("sita_vanvasi", "वनवासी सीता", "Sita in exile", dict(saree=["#c8a060", "stripes", "#7a4a2a"], crown="veil", items={})),
    ("kaushalya", "कौशल्या", "Kaushalya", dict(build="old", saree=["#f6efdf", "floral", "gold"], crown="veil")),
    ("kaikeyi", "कैकेयी", "Kaikeyi", dict(saree=["#3a2a4a", "floral", "gold"], angry=True)),
    ("sumitra", "सुमित्रा", "Sumitra", dict(saree=["#2f6a3a", "floral", "gold"])),
    ("urmila", "उर्मिला", "Urmila", dict(saree=["#e8a03a", "floral", "maroon"])),
    ("mandavi", "माण्डवी", "Mandavi", dict(saree=["#3a4a8a", "floral", "gold"])),
    ("shrutakirti", "श्रुतकीर्ति", "Shrutakirti", dict(saree=["#c8467a", "dots", "gold"])),
    ("mandodari", "मंदोदरी", "Mandodari", dict(skin="#d8a878", saree=["#8a1a1a", "floral", "gold"])),
    ("sulochana", "सुलोचना", "Sulochana", dict(saree=["#2a4a4a", "floral", "gold"])),
    ("ahalya", "अहिल्या", "Ahalya", dict(saree=["#f6efdf", "stripes", "#8a6a4a"], crown="veil")),
    ("shabari", "शबरी", "Shabari", dict(build="old", skin="skin_dark", saree=["#8a6a3a", "stripes", "#5a3a1a"], crown="veil", items={"f": "bag"})),
    ("trijata", "त्रिजटा", "Trijata", dict(skin="#5a6a5a", saree=["#3a4a3a", "dots", "gold"])),
    ("manthara", "मंथरा", "Manthara", dict(build="old", skin="skin_tan", saree=["#5a4a3a", "stripes", "#3a2a1a"], crown="veil")),
    ("tara_vanara", "तारा (वानर रानी)", "Tara (Vali's queen)", dict(skin="#e0b080", saree=["#2f6a3a", "floral", "gold"])),
    ("ruma", "रुमा", "Ruma", dict(saree=["#e8a03a", "dots", "maroon"])),
])
add("ramayana_vanara", "vanara", [
    ("hanuman", "हनुमान", "Hanuman", dict(skin="monkey", crown="kirita", dhoti=["vermilion", "dots", "cream"], items={"f": "gada"})),
    ("hanuman_flying", "उड़ते हनुमान", "Hanuman (flying, mountain)", dict(skin="monkey", crown="kirita", items={"f": "gada"})),
    ("bal_hanuman", "बाल हनुमान", "Bal Hanuman", dict(skin="monkey", build="child", crown="kirita_low", items={"f": "gada"})),
    ("panchmukhi_hanuman", "पंचमुखी हनुमान", "Panchmukhi Hanuman", dict(skin="monkey", heads=["horse", "lion", "eagle", "boar"],
                                                                     arms=10, extra_items=["trishul", "khadga", "chakra", "parashu", "ankusha",
                                                                                           "pasha", "vajra", "kalash"], items={"f": "gada"})),
    ("sugriva", "सुग्रीव", "Sugriva", dict(skin="#c8843a", crown="kirita", dhoti=["#f2c23a", "dots", "maroon"])),
    ("vali", "बाली", "Vali", dict(skin="#d8a050", crown="kirita", dhoti=["#e8833a", "dots", "gold"], build="giant")),
    ("angada", "अंगद", "Angada", dict(skin="#d8a85a", dhoti=["#3a7a3a", "dots", "cream"])),
    ("nala_vanara", "नल", "Nala (engineer)", dict(skin="#b8743a", items={"f": "parashu"})),
    ("nila", "नील", "Nila", dict(skin="#7a7a9a", items={"f": "gada"})),
    ("dvivida", "द्विविद", "Dvivida", dict(skin="#a86a3a")),
    ("mainda", "मैन्द", "Mainda", dict(skin="#9a5a2a")),
    ("sushena", "सुषेण वैद्य", "Sushena", dict(skin="#c8a070", build="old", beard="long", items={"f": "bag"})),
    ("kesari", "केसरी", "Kesari", dict(skin="#d8a050", crown="kirita")),
    ("makardhwaja", "मकरध्वज", "Makardhwaja", dict(skin="monkey", lower="fish", tail_color="#3f8f8a", items={"f": "gada"})),
    ("gavaya", "गवय", "Gavaya", dict(skin="#b8843a")),
    ("gavaksha", "गवाक्ष", "Gavaksha", dict(skin="#a8743a")),
    ("sharabha", "शरभ (वानर)", "Sharabha", dict(skin="#c8944a")),
    ("gandhamadana", "गंधमादन (वानर)", "Gandhamadana", dict(skin="#b87a3a")),
])
add("ramayana_riksha", "riksha", [
    ("jambavan", "जाम्बवान", "Jambavan", dict(build="old", skin="#4a3a30", items={"f": "danda"}, dhoti=["vermilion", "dots", "cream"])),
    ("jambavati", "जाम्बवती", "Jambavati", dict(female=True, head="human", skin="#c8a070", saree=["#5a3a2a", "floral", "gold"], beard=None)),
])
add("ramayana_rakshasa", "rakshasa", [
    ("ravana", "रावण", "Ravana", dict(skin="#c4532c", crown="kirita", heads=["human"] * 9, fangs=False, items={"f": "khadga", "b": "dhal"},
                                     dhoti=["#3f9a4a", "dots", "cream"], sash="mustard", arms=10, eye="almond", mustache="big",
                                     extra_items=["trishul", "bow", "gada", "chakra", "parashu", "shakti", "arrow", "vajra"])),
    ("ravana_sanyasi", "साधु वेश रावण", "Ravana as sadhu", dict(skin="skin_tan", crown="jata", beard="long", lower="valkal", fangs=False,
                                                              eye="almond", angry=False, build="old", items={"f": "kamandalu"}, mustache=None)),
    ("kumbhakarna", "कुम्भकर्ण", "Kumbhakarna", dict(skin="#4a3a2a", scale=1.25, items={"f": "gada"}, crown="horns")),
    ("meghnad", "मेघनाद (इन्द्रजीत)", "Meghnad / Indrajit", dict(skin="#3a4a5a", build="hero", crown="kirita", items={"f": "bow", "b": "arrow"},
                                                                fangs=False, eye="almond", angry=False)),
    ("akshaya_kumara", "अक्षय कुमार", "Akshaya Kumara", dict(skin="#4a4a5a", build="hero", crown="kirita_low", items={"f": "khadga"}, fangs=False)),
    ("atikaya", "अतिकाय", "Atikaya", dict(skin="#5a3a3a", scale=1.2, items={"f": "parashu"})),
    ("prahasta", "प्रहस्त", "Prahasta", dict(skin="#3a4a3a", items={"f": "gada"})),
    ("maricha", "मारीच", "Maricha", dict(skin="#5a5a3a", items={"f": "khadga"})),
    ("subahu", "सुबाहु", "Subahu", dict(skin="#4a3a4a", items={"f": "trishul"})),
    ("khara", "खर", "Khara", dict(skin="#6a2a2a", items={"f": "gada"})),
    ("dushana", "दूषण", "Dushana", dict(skin="#2a4a4a", items={"f": "khadga"})),
    ("trishira", "त्रिशिरा", "Trishira", dict(skin="#4a4a2a", heads=["human", "human"], items={"f": "trishul"})),
    ("kabandha", "कबंध", "Kabandha", dict(skin="#3a3a2a", build="heavy", scale=1.3, items={})),
    ("viradha", "विराध", "Viradha", dict(skin="#4a3a2a", items={"f": "shakti"})),
    ("ahiravan", "अहिरावण", "Ahiravana", dict(skin="#2a2a3a", items={"f": "khadga"}, crown="horns")),
    ("mahiravan", "महिरावण", "Mahiravana", dict(skin="#3a2a3a", items={"f": "trishul"}, crown="horns")),
    ("kalanemi", "कालनेमि", "Kalanemi", dict(skin="skin_tan", crown="jata", beard="long", lower="valkal", fangs=False, eye="almond",
                                            build="old", items={"f": "mala"})),
    ("lankini", "लंकिनी", "Lankini", dict(female=True, build="female", skin="#4a3a3a", saree=["#3a2a2a", "zigzag", "maroon"], crown="spiky", items={"f": "gada"})),
    ("dhumraksha", "धूम्राक्ष", "Dhumraksha", dict(skin="#5a5a5a", items={"f": "gada"})),
    ("vajradamshtra", "वज्रदंष्ट्र", "Vajradamshtra", dict(skin="#3a3a4a", items={"f": "vajra"})),
    ("akampana", "अकम्पन", "Akampana", dict(skin="#4a3a2a", items={"f": "gada"})),
    ("devantaka", "देवान्तक", "Devantaka", dict(skin="#3a2a2a", items={"f": "parashu"})),
    ("narantaka", "नरान्तक", "Narantaka", dict(skin="#2a3a3a", items={"f": "shakti"})),
    ("mahodara", "महोदर", "Mahodara", dict(skin="#4a4a3a", build="heavy", items={"f": "gada"})),
    ("mahaparshva", "महापार्श्व", "Mahaparshva", dict(skin="#3a4a4a", items={"f": "parashu"})),
    ("lanka_rakshasa_guard", "लंका का राक्षस प्रहरी", "Lanka rakshasa guard", dict(skin="#4a4a3a", build="hero", items={"f": "spear"})),
])
add("ramayana_rakshasi", "rakshasi", [
    ("shurpanakha", "शूर्पणखा", "Shurpanakha", dict(skin="#5a3a3a", saree=["#3a1a2a", "zigzag", "maroon"], fangs=True)),
    ("tataka", "ताड़का", "Tataka", dict(skin="#3a2a2a", scale=1.3, saree=["#2a1a1a", "zigzag", "#5a1a1a"], items={"f": "gada"})),
    ("surasa", "सुरसा", "Surasa", dict(skin="#3a5a4a", lower="serpent", crown="hoods", hoods=1, fangs=True)),
    ("simhika", "सिंहिका", "Simhika", dict(skin="#2a3a4a", fangs=True, saree=["#1e2a3a", "waves", "#5a8a9a"])),
    ("ayomukhi", "अयोमुखी", "Ayomukhi", dict(skin="#4a3a2a")),
])
# ------------------------------------------------------------------ Mahabharata
MB_MEN = [
    ("arjuna", "अर्जुन", "Arjuna", dict(skin="skin_tan", items={"f": "bow", "b": "arrow"}, dhoti=["#f0e8d4", "dots", "vermilion"], sash="vermilion")),
    ("bhima", "भीम", "Bhima", dict(skin="#7e4a2c", build="heavy", items={"f": "gada"}, dhoti=["mustard", "dots", "vermilion"], mustache="big",
                                    straps=True)),
    ("yudhishthira", "युधिष्ठिर", "Yudhishthira", dict(skin="skin_tan", items={"f": "abhaya"}, dhoti=["#f6efdf", "stripes", "gold"], beard="short")),
    ("nakula", "नकुल", "Nakula", dict(skin="skin_light", items={"f": "khadga"}, dhoti=["#3a7a7a", "dots", "cream"], mustache=None)),
    ("sahadeva", "सहदेव", "Sahadeva", dict(skin="skin_light", items={"f": "pothi"}, dhoti=["#7a5a8a", "dots", "cream"], mustache=None)),
    ("karna", "कर्ण", "Karna", dict(skin="#e0b060", armor="#f2c23a", items={"f": "bow", "b": "arrow"}, crown="sun", halo=False)),
    ("duryodhana", "दुर्योधन", "Duryodhana", dict(skin="skin_tan", items={"f": "gada"}, dhoti=["#3a2a4a", "dots", "gold"], angry=True, mustache="big",
                                                  straps=True)),
    ("dushasana", "दुःशासन", "Dushasana", dict(skin="skin_brown", items={"f": "khadga"}, dhoti=["#5a2a2a", "dots", "gold"], angry=True)),
    ("shakuni", "शकुनि", "Shakuni", dict(build="old", skin="skin_tan", beard="short", beard_color="#3a3a3a", items={"f": "pothi"}, crown="turban",
                                        turban_color="#3a2a4a", eye="round")),
    ("bhishma", "भीष्म पितामह", "Bhishma", dict(build="old", beard="long", mustache=None, armor="#c8c4b8", items={"f": "bow"}, crown="kirita")),
    ("bhishma_sharshaiyya", "शरशय्या पर भीष्म", "Bhishma on arrow-bed", dict(build="old", beard="long", mustache=None, items={})),
    ("drona", "द्रोणाचार्य", "Dronacharya", dict(build="old", beard="long", mustache=None, crown="jata", armor="#b8a070", items={"f": "bow", "b": "arrow"})),
    ("kripa", "कृपाचार्य", "Kripacharya", dict(build="old", beard="long", mustache=None, crown="jata", items={"f": "bow"})),
    ("ashwatthama", "अश्वत्थामा", "Ashwatthama", dict(skin="skin_tan", crown="jata", third_eye=True, items={"f": "bow", "b": "khadga"}, angry=True)),
    ("dhritarashtra", "धृतराष्ट्र", "Dhritarashtra", dict(build="old", beard="long", mustache=None, items={}, eye="round", iris="#c8c4b8")),
    ("vidura", "विदुर", "Vidura", dict(build="old", beard="short", crown="turban", turban_color="#f6efdf", items={"f": "pothi"})),
    ("sanjaya", "संजय", "Sanjaya", dict(crown="turban", items={"f": "abhaya"})),
    ("pandu", "पाण्डु", "Pandu", dict(skin="#f0e0d0", items={"f": "bow"})),
    ("shantanu", "शांतनु", "Shantanu", dict(build="old", beard="short", items={"f": "abhaya"})),
    ("abhimanyu", "अभिमन्यु", "Abhimanyu", dict(build="slim", mustache=None, items={"f": "khadga", "b": "dhal"}, armor="#c8a050")),
    ("ghatotkacha", "घटोत्कच", "Ghatotkacha", dict(skin="#3a3a2a", build="giant", scale=1.35, crown="horns", fangs=True, eye="round",
                                                 items={"f": "gada"})),
    ("barbarik", "बर्बरीक", "Barbarik", dict(skin="#3a3a3a", items={"f": "bow", "b": "arrow"}, crown="kirita")),
    ("parikshit", "परीक्षित", "Parikshit", dict(mustache=None, items={"f": "abhaya"})),
    ("shikhandi", "शिखंडी", "Shikhandi", dict(skin="skin_tan", items={"f": "bow"}, mustache=None)),
    ("drupada", "द्रुपद", "Drupada", dict(build="old", beard="short", items={"f": "khadga"})),
    ("dhrishtadyumna", "धृष्टद्युम्न", "Dhrishtadyumna", dict(items={"f": "khadga", "b": "dhal"}, armor="#b8a070")),
    ("jayadratha", "जयद्रथ", "Jayadratha", dict(items={"f": "khadga"}, angry=True)),
    ("shalya", "शल्य", "Shalya", dict(build="old", beard="short", items={"f": "spear"})),
    ("virata", "राजा विराट", "King Virata", dict(build="heavy", items={"f": "abhaya"})),
    ("kichaka", "कीचक", "Kichaka", dict(build="heavy", angry=True, items={"f": "gada"})),
    ("ekalavya", "एकलव्य", "Ekalavya", dict(skin="skin_dark", crown="turban", turban_color="#5a7a3a", items={"f": "bow", "b": "arrow"},
                                            lower="loin", necklace=False, sash=None, mustache=None)),
    ("bhurishravas", "भूरिश्रवा", "Bhurishravas", dict(items={"f": "khadga"}, armor="#a89a7a")),
    ("satyaki", "सात्यकि", "Satyaki", dict(items={"f": "bow"}, armor="#a89a7a")),
    ("kritavarma", "कृतवर्मा", "Kritavarma", dict(items={"f": "gada"}, armor="#a89a7a")),
    ("uttara_kumar", "उत्तर कुमार", "Prince Uttar", dict(build="slim", mustache=None, items={"f": "bow"})),
    ("iravan", "इरावान", "Iravan", dict(mustache=None, items={"f": "khadga"})),
    ("babruvahana", "बभ्रुवाहन", "Babruvahana", dict(mustache=None, items={"f": "bow"})),
    ("vikarna", "विकर्ण", "Vikarna", dict(items={"f": "khadga"})),
    ("yuyutsu", "युयुत्सु", "Yuyutsu", dict(items={"f": "spear"})),
    ("sudakshina", "सुदक्षिण", "Sudakshina", dict(items={"f": "spear"})),
    ("bhagadatta", "भगदत्त", "Bhagadatta", dict(build="old", beard="short", items={"f": "ankusha"})),
    ("vyasa", "वेद व्यास", "Ved Vyasa", dict(build="old", beard="long", mustache=None, crown="jata", lower="valkal", skin="#5a4a3a",
                                           items={"f": "pothi"}, sash=None)),
    ("dhaumya", "धौम्य", "Dhaumya (priest)", dict(build="old", crown="shikha", hair="bald", janeu=True, items={"f": "kamandalu"})),
    ("kansa", "कंस", "Kansa", dict(skin="skin_tan", build="heavy", angry=True, mustache="big", items={"f": "khadga"}, dhoti=["#3a2a2a", "dots", "gold"])),
    ("vasudeva", "वसुदेव", "Vasudeva", dict(build="old", beard="short", items={})),
    ("nanda", "नंद बाबा", "Nanda Baba", dict(build="heavy", crown="turban", turban_color="#f2c23a", beard="short", items={"f": "danda"})),
    ("sudama", "सुदामा", "Sudama", dict(build="slim", crown="shikha", hair="bald", janeu=True, dhoti=["#f0e8d4", "stripes", "#8a6a4a"],
                                         items={"f": "bag"}, necklace=False, sash=None)),
    ("uddhava", "उद्धव", "Uddhava", dict(items={"f": "pothi"}, mustache=None)),
    ("akrura", "अक्रूर", "Akrura", dict(build="old", beard="short", items={"f": "abhaya"})),
    ("pradyumna", "प्रद्युम्न", "Pradyumna", dict(skin="krishna", mustache=None, items={"f": "bow"})),
    ("aniruddha", "अनिरुद्ध", "Aniruddha", dict(skin="krishna", mustache=None, items={"f": "khadga"})),
    ("samba", "साम्ब", "Samba", dict(mustache=None, items={"f": "gada"})),
    ("shishupala", "शिशुपाल", "Shishupala", dict(angry=True, items={"f": "khadga"}, dhoti=["#3a2a4a", "dots", "gold"])),
    ("jarasandha", "जरासंध", "Jarasandha", dict(build="heavy", angry=True, mustache="big", items={"f": "gada"})),
    ("kalayavana", "कालयवन", "Kalayavana", dict(skin="#2a2a2a", items={"f": "khadga"}, crown="helmet")),
    ("rukmi", "रुक्मी", "Rukmi", dict(items={"f": "bow"})),
    ("paundraka", "पौण्ड्रक", "Paundraka (false Vasudeva)", dict(skin="krishna", arms=4, extra_items=["chakra", "shankh"], items={"f": "gada"})),
    ("shalva", "शाल्व", "Shalva", dict(items={"f": "khadga"}, angry=True)),
    ("dushyanta", "राजा दुष्यंत", "King Dushyanta", dict(items={"f": "bow"})),
    ("bharata_chakravarti", "चक्रवर्ती भरत", "Emperor Bharata", dict(items={"f": "chakra"})),
]
add("mahabharata", "king", MB_MEN)
add("mahabharata", "queen", [
    ("draupadi", "द्रौपदी", "Draupadi", dict(skin="#8a5a3a", saree=["vermilion", "floral", "gold"], hair="long")),
    ("kunti", "कुंती", "Kunti", dict(build="old", saree=["#f6efdf", "floral", "gold"], crown="veil")),
    ("gandhari", "गांधारी", "Gandhari", dict(saree=["#3a2a4a", "floral", "gold"], crown="veil", eye="round", iris="#f6efdf")),
    ("madri", "माद्री", "Madri", dict(saree=["#2f6a3a", "floral", "gold"])),
    ("satyavati", "सत्यवती", "Satyavati", dict(skin="skin_brown", saree=["#2a4a7a", "waves", "gold"])),
    ("ganga_mb", "गंगा (महाभारत)", "Ganga (Bhishma's mother)", dict(skin="#f0e8e0", saree=["#9ad0e6", "waves", "#f6efdf"])),
    ("amba", "अम्बा", "Amba", dict(saree=["#8a1a1a", "dots", "gold"], angry=True)),
    ("ambika_mb", "अम्बिका (रानी)", "Ambika (queen)", dict(saree=["#3a4a8a", "floral", "gold"])),
    ("ambalika", "अम्बालिका", "Ambalika", dict(skin="#f0e8e0", saree=["#e8a03a", "floral", "gold"])),
    ("subhadra", "सुभद्रा", "Subhadra", dict(saree=["#e89ab0", "floral", "gold"])),
    ("uttara", "उत्तरा", "Uttara", dict(saree=["#f2c23a", "floral", "maroon"])),
    ("hidimba", "हिडिम्बा", "Hidimba", dict(skin="#5a4a3a", saree=["#3a4a2a", "zigzag", "gold"], crown="spiky")),
    ("uloopi", "उलूपी", "Uloopi", dict(lower="serpent", crown="hoods", hoods=3, saree=["#2f6a4a", "scales", "gold"])),
    ("chitrangada", "चित्रांगदा", "Chitrangada", dict(saree=["#c8321f", "floral", "gold"], items={"f": "bow"})),
    ("devaki", "देवकी", "Devaki", dict(saree=["#f6efdf", "floral", "gold"], crown="veil")),
    ("yashoda", "यशोदा", "Yashoda", dict(saree=["#e8a03a", "floral", "maroon"], crown="veil", items={"f": "kalash"})),
    ("rohini", "रोहिणी", "Rohini", dict(saree=["#2f6a3a", "floral", "gold"], crown="veil")),
    ("satyabhama", "सत्यभामा", "Satyabhama", dict(saree=["#3a4a8a", "floral", "gold"])),
    ("kalindi", "कालिंदी", "Kalindi", dict(skin="#3a4a7a", saree=["#2a4a7a", "waves", "gold"])),
    ("mitravinda", "मित्रविंदा", "Mitravinda", dict(saree=["#c8467a", "floral", "gold"])),
    ("nagnajiti", "नाग्नजिती", "Nagnajiti", dict(saree=["#e8833a", "floral", "gold"])),
    ("bhadra", "भद्रा", "Bhadra", dict(saree=["#7a2a6a", "floral", "gold"])),
    ("lakshmana_rani", "लक्ष्मणा (रानी)", "Lakshmana (queen)", dict(saree=["teal", "floral", "gold"])),
    ("usha_banasura", "उषा (बाणासुर पुत्री)", "Usha", dict(saree=["#f0a070", "floral", "gold"])),
    ("chitralekha", "चित्रलेखा", "Chitralekha", dict(saree=["#9a6ac8", "dots", "gold"], items={"f": "pothi"})),
    ("shakuntala", "शकुंतला", "Shakuntala", dict(saree=["#7a9a5a", "floral", "gold"], items={"f": "flower"})),
    ("putana", "पूतना", "Putana", dict(skin="#e8c8a8", saree=["#c8467a", "floral", "gold"])),
    ("sudeshna", "सुदेष्णा", "Sudeshna", dict(saree=["#8a1a1a", "floral", "gold"])),
    ("vrushali", "वृषाली", "Vrushali (Karna's wife)", dict(saree=["#e8a03a", "dots", "maroon"])),
    ("bhanumati", "भानुमती", "Bhanumati", dict(saree=["#3a2a4a", "floral", "gold"])),
    ("lalita_gopi", "ललिता सखी", "Lalita (gopi)", dict(saree=["#f2c23a", "floral", "maroon"], crown="veil")),
    ("vishakha_gopi", "विशाखा सखी", "Vishakha (gopi)", dict(saree=["#2f6a3a", "dots", "gold"], crown="veil")),
    ("chandravali", "चन्द्रावली", "Chandravali (gopi)", dict(saree=["#f6efdf", "floral", "vermilion"], crown="veil")),
])
add("mahabharata_asura", "asura", [
    ("hidimb", "हिडिम्ब", "Hidimb", dict(skin="#3a3a2a", build="giant")),
    ("bakasura", "बकासुर", "Bakasura", dict(skin="#4a3a3a", build="giant", items={"f": "gada"})),
    ("kirmira", "किर्मीर", "Kirmira", dict(skin="#2a3a3a")),
    ("jatasura", "जटासुर", "Jatasura", dict(skin="#3a3a4a", crown="jata")),
    ("narakasura", "नरकासुर", "Narakasura", dict(skin="#2a2a3a", items={"f": "trishul"})),
    ("banasura", "बाणासुर", "Banasura", dict(skin="#3a2a4a", arms=10, extra_items=["bow", "khadga", "trishul", "gada", "shakti",
                                                                                  "dhal", "parashu", "pasha"], items={"f": "bow"})),
    ("mura", "मुर दैत्य", "Mura", dict(skin="#2a3a2a", heads=["human"] * 4)),
    ("aghasura", "अघासुर", "Aghasura", dict(lower="serpent", skin="#2a4a2a", crown="hoods", hoods=1)),
    ("trinavarta", "तृणावर्त", "Trinavarta", dict(skin="#6a6a5a", wings=True, wing_color="#8a8a7a")),
    ("dhenukasura", "धेनुकासुर", "Dhenukasura", dict(head="buffalo", skin="#4a3a2a")),
    ("arishtasura", "अरिष्टासुर", "Arishtasura", dict(head="buffalo", skin="#2a2a2a")),
    ("keshi", "केशी", "Keshi", dict(head="horse", skin="#3a3a3a")),
    ("pralambasura", "प्रलम्बासुर", "Pralambasura", dict(skin="#3a4a3a")),
    ("vatsasura", "वत्सासुर", "Vatsasura", dict(head="buffalo", skin="#8a6a4a")),
    ("shakatasura", "शकटासुर", "Shakatasura", dict(skin="#5a4a3a")),
    ("vyomasura", "व्योमासुर", "Vyomasura", dict(skin="#4a4a6a")),
])
# ------------------------------------------------------------------ Asuras & daityas
add("asura", "asura", [
    ("hiranyakashipu", "हिरण्यकशिपु", "Hiranyakashipu", dict(skin="#c8a040", crown="kirita", items={"f": "gada"}, dhoti=["#8a1a1a", "floral", "gold"])),
    ("hiranyaksha", "हिरण्याक्ष", "Hiranyaksha", dict(skin="#a88a3a", crown="spiky", items={"f": "gada"})),
    ("mahishasura", "महिषासुर", "Mahishasura", dict(head="buffalo", skin="#2a2a2a", items={"f": "khadga", "b": "dhal"}, scale=1.15)),
    ("shumbha", "शुम्भ", "Shumbha", dict(skin="#3a2a4a", items={"f": "khadga"})),
    ("nishumbha", "निशुम्भ", "Nishumbha", dict(skin="#2a3a4a", items={"f": "gada"})),
    ("raktabija", "रक्तबीज", "Raktabija", dict(skin="#8a1a1a", items={"f": "khadga"})),
    ("chanda", "चण्ड", "Chanda", dict(skin="#4a2a2a", items={"f": "parashu"})),
    ("munda", "मुण्ड", "Munda", dict(skin="#2a2a4a", items={"f": "trishul"})),
    ("dhumralochana", "धूम्रलोचन", "Dhumralochana", dict(skin="#5a5a5a", items={"f": "gada"})),
    ("madhu", "मधु", "Madhu", dict(skin="#3a3a2a", build="giant")),
    ("kaitabha", "कैटभ", "Kaitabha", dict(skin="#2a3a2a", build="giant")),
    ("vritra", "वृत्रासुर", "Vritrasura", dict(lower="serpent", skin="#2a3a3a", crown="horns", scale=1.3)),
    ("tarakasura", "तारकासुर", "Tarakasura", dict(skin="#3a2a3a", items={"f": "khadga"})),
    ("tripurasura", "त्रिपुरासुर", "Tripurasura", dict(skin="#4a3a2a", heads=["human", "human"])),
    ("andhaka", "अंधकासुर", "Andhakasura", dict(skin="#1e1e1e", eye="round", iris="#f6efdf")),
    ("jalandhara", "जलंधर", "Jalandhara", dict(skin="#2a4a6a", items={"f": "trishul"}, crown="kirita")),
    ("bhasmasura", "भस्मासुर", "Bhasmasura", dict(skin="#6a6a6a", crown="jata", items={})),
    ("raja_bali", "राजा बलि", "King Bali (Mahabali)", dict(skin="skin_tan", crown="kirita", fangs=False, eye="almond", angry=False,
                                                           items={"f": "kalash"}, dhoti=["#f2c23a", "floral", "maroon"])),
    ("prahlada", "भक्त प्रह्लाद", "Bhakt Prahlad", dict(build="child", skin="skin_light", crown="kirita_low", fangs=False, eye="almond",
                                                      angry=False, mustache=None, items={"f": "mala"}, dhoti=["#f2c23a", "dots", "vermilion"])),
    ("holika", "होलिका", "Holika", dict(female=True, build="female", fangs=False, saree=["#c8321f", "zigzag", "gold"], crown="veil")),
    ("virochana", "विरोचन", "Virochana", dict(skin="#8a6a3a", fangs=False)),
    ("shankhachuda", "शंखचूड़", "Shankhachuda", dict(skin="#2a4a4a", items={"f": "shankh"})),
    ("durgamasura", "दुर्गमासुर", "Durgamasura", dict(skin="#3a3a3a", build="giant")),
    ("vatapi", "वातापि", "Vatapi", dict(skin="#4a3a2a")),
    ("ilvala", "इल्वल", "Ilvala", dict(skin="#3a4a2a")),
    ("namuchi", "नमुचि", "Namuchi", dict(skin="#2a2a3a")),
    ("sunda", "सुन्द", "Sunda", dict(skin="#4a2a2a")),
    ("upasunda", "उपसुन्द", "Upasunda", dict(skin="#2a2a4a")),
    ("mayasura", "मयासुर (शिल्पी)", "Mayasura (architect)", dict(skin="#5a4a3a", fangs=False, items={"f": "parashu"}, build="old", beard="short")),
    ("kalakeya", "कालकेय", "Kalakeya", dict(skin="#1e1e2a", items={"f": "khadga"})),
    ("nivatakavacha", "निवातकवच", "Nivatakavacha", dict(skin="#2a2a2a", armor="#5a5a5a", items={"f": "khadga"})),
    ("rahu_asura", "स्वर्भानु", "Svarbhanu", dict(skin="#2a2a3a", items={"f": "khadga"})),
    ("andhaka_gana", "दैत्य सेनापति", "Daitya commander", dict(skin="#3a3a2a", items={"f": "spear"}, armor="#5a4a3a")),
    ("daitya_soldier", "दैत्य सैनिक", "Daitya soldier", dict(skin="#4a3a3a", build="hero", items={"f": "spear", "b": "dhal"})),
    ("danava", "दानव", "Danava", dict(skin="#3a4a4a")),
])
# ------------------------------------------------------------------ Rishis, munis, sages
RISHIS = [("kashyapa", "कश्यप", "Kashyapa"), ("atri", "अत्रि", "Atri"), ("vasishtha", "वशिष्ठ", "Vasishtha"),
          ("vishwamitra", "विश्वामित्र", "Vishwamitra"), ("gautama", "गौतम", "Gautama"), ("jamadagni", "जमदग्नि", "Jamadagni"),
          ("bharadwaja", "भारद्वाज", "Bharadwaja"), ("agastya", "अगस्त्य", "Agastya"), ("durvasa", "दुर्वासा", "Durvasa"),
          ("markandeya", "मार्कण्डेय", "Markandeya"), ("bhrigu", "भृगु", "Bhrigu"), ("dadhichi", "दधीचि", "Dadhichi"),
          ("kanva", "कण्व", "Kanva"), ("yajnavalkya", "याज्ञवल्क्य", "Yajnavalkya"), ("shandilya", "शाण्डिल्य", "Shandilya"),
          ("parashara", "पराशर", "Parashara"), ("shukadeva", "शुकदेव", "Shukadeva"), ("valmiki", "वाल्मीकि", "Valmiki"),
          ("sandipani", "सांदीपनि", "Sandipani"), ("kapila", "कपिल मुनि", "Kapila Muni"), ("ashtavakra", "अष्टावक्र", "Ashtavakra"),
          ("lomasha", "लोमश", "Lomasha"), ("rishyashringa", "ऋष्यशृंग", "Rishyashringa"), ("uddalaka", "उद्दालक", "Uddalaka"),
          ("angiras", "अंगिरा", "Angiras"), ("pulastya", "पुलस्त्य", "Pulastya"), ("pulaha", "पुलह", "Pulaha"), ("kratu", "क्रतु", "Kratu"),
          ("marichi", "मरीचि", "Marichi"), ("daksha", "दक्ष प्रजापति", "Daksha Prajapati"), ("sharabhanga", "शरभंग", "Sharabhanga"),
          ("sutikshna", "सुतीक्ष्ण", "Sutikshna"), ("matanga", "मतंग", "Matanga"), ("vibhandaka", "विभाण्डक", "Vibhandaka"),
          ("chyavana", "च्यवन", "Chyavana"), ("richika", "ऋचीक", "Richika"), ("aurva", "और्व", "Aurva"), ("gargа", "गर्ग", "Garga"),
          ("devala", "देवल", "Devala"), ("asita", "असित", "Asita"), ("sukadeva_young", "शुक (बाल रूप)", "Shuka (young)"),
          ("jaimini", "जैमिनि", "Jaimini"), ("vaishampayana", "वैशम्पायन", "Vaishampayana"), ("sumantu", "सुमंतु", "Sumantu"),
          ("paila", "पैल", "Paila"), ("patanjali", "पतंजलि", "Patanjali"), ("panini", "पाणिनि", "Panini"), ("kaushika", "कौशिक", "Kaushika"),
          ("mandavya", "माण्डव्य", "Mandavya"), ("uttanka", "उत्तंक", "Uttanka"), ("dhaumya_muni", "आयोद धौम्य", "Ayoda Dhaumya"),
          ("vamadeva", "वामदेव", "Vamadeva"), ("jabali", "जाबालि", "Jabali"), ("suta", "सूत जी", "Suta"), ("shaunaka", "शौनक", "Shaunaka"),
          ("gargi", "गार्गी", "Gargi", {"female": True, "beard": None, "saree": ["#f0e0c0", "stripes", "saffron"], "crown": "bun"}),
          ("maitreyi", "मैत्रेयी", "Maitreyi", {"female": True, "beard": None, "saree": ["#f0e8d4", "stripes", "#8a6a4a"], "crown": "bun"}),
          ("anasuya", "अनसूया", "Anasuya", {"female": True, "beard": None, "saree": ["#c8a060", "stripes", "#7a4a2a"], "crown": "veil"}),
          ("lopamudra", "लोपामुद्रा", "Lopamudra", {"female": True, "beard": None, "saree": ["#c8a060", "dots", "#7a4a2a"], "crown": "bun"}),
          ("arundhati", "अरुंधती", "Arundhati", {"female": True, "beard": None, "saree": ["#f0e8d4", "stripes", "saffron"], "crown": "veil"}),
          ("renuka", "रेणुका", "Renuka", {"female": True, "beard": None, "saree": ["#e8a03a", "dots", "maroon"], "crown": "veil"})]
rows = []
for r in RISHIS:
    ov = dict(r[3]) if len(r) > 3 else {}
    key = r[0]
    if not ov.get("female"):
        ov.setdefault("skin", pick(["skin_light", "skin_tan", "#e8c8a0", "skin_brown"], key))
        ov.setdefault("items", pick([{"f": "danda", "b": "kamandalu"}, {"f": "mala", "b": "kamandalu"}, {"f": "pothi"},
                                     {"f": "danda"}, {"f": "kamandalu"}], key, "i"))
    if key in ("durvasa", "vishwamitra", "bhrigu"):
        ov["angry"] = True
    if key in ("ashtavakra",):
        ov["scale"] = 0.85
    if key in ("markandeya", "shukadeva", "sukadeva_young"):
        ov.update({"build": "slim", "beard": None})
    if key == "valmiki":
        ov.update({"skin": "skin_brown", "items": {"f": "pothi"}})
    rows.append((r[0], r[1], r[2], ov))
add("rishi", "rishi", rows)
add("muni", "muni", [
    ("dhruva", "भक्त ध्रुव", "Bhakt Dhruva", dict(build="child", beard=None, items={"f": "mala"})),
    ("nachiketa", "नचिकेता", "Nachiketa", dict(build="child", beard=None, crown="shikha", hair="bald", items={})),
    ("eklavya_muni", "शिष्य", "Student (shishya)", dict(build="child", beard=None, crown="shikha", hair="bald", items={"f": "pothi"})),
    ("brahmachari", "ब्रह्मचारी", "Brahmachari", dict(beard=None, crown="shikha", hair="bald", items={"f": "danda"})),
    ("sanyasi", "संन्यासी", "Sanyasi", dict(skin="skin_tan", items={"f": "danda", "b": "kamandalu"}, lower="valkal")),
    ("aghori", "अघोरी", "Aghori", dict(skin="#9a9a9a", items={"f": "trishul"}, mundamala=True, lower="loin")),
    ("tapasvi", "तपस्वी", "Tapasvi", dict(skin="skin_brown", items={"f": "mala"})),
    ("yogi", "योगी", "Yogi", dict(skin="skin_tan", items={})),
    ("bairagi", "बैरागी", "Bairagi", dict(skin="skin_tan", items={"f": "danda"})),
    ("kakbhushundi_rishi", "काकभुशुण्डि (ऋषि रूप)", "Kakbhushundi (sage form)", dict(skin="#3a3a3a", items={"f": "mala"})),
])
# ------------------------------------------------------------------ celestial beings
add("apsara", "apsara", [(i, h, e, dict(saree=SAREE_PALETTE[n % len(SAREE_PALETTE)], choli=pick(["#f0c0c8", "#f2c23a", "#9ad0e6", "mint"], i)))
                         for n, (i, h, e) in enumerate([("urvashi", "उर्वशी", "Urvashi"), ("menaka", "मेनका", "Menaka"),
                                                        ("rambha", "रम्भा", "Rambha"), ("tilottama", "तिलोत्तमा", "Tilottama"),
                                                        ("ghritachi", "घृताची", "Ghritachi"), ("alambusha", "अलम्बुषा", "Alambusha"),
                                                        ("pramlocha", "प्रम्लोचा", "Pramlocha"), ("manjughosha", "मंजुघोषा", "Manjughosha"),
                                                        ("misrakeshi", "मिश्रकेशी", "Misrakeshi"), ("purvachitti", "पूर्वचित्ति", "Purvachitti")])])
add("gandharva", "gandharva", [(i, h, e, dict(dhoti=DHOTI_PALETTE[n % len(DHOTI_PALETTE)]))
                               for n, (i, h, e) in enumerate([("chitraratha", "चित्ररथ", "Chitraratha"), ("tumburu", "तुम्बुरु", "Tumburu"),
                                                              ("vishwavasu", "विश्वावसु", "Vishwavasu"), ("chitrasena", "चित्रसेन", "Chitrasena"),
                                                              ("hahahuhu", "हाहा-हूहू", "Haha-Huhu"), ("kinnara", "किन्नर", "Kinnara"),
                                                              ("kimpurusha", "किम्पुरुष", "Kimpurusha"), ("vidyadhara", "विद्याधर", "Vidyadhara")])])
add("yaksha", "yaksha", [("yaksha", "यक्ष", "Yaksha"), ("yakshini", "यक्षिणी", "Yakshini", dict(female=True, build="female", crown="tiara",
                                                                                        saree=["#f2c23a", "floral", "maroon"])),
                          ("manibhadra", "मणिभद्र", "Manibhadra"), ("yaksha_prashna", "सरोवर का यक्ष", "Yaksha of the lake (Yaksha Prashna)",
                                                                   dict(crown="kirita", halo=True))])
# ------------------------------------------------------------------ Nagas
add("naga", "naga", [
    ("sheshnaag", "शेषनाग (अनंत)", "Sheshnaag (Ananta)", dict(hoods=7, skin="#7aa88a", items={"f": "abhaya"})),
    ("vasuki", "वासुकि", "Vasuki", dict(hoods=5, skin="#6a9a7a")),
    ("takshaka", "तक्षक", "Takshaka", dict(hoods=3, skin="#5a7a5a", angry=True, fangs=True)),
    ("kaliya", "कालिया नाग", "Kaliya", dict(hoods=5, skin="#2a3a3a", tail_color="#1e2a2a", angry=True, fangs=True)),
    ("karkotaka", "कर्कोटक", "Karkotaka", dict(hoods=3, skin="#4a5a3a")),
    ("padma_naga", "पद्मनाग", "Padma", dict(hoods=3, skin="#8a7a5a")),
    ("mahapadma", "महापद्म", "Mahapadma", dict(hoods=5, skin="#7a6a4a")),
    ("shankha_naga", "शंखनाग", "Shankha", dict(hoods=3, skin="#e8e0d0", tail_color="#c8c0b0")),
    ("kulika", "कुलिक", "Kulika", dict(hoods=3, skin="#6a3a3a")),
    ("aryaka", "आर्यक", "Aryaka", dict(hoods=3, skin="#5a6a7a", build="old", beard="short")),
    ("airavata_naga", "ऐरावत नाग", "Airavata (naga)", dict(hoods=3, skin="#6a7a8a")),
    ("naga_king", "नागराज", "Nagaraja", dict(hoods=7, skin="#5a8a6a")),
])
add("naga", "nagin", [("nagini", "नागिन", "Nagini"), ("naga_kanya", "नागकन्या", "Naga Kanya", dict(saree=["#2f6a4a", "scales", "gold"])),
                      ("sulasa", "सुलसा", "Sulasa")])
# ------------------------------------------------------------------ Kings & legends
add("legend", "king", [
    ("harishchandra", "राजा हरिश्चंद्र", "Raja Harishchandra", dict(items={"f": "abhaya"})),
    ("harishchandra_chandal", "हरिश्चंद्र (श्मशान प्रहरी)", "Harishchandra at the cremation ground", dict(crown="turban", items={"f": "danda"}, lower="loin")),
    ("rohitashva", "रोहिताश्व", "Rohitashva", dict(build="child", mustache=None)),
    ("nala", "राजा नल", "King Nala", dict(items={"f": "khadga"})),
    ("bhagiratha", "भगीरथ", "Bhagiratha", dict(crown="jata", lower="valkal", items={"f": "mala"})),
    ("sagara", "राजा सगर", "King Sagara", dict(build="old", beard="short")),
    ("mandhata", "मान्धाता", "Mandhata", dict(items={"f": "chakra"})),
    ("shibi", "राजा शिबि", "King Shibi", dict(items={"f": "khadga"})),
    ("rantideva", "रन्तिदेव", "Rantideva", dict(items={"f": "kalash"})),
    ("yayati", "ययाति", "Yayati", dict(build="old", beard="short")),
    ("pururava", "पुरुरवा", "Pururava", dict(items={"f": "bow"})),
    ("nahusha", "नहुष", "Nahusha", dict(items={"f": "vajra"})),
    ("prithu", "राजा पृथु", "King Prithu", dict(items={"f": "bow", "b": "arrow"})),
    ("manu", "मनु", "Manu", dict(build="old", beard="long", mustache=None)),
    ("satyavan", "सत्यवान", "Satyavan", dict(crown="jata", lower="valkal", mustache=None, items={"f": "parashu"})),
    ("ambarish", "राजा अम्बरीष", "King Ambarish", dict(items={"f": "mala"})),
    ("dilipa", "राजा दिलीप", "King Dilipa", dict(items={"f": "bow"})),
    ("raghu", "राजा रघु", "King Raghu", dict(items={"f": "bow"})),
    ("aja", "राजा अज", "King Aja", dict(items={"f": "bow"})),
    ("ikshvaku", "इक्ष्वाकु", "Ikshvaku", dict(build="old", beard="short")),
    ("mucukunda", "मुचुकुन्द", "Mucukunda", dict(build="old", beard="long", mustache=None)),
    ("kartavirya", "सहस्रबाहु कार्तवीर्य", "Kartavirya Arjuna", dict(arms=10, extra_items=["khadga", "bow", "gada", "trishul", "shakti",
                                                                                         "dhal", "parashu", "chakra"], items={"f": "khadga"})),
    ("trishanku", "त्रिशंकु", "Trishanku", dict(items={})),
    ("ashvapati", "अश्वपति", "Ashvapati", dict(build="old", beard="short")),
    ("gadhi", "राजा गाधि", "King Gadhi", dict(build="old")),
    ("vikramaditya", "विक्रमादित्य", "Vikramaditya", dict(items={"f": "khadga"})),
    ("betal", "बेताल", "Betal", dict(skin="#9a9a8a", build="slim", fangs=True, eye="round", crown="none", hair="long", hair_color="#e6e0d0",
                                     items={}, lower="loin")),
    ("drupad_kids", "राजकुमार (बाल)", "Young prince", dict(build="child", mustache=None, crown="kirita_low")),
])
add("legend", "queen", [
    ("taramati", "तारामती", "Taramati", dict(saree=["#f6efdf", "floral", "gold"])),
    ("damayanti", "दमयंती", "Damayanti", dict(saree=["#e8a03a", "floral", "maroon"])),
    ("savitri", "सावित्री", "Savitri", dict(saree=["#c8321f", "floral", "gold"])),
    ("devayani", "देवयानी", "Devayani", dict(saree=["#f6efdf", "dots", "gold"])),
    ("sharmishtha", "शर्मिष्ठा", "Sharmishtha", dict(saree=["#3a2a4a", "floral", "gold"])),
    ("shatarupa", "शतरूपा", "Shatarupa", dict(saree=["#f2c23a", "floral", "maroon"])),
    ("indumati", "इन्दुमती", "Indumati", dict(saree=["#e89ab0", "floral", "gold"])),
    ("madalasa", "मदालसा", "Madalasa", dict(saree=["#2f6a3a", "floral", "gold"])),
    ("sukanya", "सुकन्या", "Sukanya", dict(saree=["#f0a070", "floral", "gold"])),
    ("tara_brihaspati", "तारा (बृहस्पति पत्नी)", "Tara (Brihaspati's wife)", dict(saree=["#3a4a8a", "dots", "gold"])),
])
# ------------------------------------------------------------------ ensemble / generic (crowds, armies, villages)
ENSEMBLE = [
    ("ayodhya_soldier", "अयोध्या सैनिक", "Ayodhya soldier", "soldier", dict(armor="#c8a050")),
    ("ayodhya_archer", "अयोध्या धनुर्धर", "Ayodhya archer", "soldier", dict(armor="#c8a050", items={"f": "bow", "b": "arrow"})),
    ("lanka_soldier", "लंका सैनिक", "Lanka soldier", "rakshasa", dict(skin="#4a4a3a", build="hero", items={"f": "spear", "b": "dhal"})),
    ("kaurava_soldier", "कौरव सैनिक", "Kaurava soldier", "soldier", dict(armor="#6a5a7a")),
    ("pandava_soldier", "पांडव सैनिक", "Pandava soldier", "soldier", dict(armor="#c8a050")),
    ("kaurava_archer", "कौरव धनुर्धर", "Kaurava archer", "soldier", dict(armor="#6a5a7a", items={"f": "bow", "b": "arrow"})),
    ("pandava_archer", "पांडव धनुर्धर", "Pandava archer", "soldier", dict(armor="#c8a050", items={"f": "bow", "b": "arrow"})),
    ("spearman", "भालाधारी", "Spearman", "soldier", dict()),
    ("swordsman", "तलवारबाज़", "Swordsman", "soldier", dict(items={"f": "khadga", "b": "dhal"})),
    ("maceman", "गदाधारी योद्धा", "Mace warrior", "soldier", dict(items={"f": "gada"})),
    ("charioteer", "सारथी", "Charioteer (sarathi)", "commoner", dict(items={"f": "ankusha"})),
    ("dwarpal", "द्वारपाल", "Gatekeeper (dwarpal)", "warrior", dict(items={"f": "gada"}, build="heavy")),
    ("doot", "दूत", "Messenger (doot)", "commoner", dict(items={"f": "pothi"})),
    ("herald", "उद्घोषक", "Herald (with conch)", "commoner", dict(items={"f": "shankh"})),
    ("villager_man", "ग्रामीण", "Villager (man)", "commoner", dict()),
    ("villager_woman", "ग्रामीण स्त्री", "Villager (woman)", "woman", dict(items={"f": "kalash"})),
    ("farmer", "किसान", "Farmer", "commoner", dict(items={"f": "hala"})),
    ("gwala", "ग्वाला", "Cowherd boy (gwala)", "commoner", dict(build="slim", mustache=None, items={"f": "danda"}, crown="turban")),
    ("gopi", "गोपी", "Gopi", "woman", dict(items={"f": "kalash"})),
    ("boatman", "नाविक", "Boatman", "commoner", dict(items={"f": "danda"})),
    ("purohit", "पुरोहित", "Priest (purohit)", "brahmin", dict(items={"f": "kamandalu"})),
    ("pandit", "पंडित", "Pandit", "brahmin", dict()),
    ("acharya", "आचार्य", "Acharya (teacher)", "brahmin", dict(build="old", beard="short", mustache=None)),
    ("merchant", "व्यापारी", "Merchant (seth)", "yaksha", dict(build="heavy", items={"f": "bag"})),
    ("dancer", "नर्तकी", "Dancer (nartaki)", "apsara", dict()),
    ("musician_dhol", "ढोल वादक", "Drummer", "commoner", dict(items={"f": "damru"})),
    ("musician_flute", "बाँसुरी वादक", "Flute player", "commoner", dict(items={"f": "bansuri"})),
    ("musician_veena", "वीणा वादक", "Veena player", "gandharva", dict()),
    ("shankh_vadak", "शंख वादक", "Conch blower", "brahmin", dict(items={"f": "shankh"})),
    ("child_boy", "बालक", "Boy", "child", dict()),
    ("child_girl", "बालिका", "Girl", "child", dict(female=True, saree=["#e8a03a", "dots", "maroon"])),
    ("old_man", "वृद्ध", "Old man", "commoner", dict(build="old", beard="long", mustache=None, items={"f": "danda"})),
    ("old_woman", "वृद्धा", "Old woman", "woman", dict(build="old", items={"f": "danda"})),
    ("king_generic", "राजा", "King", "king", dict()),
    ("queen_generic", "रानी", "Queen", "queen", dict()),
    ("mantri", "मंत्री", "Minister (mantri)", "commoner", dict(build="heavy", items={"f": "pothi"}, crown="turban", turban_color="#3a4a8a")),
    ("senapati", "सेनापति", "Commander (senapati)", "warrior", dict(items={"f": "khadga"})),
    ("rajkumar", "राजकुमार", "Prince", "prince", dict(items={"f": "bow"})),
    ("rajkumari", "राजकुमारी", "Princess", "princess", dict()),
    ("dasi", "दासी", "Maid (dasi)", "woman", dict(items={"f": "chamara"})),
    ("sevak", "सेवक", "Servant", "commoner", dict(items={"f": "chhatra"})),
    ("palki_kahar", "कहार", "Palanquin bearer", "commoner", dict(lower="loin")),
    ("hunter", "शिकारी (शबर)", "Hunter (shabar)", "commoner", dict(skin="skin_dark", items={"f": "bow", "b": "arrow"}, lower="loin")),
    ("bhil", "भील", "Bhil tribesman", "commoner", dict(skin="skin_dark", items={"f": "bow"}, lower="loin", turban_color="#5a7a3a")),
    ("potter", "कुम्हार", "Potter", "commoner", dict(items={"f": "kalash"})),
    ("blacksmith", "लोहार", "Blacksmith", "commoner", dict(build="heavy", items={"f": "parashu"})),
    ("weaver", "बुनकर", "Weaver", "commoner", dict()),
    ("washerman", "धोबी", "Washerman", "commoner", dict(items={"f": "bag"})),
    ("cook", "रसोइया", "Cook", "commoner", dict(build="heavy", items={"f": "kalash"})),
    ("guru", "गुरु", "Guru", "rishi", dict()),
    ("shishya", "शिष्य", "Disciple", "brahmin", dict(build="child", items={"f": "pothi"})),
    ("rakshasa_soldier", "राक्षस सैनिक", "Rakshasa soldier", "rakshasa", dict(build="hero", items={"f": "spear", "b": "dhal"})),
    ("rakshasa_guard", "राक्षस प्रहरी", "Rakshasa guard", "rakshasa", dict(build="heavy", items={"f": "gada"})),
    ("asura_warrior", "असुर योद्धा", "Asura warrior", "asura", dict(items={"f": "khadga", "b": "dhal"})),
    ("vanara_soldier_1", "वानर सैनिक", "Vanara soldier", "vanara", dict(skin="#c8843a", items={"f": "gada"})),
    ("vanara_soldier_2", "वानर योद्धा", "Vanara warrior", "vanara", dict(skin="#b8743a", items={"f": "parashu"})),
    ("vanara_soldier_3", "वानर (पत्थर लिए)", "Vanara with rock", "vanara", dict(skin="#d8a85a", items={})),
    ("vanara_soldier_4", "वानर धनुर्धर", "Vanara archer", "vanara", dict(skin="#a86a3a", items={"f": "bow"})),
    ("riksha_soldier", "ऋक्ष सैनिक", "Bear soldier", "riksha", dict()),
    ("deva_soldier", "देव सैनिक", "Deva soldier", "soldier", dict(armor="#e0c070", crown="kirita_low", halo=False)),
    ("yama_doot", "यमदूत", "Yamaduta", "asura", dict(skin="#2a2a3a", items={"f": "pasha"})),
    ("vishnu_doot", "विष्णुदूत", "Vishnuduta", "deva", dict(skin="krishna", items={"f": "gada"}, halo=False)),
    ("celestial_maiden", "देवकन्या", "Celestial maiden", "apsara", dict(halo=True)),
    ("gana_soldier", "गण सैनिक", "Gana soldier", "gana", dict()),
    ("pishacha", "पिशाच", "Pishacha (ghoul)", "asura", dict(skin="#8a8a7a", build="slim", lower="loin", items={})),
    ("bhoot", "भूत", "Ghost (bhoot)", "asura", dict(skin="#c8c8c0", build="slim", lower="loin", items={})),
    ("vetala", "वेताल", "Vetala", "asura", dict(skin="#9a9a8a", build="slim", items={})),
    ("sadhu", "साधु", "Sadhu", "muni", dict()),
    ("bhikshu", "भिक्षु", "Bhikshu (monk)", "muni", dict(crown="bun", hair="short", beard=None, sash="saffron")),
    ("jogan", "जोगन", "Jogan (wandering devotee)", "woman", dict(saree=["saffron", "dots", "maroon"], items={"f": "mala"})),
    ("devdasi", "मंदिर नर्तकी", "Temple dancer", "apsara", dict(halo=False)),
    ("rajguru", "राजगुरु", "Royal preceptor", "rishi", dict(crown="jata")),
    ("jyotishi", "ज्योतिषी", "Astrologer", "brahmin", dict(build="old", beard="short", mustache=None)),
    ("vaidya", "वैद्य", "Physician (vaidya)", "brahmin", dict(items={"f": "bag"})),
    ("charan", "चारण कवि", "Bard (charan)", "commoner", dict(items={"f": "veena"})),
    ("sutradhar", "सूत्रधार", "Sutradhar (narrator-puppeteer)", "commoner", dict(crown="turban", turban_color="vermilion", items={"f": "pothi"})),
]
for id_, hi, en, tpl, ov in ENSEMBLE:
    ov = dict(ov)
    if tpl in ("commoner", "soldier", "warrior", "king", "prince"):
        ov.setdefault("dhoti", pick(DHOTI_PALETTE, id_))
        ov.setdefault("skin", pick(SKINS, id_))
        ov.setdefault("sash", pick(SASH, id_))
        ov.setdefault("turban_color", pick(["saffron", "vermilion", "#f2c23a", "#f6efdf", "#3a4a8a", "#5a7a3a"], id_))
    if tpl in ("woman", "queen", "apsara", "princess"):
        ov.setdefault("saree", pick(SAREE_PALETTE, id_))
    if tpl in ("rakshasa", "asura"):
        ov.setdefault("skin", pick(RAKSHASA_SKINS, id_))
    C.append((id_, hi, en, "ensemble", tpl, ov))


def build_characters():
    out, seen = [], set()
    for id_, hi, en, cat, tpl, ov in C:
        if id_ in seen:
            continue
        seen.add(id_)
        spec = dict(TEMPLATES.get(tpl, {}))
        spec.update(ov)
        if tpl in ("rakshasa", "asura") and "skin" not in ov:
            spec["skin"] = pick(RAKSHASA_SKINS, id_)
        if tpl == "vanara" and "skin" not in ov:
            spec["skin"] = pick(VANARA_SKINS, id_)
        if tpl in ("king", "prince", "warrior") and "dhoti" not in ov:
            spec["dhoti"] = pick(DHOTI_PALETTE, id_)
        if tpl in ("queen", "princess", "devi") and "saree" not in ov:
            spec["saree"] = pick(SAREE_PALETTE, id_)
        if tpl in ("king", "queen", "prince") and "skin" not in ov:
            spec["skin"] = pick(SKINS, id_, "s")
        if spec.get("female") and "crown" not in ov and spec.get("crown") in ("kirita", "kirita_low", "turban", "helmet"):
            spec["crown"] = "tiara"
        if spec.get("female") and "mustache" not in ov:
            spec["mustache"] = None
        if spec.get("female") and spec.get("lower", "dhoti") == "dhoti" and "lower" not in ov:
            spec["lower"] = "saree"
        entry = {"id": id_, "hi": hi, "en": en, "cat": cat, "kind": "humanoid"}
        entry.update(spec)
        out.append(entry)
    return out


# ------------------------------------------------------------------ animals
ANIMALS = [
    ("horse", "घोड़ा", "Horse", "horse", {}), ("white_horse", "सफ़ेद घोड़ा", "White horse", "horse", {"cloth": "vermilion"}),
    ("black_horse", "काला घोड़ा", "Black horse", "horse", {"color": "#2a2420", "mane_color": "#1a1410"}),
    ("brown_horse", "भूरा घोड़ा", "Brown horse", "horse", {"color": "#8a5a32"}),
    ("chariot_horse", "रथ का घोड़ा", "Chariot horse (caparisoned)", "horse", {"cloth": "vermilion"}),
    ("uchchaihshravas", "उच्चैःश्रवा", "Uchchaihshravas (divine horse)", "horse", {"cloth": "#f2c23a", "scale": 1.2}),
    ("devdatta", "देवदत्त (कल्कि का घोड़ा)", "Devadatta (Kalki's horse)", "horse", {"cloth": "#3a4a8a"}),
    ("ashwamedha_horse", "अश्वमेध का घोड़ा", "Ashvamedha horse", "horse", {"cloth": "#f2c23a"}),
    ("cow", "गाय", "Cow", "cow", {}), ("kamadhenu", "कामधेनु", "Kamadhenu", "cow", {"cloth": "#f2c23a", "bells": True}),
    ("nandini", "नंदिनी", "Nandini (Vasishtha's cow)", "cow", {"bells": True}), ("calf", "बछड़ा", "Calf", "cow", {"scale": 0.6}),
    ("nandi", "नंदी", "Nandi (Shiva's bull)", "bull", {"cloth": "vermilion", "bells": True}), ("bull", "बैल", "Bull", "bull", {}),
    ("buffalo", "भैंस", "Buffalo", "buffalo", {}), ("yama_buffalo", "यम का भैंसा", "Yama's buffalo", "buffalo", {"cloth": "#1e1e2a", "bells": True}),
    ("elephant", "हाथी", "Elephant", "elephant", {}), ("airavata", "ऐरावत", "Airavata (white elephant)", "elephant", {"color": "#efece4", "cloth": "#f2c23a"}),
    ("war_elephant", "युद्ध हाथी", "War elephant", "elephant", {"cloth": "vermilion"}),
    ("gajendra", "गजेन्द्र", "Gajendra", "elephant", {"color": "#9a9690"}), ("baby_elephant", "हाथी का बच्चा", "Baby elephant", "elephant", {"scale": 0.55}),
    ("lion", "सिंह", "Lion", "lion", {}), ("durga_lion", "दुर्गा का सिंह", "Durga's lion", "lion", {"cloth": "vermilion", "scale": 1.15}),
    ("tiger", "बाघ", "Tiger", "tiger", {}), ("durga_tiger", "दुर्गा का व्याघ्र", "Durga's tiger", "tiger", {"cloth": "vermilion"}),
    ("leopard", "तेंदुआ", "Leopard", "leopard", {}), ("cheetah", "चीता", "Cheetah", "leopard", {"color": "#e8c070"}),
    ("deer", "हिरण", "Deer", "deer", {}), ("golden_deer", "स्वर्ण मृग (मारीच)", "Golden deer (Maricha)", "deer", {"color": "#f2c23a"}),
    ("blackbuck", "काला हिरण", "Blackbuck", "deer", {"color": "#3a2a20", "pattern": None, "horns": "spiral"}),
    ("musk_deer", "कस्तूरी मृग", "Musk deer", "deer", {"color": "#8a6a4a", "horns": None}),
    ("fawn", "मृगछौना", "Fawn", "deer", {"scale": 0.6, "horns": None}),
    ("dog", "कुत्ता", "Dog", "dog", {}), ("bhairava_dog", "भैरव का श्वान", "Bhairava's dog", "dog", {"color": "#1e1a18"}),
    ("dharma_dog", "धर्मराज का श्वान", "Yudhishthira's dog", "dog", {"color": "#e8e0d0"}),
    ("wolf", "भेड़िया", "Wolf", "wolf", {}), ("jackal", "सियार", "Jackal", "jackal", {}), ("fox", "लोमड़ी", "Fox", "jackal", {"color": "#c8642a"}),
    ("boar", "सूअर", "Boar", "boar", {}), ("bear", "भालू", "Bear", "bear", {}), ("goat", "बकरी", "Goat", "goat", {}),
    ("ram", "मेढ़ा", "Ram (Agni's vahana)", "ram", {}), ("camel", "ऊँट", "Camel", "camel", {}),
    ("donkey", "गधा", "Donkey (Shitala's vahana)", "donkey", {}), ("rabbit", "खरगोश", "Rabbit (moon rabbit)", "rabbit", {}),
    ("mooshak", "मूषक (गणेश वाहन)", "Mooshak (Ganesha's mouse)", "rat", {"scale": 1.4}), ("rat", "चूहा", "Rat", "rat", {}),
    ("cat", "बिल्ली", "Cat", "cat", {}), ("monkey_animal", "बंदर", "Monkey", "monkey", {}),
    ("langur", "लंगूर", "Langur", "monkey", {"color": "#c8c0b0"}), ("rhino", "गैंडा", "Rhinoceros", "rhino", {}),
    ("mule", "खच्चर", "Mule", "donkey", {"color": "#6a5a4a"}), ("ox_pair", "बैलगाड़ी का बैल", "Cart ox", "bull", {"color": "#d8c8b0"}),
    ("gaur", "गौर (वन भैंसा)", "Gaur (Indian bison)", "buffalo", {"color": "#2a1e18"}),
    ("sambar", "साँभर", "Sambar deer", "deer", {"color": "#6a4a32", "pattern": None}),
    ("nilgai", "नीलगाय", "Nilgai", "deer", {"color": "#7a7a8a", "pattern": None, "horns": "back"}),
    ("tortoise", "कछुआ", "Tortoise (Kurma)", "rat", {"L": 20, "H": 9, "leg": 3, "lw": 3.2, "color": "#6a7a3a", "pattern": "wool",
                                                    "tail": "short", "head": "rodent", "scale": 1.6}),
    ("crocodile", "मगरमच्छ (मकर)", "Crocodile / Makara", "dog", {"L": 40, "H": 6, "leg": 4, "lw": 3.0, "color": "#4a6a4a",
                                                                   "pattern": "wool", "tail": "long_cat", "head": "canine", "neck": 2, "neck_ang": 0}),
    ("frog", "मेंढक", "Frog", "rat", {"L": 8, "H": 6, "color": "#5a8a3a", "tail": "none", "ears": "small"}),
]
SERPENTS = [("sheshnaag_animal", "शेषनाग (शय्या)", "Sheshnaag (coiled bed)", {"hoods": 7, "color": "#2f6a4a", "length": 1.4}),
            ("vasuki_animal", "वासुकि (सर्प)", "Vasuki (serpent)", {"hoods": 1, "color": "#3a6a5a", "length": 1.6}),
            ("kaliya_animal", "कालिया (सर्प)", "Kaliya (serpent)", {"hoods": 5, "color": "#1e2a2a"}),
            ("cobra", "नाग", "Cobra", {"hoods": 1, "color": "#3a3a2a"}),
            ("python", "अजगर", "Python", {"hoods": 1, "color": "#7a6a3a", "length": 1.6}),
            ("takshaka_animal", "तक्षक (सर्प)", "Takshaka (serpent)", {"hoods": 3, "color": "#5a3a2a"})]
FISH = [("matsya_fish", "मत्स्य (स्वर्ण मछली)", "Matsya (golden fish)", {"color": "#f2a23a", "size": 1.6}),
        ("fish", "मछली", "Fish", {"color": "#7aa0b8"}), ("koi", "रंगीन मछली", "Koi", {"color": "#e8833a"}),
        ("makara_fish", "मकर", "Makara (sea monster)", {"color": "#3f8f8a", "size": 2.4})]


def build_animals():
    out = []
    for id_, hi, en, base, ov in ANIMALS:
        e = {"id": id_, "hi": hi, "en": en, "cat": "animal", "kind": "quadruped", "base": base}
        e.update(ov)
        out.append(e)
    for id_, hi, en, ov in SERPENTS:
        e = {"id": id_, "hi": hi, "en": en, "cat": "serpent", "kind": "serpent"}
        e.update(ov)
        out.append(e)
    for id_, hi, en, ov in FISH:
        e = {"id": id_, "hi": hi, "en": en, "cat": "fish", "kind": "fish"}
        e.update(ov)
        out.append(e)
    return out


BIRDS = [("peacock", "मोर", "Peacock"), ("paravani", "परवाणी (कार्तिकेय का मोर)", "Paravani (Kartikeya's peacock)", "peacock", {"size": 1.3}),
         ("peahen", "मोरनी", "Peahen", "peacock", {"tail": "short", "body": "#7a8a6a", "head": "#7a8a6a", "crest": "peacock"}),
         ("hamsa", "हंस", "Hamsa (swan)"), ("saraswati_hamsa", "सरस्वती का हंस", "Saraswati's swan", "hamsa", {"size": 1.3}),
         ("brahma_hamsa", "ब्रह्मा का हंस", "Brahma's swan", "hamsa", {"size": 1.4}),
         ("eagle", "चील/गरुड़ पक्षी", "Eagle"), ("garuda_bird", "गरुड़ (पक्षी रूप)", "Garuda (bird form)"),
         ("jatayu", "जटायु", "Jatayu", "vulture", {"size": 1.6}), ("sampati", "सम्पाति", "Sampati", "vulture", {"size": 1.6, "wing": "#5a3a2a"}),
         ("vulture", "गिद्ध", "Vulture"), ("owl", "उल्लू", "Owl"), ("uluka", "उलूक (लक्ष्मी वाहन)", "Uluka (Lakshmi's owl)", "owl", {"body": "#e8dcc4", "head": "#e8dcc4", "wing": "#c8b898"}),
         ("crow", "कौआ", "Crow"), ("shani_crow", "शनि का कौआ", "Shani's crow", "crow", {"size": 1.1}),
         ("kakbhushundi", "काकभुशुण्डि", "Kakbhushundi", "crow", {"size": 1.0}), ("parrot", "तोता", "Parrot"),
         ("shuka_parrot", "शुक (कामदेव का तोता)", "Kamadeva's parrot", "parrot", {"size": 1.0}),
         ("crane", "सारस/बगुला", "Crane"), ("heron", "बगुला", "Heron"), ("sparrow", "गौरैया", "Sparrow"), ("pigeon", "कबूतर", "Pigeon"),
         ("rooster", "मुर्गा", "Rooster"), ("hen", "मुर्गी", "Hen"), ("kingfisher", "किलकिला", "Kingfisher"), ("koel", "कोयल", "Koel"),
         ("myna", "मैना", "Myna"), ("hornbill", "धनेश", "Hornbill"), ("flamingo", "राजहंस", "Flamingo"), ("kite", "चील", "Kite"),
         ("falcon", "बाज़", "Falcon"), ("stork", "लगलग", "Stork"), ("duck", "बत्तख", "Duck"), ("chakravak", "चकवा", "Chakravak (ruddy shelduck)"),
         ("bulbul", "बुलबुल", "Bulbul"), ("woodpecker", "कठफोड़वा", "Woodpecker"), ("nightingale", "बुलबुल (कोकिला)", "Nightingale"),
         ("quail", "बटेर", "Quail"), ("partridge", "तीतर", "Partridge"), ("chakor", "चकोर", "Chakor"), ("sarus", "सारस", "Sarus crane"),
         ("cuckoo", "पपीहा", "Cuckoo / Papiha"), ("hawk", "श्येन", "Hawk (shyena)"), ("pelican", "हवासील", "Pelican"),
         ("bat", "चमगादड़", "Bat"), ("butterfly", "तितली", "Butterfly"),
         ("golden_bird", "सोने की चिड़िया", "Golden bird", "sparrow", {"body": "#f2c23a", "wing": "#e0a020", "head": "#f2c23a", "size": 0.6}),
         ("gandaberunda", "गण्डभेरुण्ड", "Gandaberunda", "eagle", {"size": 1.5, "body": "#c8a040", "wing": "#a87a20"})]


def build_birds():
    out = []
    for b in BIRDS:
        id_, hi, en = b[:3]
        base = b[3] if len(b) > 3 else id_
        ov = b[4] if len(b) > 4 else {}
        e = {"id": id_, "hi": hi, "en": en, "cat": "bird", "kind": "bird", "base": base}
        e.update(ov)
        out.append(e)
    return out


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    chars = build_characters()
    animals = build_animals()
    birds = build_birds()
    for name, data in (("characters", chars), ("animals", animals), ("birds", birds)):
        with open(OUT / f"{name}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
    from collections import Counter
    print("characters:", len(chars), dict(Counter(c["cat"] for c in chars)))
    print("animals+serpents+fish:", len(animals), " birds:", len(birds), " TOTAL:", len(chars) + len(animals) + len(birds))
