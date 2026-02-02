#!/usr/bin/env python3
"""
12-sector classification engine for federal credit programs.

Classification priority:
  1. Program-level overrides (specific exceptions)
  2. Bureau-level rules (most classifications)
  3. Agency-level fallback (catch-all)

All matching uses normalized strings (lowercased, dash-normalized,
whitespace-collapsed).
"""

import json
import re
from pathlib import Path

# ── Sector definitions ───────────────────────────────────────────────────────

SECTORS = {
    "agriculture": {
        "name": "Agriculture",
        "description": "Farm credit, rural development, and agricultural lending",
    },
    "housing": {
        "name": "Housing",
        "description": "Residential mortgage programs, rental assistance, and housing finance",
    },
    "education": {
        "name": "Education",
        "description": "Student loans, postsecondary education credit programs",
    },
    "small_business": {
        "name": "Small Business",
        "description": "SBA lending programs and small business support",
    },
    "energy_environment": {
        "name": "Energy & Environment",
        "description": "Energy loans, environmental cleanup, and green infrastructure",
    },
    "international": {
        "name": "International",
        "description": "Export-Import Bank, development finance, foreign assistance",
    },
    "veterans": {
        "name": "Veterans",
        "description": "VA home loans and veterans benefit programs",
    },
    "healthcare": {
        "name": "Healthcare",
        "description": "Health facility loans, medical education, health program financing",
    },
    "transportation": {
        "name": "Transportation",
        "description": "Maritime, railroad, and transportation infrastructure lending",
    },
    "disaster_assistance": {
        "name": "Disaster Assistance",
        "description": "Disaster loans, flood insurance, emergency lending",
    },
    "defense_security": {
        "name": "Defense & Security",
        "description": "Defense procurement credit, homeland security lending",
    },
    "other_government": {
        "name": "Other Government",
        "description": "Treasury, Commerce, Interior, and other miscellaneous programs",
    },
}

# ── Normalization ────────────────────────────────────────────────────────────

_DASH_RE = re.compile(r"[\u2010-\u2015\u2212\ufe58\ufe63\uff0d-]+")
_SPACE_RE = re.compile(r"\s+")


def _norm(s: str) -> str:
    """Normalize string for matching: lowercase, collapse dashes/whitespace."""
    if not s:
        return ""
    s = _DASH_RE.sub("-", s)
    s = _SPACE_RE.sub(" ", s)
    return s.lower().strip()


# ── Program-level overrides (highest priority) ───────────────────────────────
# Key: (normalized_program_substring,) → sector
# Checked via substring containment against the normalized program name.

_PROGRAM_OVERRIDES = [
    # SBA disaster loans → disaster, not small_business
    ("sba disaster", "disaster_assistance"),
    ("disaster loans", "disaster_assistance"),
    ("disaster assistance", "disaster_assistance"),
    # USDA Rural Housing → housing, not agriculture
    ("rural housing", "housing"),
    ("section 502", "housing"),
    ("section 504", "housing"),
    ("section 515", "housing"),
    ("section 538", "housing"),
    # FEMA / flood
    ("flood insurance", "disaster_assistance"),
    ("national flood", "disaster_assistance"),
    # VA housing
    ("vendee", "veterans"),
    ("native american veteran", "veterans"),
    ("veterans housing", "veterans"),
    # Ginnie Mae → housing
    ("ginnie mae", "housing"),
    ("government national mortgage", "housing"),
    # FHA → housing
    ("fha", "housing"),
    ("mutual mortgage", "housing"),
    # Community development → housing
    ("community development", "housing"),
    ("section 108", "housing"),
    # Indian housing / HUD Indian programs
    ("indian housing", "housing"),
    ("indian home", "housing"),
    # TIFIA / transportation
    ("tifia", "transportation"),
    ("railroad", "transportation"),
    # Defense procurement
    ("defense production act", "defense_security"),
]

# ── Bureau-level rules ───────────────────────────────────────────────────────

