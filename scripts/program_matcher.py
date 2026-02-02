#!/usr/bin/env python3
"""
Cross-year program name normalization and stable ID assignment.

Handles dash variants, whitespace, casing differences, and genuine name
changes across budget years (e.g. OPIC → DFC in 2019).
"""

from __future__ import annotations

import re
from collections import defaultdict

# ── Normalization ────────────────────────────────────────────────────────────

_DASH_RE = re.compile(r"[\u2010-\u2015\u2212\ufe58\ufe63\uff0d-]+")
_SPACE_RE = re.compile(r"\s+")
_FOOTNOTE_RE = re.compile(r"\s*\d+\s*$")
_PAREN_RE = re.compile(r"\s*\(.*?\)\s*")
_NONALNUM_RE = re.compile(r"[^a-z0-9 ]")


def _norm(s: str) -> str:
    """Normalize: lowercase, collapse dashes to hyphen, collapse whitespace."""
    if not s:
        return ""
    s = _DASH_RE.sub("-", s)
    s = _SPACE_RE.sub(" ", s)
    return s.lower().strip()


def _normalize_fuzzy(name: str) -> str:
    """Aggressive normalization for fuzzy cross-year matching."""
    if not name:
        return ""
    n = name.lower()
    n = _DASH_RE.sub(" ", n)
    n = _PAREN_RE.sub(" ", n)           # remove parentheticals
    n = _NONALNUM_RE.sub(" ", n)        # strip punctuation
    n = re.sub(r"\bloans?\b", "loan", n)
    n = re.sub(r"\bprograms?\b", "program", n)
    n = re.sub(r"\bguarantees?\b", "guarantee", n)
    n = re.sub(r"\s+\d+$", "", n)       # trailing numbers
    n = _SPACE_RE.sub(" ", n).strip()
    return n


def normalize_program_key(agency: str, bureau: str, account: str,
                          program: str) -> str:
    """
    Build a stable canonical key from the 4-level hierarchy.

    Returns a pipe-delimited normalized string:
        "agency|bureau|account|program"
    """
    parts = [
        _norm(agency or ""),
        _norm(bureau or ""),
        _norm(account or ""),
        _norm(_FOOTNOTE_RE.sub("", program or "")),
    ]
    return "|".join(parts)


# ── Program aliases for genuine name changes across years ────────────────────

PROGRAM_ALIASES = {
    # OPIC was renamed to DFC in FY2020 budget
    "overseas private investment corporation": "united states international development finance corporation",
    "opic": "dfc",
    # Education department reorganizations
    "office of postsecondary education": "office of federal student aid",
    # FFEL → Direct Loan transition terminology
    "federal family education loan": "federal direct student loan",
    # Stafford variants
    "stafford loans": "stafford",
    "stafford loan": "stafford",
    "subsidized stafford": "stafford",
    # FHA fund name changes
    "fha-mutual mortgage insurance": "fha-mutual mortgage",
    "mutual mortgage insurance": "fha-mutual mortgage",
    # Ex-Im variations
    "export-import bank direct loans": "export-import direct",
    "ex-im direct loans": "export-import direct",
    # SBA program name variations
    "7(a) general business loans": "7(a) loans",
    "general business loan guarantee": "7(a) loans",
    "section 504 certified development": "504 certified development company",
    "504 loans": "504 certified development company",
    # USDA program variations
    "farm ownership-direct": "farm ownership",
    "farm operating-direct": "farm operating",
    "farm ownership loans-direct": "farm ownership",
    "farm operating loans-direct": "farm operating",
    # Rural housing
    "single family housing direct": "section 502",
    "single family housing guaranteed": "section 502 unsubsidized guaranteed",
    "multi-family housing direct": "section 515",
    "multi-family housing guaranteed": "section 538",
}

# Precompute normalized alias mapping
_ALIAS_MAP = {_norm(k): _norm(v) for k, v in PROGRAM_ALIASES.items()}


