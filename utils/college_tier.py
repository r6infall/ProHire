def classify_college_tier(college_name: str):
    if not college_name:
        return None

    col = college_name.lower().replace(".", "").strip()

    # ------------------------------------------------------------
    # TIER 1 – Top IITs, NITs, IIITs, BITS, DTU, NSUT, COEP, VIT
    # ------------------------------------------------------------
    tier1_keywords = [
        # IIT (Indian Institute of Technology)
        "iit", "indian institute of technology",
        
        # NIT (National Institute of Technology)
        "nit ", "national institute of technology",
        
        # IIIT (Indian Institute of Information Technology)
        "iiit", "indian institute of information technology",

        # BITS Pilani group
        "bits",
        "birla institute of technology and science",

        # VIT Vellore (ONLY Vellore is Tier-1)
        "vit vellore", "vellore institute of technology",

        # COEP
        "coep", "college of engineering pune",

        # DTU (Delhi Technological University)
        "dtu", "delhi technological university",

        # NSUT/NSIT
        "nsut", "nsit", "netaji subhas university",
        "netaji subhas institute of technology",

        # Manipal / MIT Manipal
        "manipal", "mit manipal",

        # ICT Mumbai
        "ict mumbai", "institute of chemical technology",
    ]

    # ------------------------------------------------------------
    # TIER 2 – Strong, recognized engineering universities
    # ------------------------------------------------------------
    tier2_keywords = [
        # State engineering universities
        "pict", "pune institute of computer technology",
        "vjit",
        "vjti", "veermata jijabai technological institute",

        # SPPU / Pune University
        "sppu", "savitribai phule pune university",

        # RTMNU / Nagpur University
        "rtmnu", "rashtrasant tukadoji maharaj nagpur university",

        # SRM University
        "srm", "srm university",

        # Amity University
        "amity", "amity university",

        # PES University
        "pes university", "pes institute",

        # RV College of Engineering
        "rv college", "rvce",

        # Chandigarh University
        "chandigarh university",

        # VIT campuses other than Vellore
        "vit bhopal", "vit chennai", "vit amaravati",

        # KIIT University
        "kiit", "kalinga institute of industrial technology",

        # Lovely Professional University
        "lpu", "lovely professional university",

        # MSRIT / Ramaiah
        "msrit", "ramaiah institute", "mrsit", "ms ramaiah",

        # Thapar
        "thapar", "thapar institute",

        # MIT WPU Pune (NOT MIT Manipal)
        "mit wpu", "mit world peace university",
    ]

    # ------------------------------------------------------------
    # CLASSIFICATION LOGIC
    # ------------------------------------------------------------
    if any(k in col for k in tier1_keywords):
        return "Tier 1"

    if any(k in col for k in tier2_keywords):
        return "Tier 2"

    return "Tier 3"