_BUREAU_RULES = {
    # Agriculture
    "farm service agency": "agriculture",
    "rural business-cooperative service": "agriculture",
    "rural utilities service": "agriculture",
    "forest service": "agriculture",
    # Housing
    "rural housing service": "housing",
    "housing programs": "housing",
    "public and indian housing programs": "housing",
    "community planning and development": "housing",
    "government national mortgage association": "housing",
    # Education
    "office of postsecondary education": "education",
    "office of federal student aid": "education",
    # Energy / Environment
    "energy programs": "energy_environment",
    "environmental protection agency": "energy_environment",
    # International
    "administration of foreign affairs": "international",
    "international security assistance": "international",
    "multilateral assistance": "international",
    "agency for international development": "international",
    "united states international development finance corporation": "international",
    "export-import bank of the united states": "international",
    "overseas private investment corporation": "international",
    # Healthcare
    "health resources and services administration": "healthcare",
    "administration for a healthy america": "healthcare",
    # Veterans
    "benefits programs": "veterans",
    # Transportation
    "maritime administration": "transportation",
    # Disaster
    "federal emergency management agency": "disaster_assistance",
    # Small Business
    "small business administration": "small_business",
    # Defense
    "procurement": "defense_security",
    # Other
    "national oceanic and atmospheric administration": "other_government",
    "national institute of standards and technology": "other_government",
    "bureau of indian affairs": "other_government",
    "office of the secretary": "other_government",
    "departmental offices": "other_government",
    "corps of engineers-civil works": "other_government",
    "corps of engineers--civil works": "other_government",
}

# ── Agency-level fallback ────────────────────────────────────────────────────

_AGENCY_RULES = {
    "department of agriculture": "agriculture",
    "department of education": "education",
    "department of energy": "energy_environment",
    "department of housing and urban development": "housing",
    "department of veterans affairs": "veterans",
    "department of health and human services": "healthcare",
    "department of transportation": "transportation",
    "department of homeland security": "disaster_assistance",
    "department of defense": "defense_security",
    "department of defense-military programs": "defense_security",
    "department of state": "international",
    "department of the interior": "other_government",
    "department of commerce": "other_government",
    "department of the treasury": "other_government",
    "department of labor": "other_government",
    "small business administration": "small_business",
    "export-import bank of the united states": "international",
    "international assistance programs": "international",
    "other independent agencies": "other_government",
    "other defense civil programs": "defense_security",
}


def classify_program(agency: str, bureau: str, account: str,
                     program: str) -> str:
    """
    Classify a federal credit program into one of 12 sectors.

    Returns sector key string (e.g. "agriculture", "housing").
    """
    n_prog = _norm(program or "")
    n_bureau = _norm(bureau or "")
    n_agency = _norm(agency or "")
    n_account = _norm(account or "")

    # Priority 1: Program-level overrides
    for pattern, sector in _PROGRAM_OVERRIDES:
        if pattern in n_prog or pattern in n_account:
            return sector

    # Priority 2: Bureau-level rules
    if n_bureau:
        for pattern, sector in _BUREAU_RULES.items():
            if _norm(pattern) == n_bureau or _norm(pattern) in n_bureau:
                return sector

    # Priority 3: Agency-level fallback
    if n_agency:
        for pattern, sector in _AGENCY_RULES.items():
            if _norm(pattern) == n_agency or _norm(pattern) in n_agency:
                return sector

    return "other_government"


def export_taxonomy(output_path: Path = None) -> dict:
    """Export the taxonomy as a JSON-serializable dict."""
    taxonomy = {
        "sectors": SECTORS,
        "classification_priority": [
            "1. Program-level overrides",
            "2. Bureau-level rules",
            "3. Agency-level fallback",
        ],
        "program_override_count": len(_PROGRAM_OVERRIDES),
        "bureau_rule_count": len(_BUREAU_RULES),
        "agency_rule_count": len(_AGENCY_RULES),
    }
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(taxonomy, f, indent=2)
    return taxonomy