def _apply_aliases(key: str) -> str:
    """Apply program aliases to normalized key parts."""
    parts = key.split("|")
    if len(parts) != 4:
        return key

    prog = parts[3]
    bureau = parts[1]

    # Check program name aliases
    if prog in _ALIAS_MAP:
        parts[3] = _ALIAS_MAP[prog]

    # Check bureau aliases
    if bureau in _ALIAS_MAP:
        parts[1] = _ALIAS_MAP[bureau]

    return "|".join(parts)


class ProgramRegistry:
    """
    Assigns stable integer IDs to programs discovered across years.

    Programs are identified by their normalized canonical key. Aliases are
    resolved so that renamed programs map to the same ID.
    """

    def __init__(self):
        self._next_id = 1
        # canonical_key → program_id string (e.g. "P001")
        self._key_to_id = {}
        # program_id → metadata dict
        self._programs = {}

    def register(self, agency: str, bureau: str, account: str,
                 program: str, budget_year: int = None) -> str:
        """
        Register a program and return its stable ID (e.g. "P001").

        If the program was already registered (possibly under an alias),
        returns the existing ID.
        """
        raw_key = normalize_program_key(agency, bureau, account, program)
        resolved_key = _apply_aliases(raw_key)

        if resolved_key in self._key_to_id:
            pid = self._key_to_id[resolved_key]
            # Track additional name variants and years
            meta = self._programs[pid]
            if raw_key not in meta["key_variants"]:
                meta["key_variants"].append(raw_key)
            if program and program not in meta["name_variants"]:
                meta["name_variants"].append(program)
            if budget_year and budget_year not in meta["budget_years_seen"]:
                meta["budget_years_seen"].append(budget_year)
            if program and budget_year:
                nym = meta.setdefault("name_year_map", {})
                if program not in nym or budget_year > nym[program]:
                    nym[program] = budget_year
            return pid

        # Also map the raw key so exact matches work
        if raw_key != resolved_key and raw_key in self._key_to_id:
            pid = self._key_to_id[raw_key]
            self._key_to_id[resolved_key] = pid
            meta = self._programs[pid]
            if budget_year and budget_year not in meta["budget_years_seen"]:
                meta["budget_years_seen"].append(budget_year)
            return pid

        # New program
        pid = f"P{self._next_id:03d}"
        self._next_id += 1

        self._key_to_id[resolved_key] = pid
        self._key_to_id[raw_key] = pid

        self._programs[pid] = {
            "program_id": pid,
            "canonical_name": program or "",
            "agency": agency or "",
            "bureau": bureau or "",
            "account": account or "",
            "canonical_key": resolved_key,
            "key_variants": [raw_key] if raw_key != resolved_key else [resolved_key],
            "name_variants": [program] if program else [],
            "budget_years_seen": [budget_year] if budget_year else [],
            "name_year_map": {},
        }
        if program and budget_year:
            self._programs[pid]["name_year_map"][program] = budget_year
        return pid

    def get_id(self, agency: str, bureau: str, account: str,
               program: str) -> str | None:
        """Look up the ID for a program, or None if not registered."""
        raw_key = normalize_program_key(agency, bureau, account, program)
        resolved_key = _apply_aliases(raw_key)
        return self._key_to_id.get(resolved_key) or self._key_to_id.get(raw_key)

    def get_program(self, program_id: str) -> dict | None:
        """Return metadata dict for a program ID."""
        return self._programs.get(program_id)

    def all_programs(self) -> dict:
        """Return dict of all program_id → metadata."""
        return dict(self._programs)

    def to_json(self) -> dict:
        """Export registry as JSON-serializable dict."""
        programs = {}
        for pid, meta in sorted(self._programs.items()):
            programs[pid] = {
                "program_id": pid,
                "canonical_name": meta["canonical_name"],
                "agency": meta["agency"],
                "bureau": meta["bureau"],
                "account": meta["account"],
                "name_variants": sorted(set(meta["name_variants"])),
                "budget_years_seen": sorted(meta["budget_years_seen"]),
            }
        return programs

    # ── Pass 2: fuzzy reconciliation ─────────────────────────────────────

    def reconcile(self, subsidy_rates: dict | None = None,
                  rate_tolerance: float = 0.5) -> dict:
        """
        Merge short-lived programs into longer-lived ones using fuzzy
        matching on (agency, program_name), validated by original subsidy
        rate consistency at the cohort level.

        Args:
            subsidy_rates: {program_id: {cohort_year_int: original_rate_float}}
            rate_tolerance: max absolute pct-pt difference to consider
                rates consistent (accounts for rounding across years).

        Returns:
            dict with merge stats.
        """
        # Build fuzzy groups: (fuzzy_agency, fuzzy_program) → [pid, ...]
        fuzzy_groups = defaultdict(list)
        for pid, meta in self._programs.items():
            fa = _normalize_fuzzy(meta["agency"])
            fp = _normalize_fuzzy(meta["canonical_name"])
            fuzzy_groups[(fa, fp)].append(pid)

        merges = 0
        blocked_by_rates = 0

        for (_fa, _fp), pids in fuzzy_groups.items():
            if len(pids) < 2:
                continue

            # Sort: most budget years first, then lowest ID as tiebreaker
            pids_sorted = sorted(
                pids,
                key=lambda p: (-len(self._programs[p]["budget_years_seen"]), p),
            )
            target = pids_sorted[0]

            for source in pids_sorted[1:]:
                if self._rates_consistent(target, source, subsidy_rates,
                                          rate_tolerance):
                    self._merge(source, target)
                    merges += 1
                else:
                    blocked_by_rates += 1

        return {
            "merges": merges,
            "blocked_by_rates": blocked_by_rates,
            "programs_after": len(self._programs),
        }

    def _rates_consistent(self, pid_a: str, pid_b: str,
                          subsidy_rates: dict | None,
                          tolerance: float) -> bool:
        """Check if two programs have consistent original subsidy rates."""
        if subsidy_rates is None:
            return True

        rates_a = subsidy_rates.get(pid_a, {})
        rates_b = subsidy_rates.get(pid_b, {})

        common = set(rates_a) & set(rates_b)
        if not common:
            # No overlapping cohort years — can't contradict, allow merge
            return True

        for yr in common:
            ra, rb = rates_a[yr], rates_b[yr]
            if ra is not None and rb is not None:
                if abs(ra - rb) > tolerance:
                    return False
        return True

    def _merge(self, source_pid: str, target_pid: str) -> None:
        """Merge source program into target, updating all internal maps."""
        source = self._programs[source_pid]
        target = self._programs[target_pid]

        # Merge years, name variants, key variants
        for yr in source["budget_years_seen"]:
            if yr not in target["budget_years_seen"]:
                target["budget_years_seen"].append(yr)
        for nv in source["name_variants"]:
            if nv not in target["name_variants"]:
                target["name_variants"].append(nv)
        for kv in source.get("key_variants", []):
            if kv not in target["key_variants"]:
                target["key_variants"].append(kv)

        # Merge name_year_map (keep latest year for each name)
        src_nym = source.get("name_year_map", {})
        tgt_nym = target.setdefault("name_year_map", {})
        for name, yr in src_nym.items():
            if name not in tgt_nym or yr > tgt_nym[name]:
                tgt_nym[name] = yr

        # Redirect all keys that pointed to source → target
        for key, pid in self._key_to_id.items():
            if pid == source_pid:
                self._key_to_id[key] = target_pid

        del self._programs[source_pid]

    def finalize_canonical_names(self) -> None:
        """
        Set each program's canonical_name to the variant from the most
        recent budget year (preferring FY2026 labels).
        """
        for pid, meta in self._programs.items():
            nym = meta.get("name_year_map", {})
            if not nym:
                continue
            # Pick the name with the highest year
            best_name = max(nym, key=lambda n: nym[n])
            meta["canonical_name"] = best_name
