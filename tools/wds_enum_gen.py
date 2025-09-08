#!/usr/bin/env python3
"""
Statistics Canada Enum Generator with Smart Truncation and Substitution
"""

import asyncio
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple
import logging

from tqdm import tqdm

from tools.writer import EnumEntry, enum_file, cleanstr


logger = logging.getLogger(__name__)

class EnumGenerator:
    def __init__(self):
        self.abbreviation_map = {
            "abd": ["abroad"],
            "ab": ["alberta"],
            "aborig": ["aboriginal"],
            "access": ["accessibility"],
            "accom": ["accommodation"],
            "acct": [
                "accounting",
                "accountant", 
                "account"
            ],
            "accept": ["accepting"],
            "act": [
                "activity", 
                "actual"
            ],
            "academ": ["academic"],
            "admin": [
                "administrative",
                "administration"
            ],
            "adv": [
                "advertising", 
                "advanced", 
                "adventure"
            ],
            "aero": ["aerospace"],
            "afflt": ["affiliate"],
            "affr": ["affair"],
            "agg": ["aggregation"],
            "aggr": ["aggregate"],
            "agmnt": ["arrangement"],
            "agric": [
                "agriculture",
                "agricultural"
            ],
            "agt": ["agent"],
            "alc": [
                "alcoholic",
                "alcohol"
            ],
            "allow": ["allowance"],
            "alt": ["alternative"],
            "anal": [
                "analysis",
                "analytical"
            ],
            "ann": [
                "annual", 
                "annually"
            ],
            "app": ["application"],
            "appl": ["appliance"],
            "appr": ["appraiser"],
            "apt": ["apartment"],
            "apprtc": [
                "apprenticeship", 
                "apprentice"
            ],
            "aquacult": ["aquaculture"],
            "arch": [
                "architectural", 
                "architect"
            ],
            "art": [
                "arts",
                "artist"
            ],
            "argmnt": ["arrangement"],
            "abs": ["absence"],
            "adapt": ["adaptation"],
            "adjust": ["adjustment"],
            "affl": ["affiliation"],
            "afford": ["affordability"],
            "agnc": ["agency"],
            "assess": ["assessment"],
            "asset": ["assets"],
            "assist": [
                "assistance",
                "assistive"
            ],
            "assoc": ["association"],
            "assur": ["assurance"],
            "attr": ["attraction"],
            "audit": ["auditing"],
            "auto": ["automotive"],
            "avail": [
                "availability",
                "available"
            ],
            "avg": ["average"],
            "aware": ["awareness"],
            "bal": ["balance"],
            "bank": ["banking"],
            "bc": ["british columbia"],
            "bcast": ["broadcasting"],
            "bev": ["beverage"],
            "biann": ["biannual"],
            "bio": ["biological"],
            "bioprod": ["bioproduct"],
            "behav": ["behaviour"],
            "bft": ["benefit"],
            "biling": ["bilingualism"],
            "biodiv": ["biodiversity"],
            "biotech": ["biotechnology"],
            "bldg": ["building"],
            "bus": ["business"],
            "can": [
                "canadian", 
                "canada", 
                "canada's"
            ],
            "cap": [
                "capital", 
                "capacity"
            ],
            "cat": ["category"],
            "cen": ["census"],
            "cert": [
                "certification", 
                "certificate"
            ],
            "chem": ["chemical"],
            "cardio": ["cardiovascular"],
            "char": ["characteristic"],
            "charit": ["charitable"],
            "chart": ["chartered"],
            "child": [
                "children",
                "child"
            ],
            "chron": ["chronic"],
            "civ": ["civil"],
            "class": [
                "classified", 
                "classification"
            ],
            "clean": ["cleaning"],
            "clg": ["college"],
            "cli": ["client"],
            "cloth": ["clothing"],
            "comm": [
                "communication",
                "community",
                "commercial",
                "commodity",
                "commercialization",
                "commissioner",
                "commuting"
            ],
            "comp": [
                "compliance", 
                "company", 
                "comparison",
                "composite", 
                "computer", 
                "component",
                "competency",
                "compensation"
            ],
            "cond": ["conditions"],
            "condo": ["condominium"],
            "cons": [
                "consolidated", 
                "consumption", 
                "consumer"
            ],
            "const": ["construction"],
            "consult": ["consulting"],
            "cont": [
                "continuing",
                "content"
            ],
            "coord": ["coordination"],
                        "copd": ["chronic obstructive pulmonary disease"],
            "corp": ["corporate"],
            "curr": ["currently"],
            "correct": ["correctional"],
            "cov": ["coverage"],
            "cred": ["credit"],
            "crush": ["crushing"],
            "ctrl": ["control"],
            "cult": ["culture"],
            "cust": ["customer"],
            "dec": [
                "decorative",
                "december"
            ],
            "def": ["defence"],
            "deg": ["degrees"],
            "del": ["delivery"],
            "demo": [
                "demographic",
                "demography"
            ],
            "demogr": ["demography"],
            "depr": ["depression"],
            "detect": ["detection"],
            "dent": ["dental"],
            "depr": [
                "deprivation",
                "depreciation"
            ],
            "dept": ["department"],
            "design": ["design"],
            "desk": ["desktop"],
            "dest": ["destination"],
            "dev": [
                "development", 
                "device",
                "developing"
            ],
            "diabl": ["disability"],
            "diff": ["differential"],
            "dir": ["directory"],
            "disc": [
                "discover",
                "discrimination"
            ],
            "disp": ["disposition"],
            "displ": ["displaced"],
            "dist": [
                "distribution",
                "distributor"
            ],
            "dgtl": ["digital"],
            "dipl": ["diploma"],
            "discl": ["disclosure"],
            "dissem": ["dissemination"],
            "div": [
                "division",
                "diversity"
            ],
            "dly": ["daily"],
            "doc": ["documentation"],
            "dom": ["domestic"],
            "dr": ["doctorate"],
            "drink": ["drinking"],
            "dwel": ["dwellings"],
            "dyn": ["dynamics"],
            "eco": ["ecosystem"],
            "earn": ["earning"],
            "econ": [
                "economic",
                "economy"
            ],
            "ed": ["edition"],
            "emo": ["emotional"],
            "est": ["estimation"],
            "ethno": ["ethnocultural"],
            "expect": ["expectancy"],
            "edu": [
                "education", 
                "educational"
            ],
            "elec": [
                "electric", 
                "electrical", 
                "electricity", 
                "electronic"
            ],
            "elem": ["elementary"],
            "emerg": ["emergency"],
            "emiss": ["emission"],
            "empl": [
                "employee",
                "employment",
                "employer"
            ],
            "en": ["english"],
            "enforce": ["enforcement"],
            "eng": ["engineering"],
            "enrol": ["enrolment"],
            "ent": [
                "entertainment", 
                "enterprise",
                "entrepreneur",
                "entrepreneurship"
            ],
            "env": [
                "environmental", 
                "environment"
            ],
            "epidem": ["epidemiological"],
            "equip": ["equipment"],
            "est": ["estimate"],
            "eval": ["evaluation"],
            "ex": ["exchange"],
            "excl": ["excluding"],
            "exec": ["executive"],
            "exp": [
                "expenditure",
                "exposure",
                "experience",
                "expense"
            ],
            "ext": ["external"],
            "extract": ["extraction"],
            "fab": ["fabricated"],
            "fac": [
                "facility", 
                "factory"
            ],
            "fact": ["factor"],
            "fam": ["family"],
            "farm": ["farming"],
            "fed": ["federal"],
            "fgn": ["foreign"],
            "fin": [
                "financial", 
                "finance", 
                "financing"
            ],
            "fish": ["fishery"],
            "fit": ["fitness"],
            "food": ["food"],
            "forest": ["forestry"],
            "fr": ["french"],
            "func": ["functional"],
            "furn": ["furniture"],
            "gas": ["gasoline"],
            "gdp": ["gross domestic product"],
            "gen": [
                "generating", 
                "general",
                "genetic",
                "generation"
            ],
            "geo": ["geography"],
            "geomat": ["geomatics"],
            "geospat": ["geospatial"],
            "ghg": ["greenhouse gas"],
            "glbl": [
                "global",
                "globalization"
            ],
            "gov": [
                "governance",
                "government"
            ],
            "govt": ["government"],
            "grad": ["graduate"],
            "guide": ["guidelines"],
            "grp": ["group"],
            "haz": [
                "hazard",
                "hazardous"
            ],
            "health": ["healthcare"],
            "her": ["heritage"],
            "hh": ["household"],
            "hist": ["history"],
            "horticult": ["horticulture"],
            "hosp": ["hospitality"],
            "hw": ["hardware"],
            "id": ["identity"],
            "idx": [
                "index",
                "indexes",
                "indice"
            ],
            "icd": ["international classification of diseases"],
            "immigr": [
                "immigration",
                "immigrant"
            ],
            "incl": [
                "inclusion",
                "including"
            ],
            "ineq": ["inequality"],
            "infer": ["inference"],
            "inet": ["internet"],
            "instr": ["instruction"],
            "invlv": ["involving"],
            "improv": ["improvement"],
            "inc": ["income"],
            "ind": [
                "independent",
                "independence",
                "individual",
                "indicator",
                "industry",
                "industrial"
            ],
            "indig": ["indigenous"],
            "info": ["information"],
            "infra": ["infrastructure"],
            "init": ["initiative"],
            "innov": [
                "innovation",
                "innovative"
            ],
            "ins": ["insurance"],
            "inst": [
                "installation", 
                "institution", 
                "institutional"
            ],
            "insul": ["insulating"],
            "int": [
                "integration", 
                "integrated"
            ],
            "intel": [
                "intellectual",
                "intelligence"
            ],
            "intend": ["intended"],
            "intent": ["intention"],
            "intermed": ["intermediary"],
            "interp": ["interpretation"],
            "intl": ["international"],
            "invent": ["inventory"],
            "invest": [
                "investment", 
                "invested"
            ],
            "io": [
                "input-output", 
                "input output"
            ],
            "iso": ["isolated"],
            "know": ["knowledge"],
            "lab": ["labour"],
            "lang": ["language"],
            "learn": ["learning"],
            "lease": ["leasing"],
            "legal": ["legal"],
            "lend": ["lending"],
            "lg": ["large"],
            "liab": ["liability"],
            "lic": ["licensing"],
            "limit": ["limitation"],
            "listen": ["listening"],
            "lit": ["literacy"],
            "liv": ["living"],
            "loan": ["loan"],
            "loc": ["local"],
            "log": ["logistics"],
            "long": ["longitudinal"],
            "lvl": ["level"],
            "mach": [
                "machine", 
                "machinery"
            ],
            "maint": ["maintenance"],
            "maj": [
                "majority", 
                "major"
            ],
            "mat": [
                "material",
                "maternity"
            ],
            "math": ["mathematic"],
            "meas": ["measures"],
            "mech": ["mechanical"],
            "med": [
                "medical", 
                "medium"
            ],
            "media": ["media"],
            "merch": ["merchandise"],
            "meth": ["method"],
            "metro": ["metropolitan"],
            "mfg": [
                "manufacture", 
                "manufactured", 
                "manufacturing"
            ],
            "map": ["mapping"],
            "mgmt": ["management"],
            "mig": ["migration"],
            "min": [
                "mining",
                "minority",
                "minimum"
            ],
            "miscond": ["misconduct"],
            "mkt": [
                "market", 
                "marketing"
            ],
            "mod": ["modification"],
            "mort": ["mortality"],
            "multinat": ["multinational"],
            "mob": ["mobile"],
            "mod": ["module"],
            "mon": [
                "monitoring", 
                "monthly"
            ],
            "mot": ["motion"],
            "mort": ["mortgage"],
            "motiv": ["motivation"],
            "munic": ["municipal"],
            "mvmt": ["movement"],
            "na": ["not applicable"],
            "nanotech": ["nanotechnology"],
            "nat": [
                "natural", 
                "nature",
                "nation"
            ],
            "natl": ["national"],
            "net": ["network"],
            "neuro": ["neurological"],
            "ns": ["nova scotia"],
            "nu": ["nunavut"],
            "num": ["number"],
            "nutr": ["nutrition"],
            "occ": ["occupation"],
            "off": ["official"],
            "on": ["ontario"],
            "oper": [
                "operator",
                "operating"
            ],
            "opport": ["opportunity"],
            "ops": ["operation"],
            "org": [
                "organization",
                "organizational"
            ],
            "orient": ["orientation"],
            "owner": ["ownership"],
            "orig": ["origin"],
            "osb": ["oriented strandboard"],
            "part": ["participation"],
            "partner": ["partnership"],
            "pass": ["passenger"],
            "periph": ["peripheral"],
            "pat": ["pattern"],
            "perc": [
                "perception",
                "perceived"
            ],
            "perf": [
                "performing",
                "performance"
            ],
            "perm": ["permanent"],
            "pens": ["pension"],
            "phys": ["physical"],
            "pract": ["practice"],
            "preg": ["pregnancy"],
            "prob": ["problems"],
            "period": ["periodical"],
            "pers": [
                "personal", 
                "personnel"
            ],
            "petro": ["petroleum"],
            "petrochem": ["petrochemical"],
            "pharm": ["pharmaceutical"],
            "phys": ["physical"],
            "pict": ["picture"],
            "pkg": ["packaging"],
            "plan": ["planning"],
            "plt": ["plant"],
            "pol": ["policy"],
            "pop": [
                "population", 
                "populaires"
            ],
            "port": ["portrait"],
            "pos": ["position"],
            "postsec": ["postsecondary"],
            "ppl": [
                "people",
                "person"
            ],
            "ppe": ["personal protective equipment"],
            "pr": ["public relation"],
            "prelim": ["preliminary"],
            "prep": ["preparedness"],
            "pres": ["pressure"],
            "prev": ["prevention"],
            "pri": ["primary"],
            "prio": ["priorities"],
            "print": ["printing"],
            "priv": [
                "privacy", 
                "private"
            ],
            "prob": ["problem"],
            "proc": [
                "process", 
                "processing", 
                "procurement", 
                "procedure",
                "processor"
            ],
            "prod": [
                "production",
                "productivity",
                "product",
                "producer"
            ],
            "prof": ["professional"],
            "prog": [
                "program",
                "programme"
            ],
            "proj": [
                "project", 
                "projection"
            ],
            "promo": ["promotor"],
            "prop": ["property"],
            "prosec": ["prosecutorial"],
            "protect": ["protection"],
            "prov": [
                "provincial",
                "province",
                "provider",
                "provision"
            ],
            "ptnr": ["partner"],
            "pub": [
                "publishing", 
                "public", 
                "publisher"
            ],
            "purch": [
                "purchasing", 
                "purchase"
            ],
            "pwr": ["power"],
            "qtr": ["quarterly"],
            "qual": [
                "quality",
                "qualification"
            ],
            "quest": ["questionnaire"],
            "real": ["real estate"],
            "rec": [
                "recreation", 
                "record", 
                "recording"
            ],
            "recov": ["recovery"],
            "recpt": ["receipt"],
            "ref": [
                "refined",
                "reference"
            ],
            "reg": ["region"],
            "relig": ["religious"],
            "renum": ["remuneration"],
            "resp": ["response"],
            "retire": ["retirement"],
            "rev": [
                "revenue",
                "revision"
            ],
            "rx": ["prescription"],
            "reg": [
                "registration", 
                "registered", 
                "regulatory", 
                "register",
                "registry",
                "regulation",
                "region"
            ],
            "regr": ["regression"],
            "rel": [
                "related",
                "release"
            ],
            "reno": ["renovation"],
            "rent": ["rental"],
            "rep": [
                "repair", 
                "reporting", 
                "report",
                "reported"
            ],
            "req": ["requirement"],
            "res": [
                "research",
                "residential",
                "resource",
                "resident"
            ],
            "resil": ["resilience"],
            "resp": ["respondent"],
            "rest": ["restaurant"],
            "restric": ["restriction"],
            "ret": ["retail"],
            "rev": ["revenue"],
            "sal": ["salary"],
            "sat": ["satellite"],
            "sched": ["scheduling"],
            "sci": [
                "scientific", 
                "science"
            ],
            "sec": [
                "security", 
                "secondary", 
                "second"
            ],
            "sect": ["sector"],
            "sel": [
                "selected", 
                "selection"
            ],
            "semiann": [
                "semi-annually", 
                "semiannually"
            ],
            "serv": [
                "service", 
                "server"
            ],
            "sex": ["sexual"],
            "ship": [
                "shipping", 
                "shipment"
            ],
            "sav": ["saving"],
            "sm": ["small"],
            "soc": [
                "social",
                "society"
            ],
            "socecon": ["socioeconomic"],
            "soft": ["software"],
            "spec": [
                "specification", 
                "special",
                "specialty",
                "spectator"
            ],
            "spend": ["spending"],
            "sport": ["sport"],
            "src": ["source"],
            "stat": [
                "statistic",
                "statistical"
            ],
            "std": [
                "standard",
                "sexually transmitted disease"
            ],
            "subs": ["subsidiary"],
            "subst": ["substance"],
            "suppr": ["suppressed to meet the confidentiality requirements of the statistics act"],
            "stmnt": ["statement"],
            "stor": ["storage"],
            "stn": ["station"],
            "strat": [
                "strategy", 
                "strategic"
            ],
            "struct": ["structural"],
            "sts": ["status"],
            "stud": ["student"],
            "subprov": ["subprovincial"],
            "suff": ["sufficiency"],
            "supp": [
                "supply", 
                "support", 
                "supplementary"
            ],
            "surv": [
                "survey",
                "surveying"
            ],
            "svcs": ["service"],
            "sys": ["system"],
            "tab": ["tablet"],
            "tabl": ["table"],
            "tax": ["taxation"],
            "tech": [
                "technical", 
                "technology",
                "technological"
            ],
            "telecom": ["telecommunication"],
            "terr": [
                "territorial",
                "territory"
            ],
            "test": ["testing"],
            "text": ["textile"],
            "theat": ["theatre"],
            "thera": ["therapeutic"],
            "therm": ["thermal"],
            "tour": ["tourism"],
            "track": ["tracking"],
            "train": ["training"],
            "trans": [
                "transportation",
                "transaction",
                "transit",
                "transport",
                "transmission",
                "translation",
                "transition",
                "transfer"
            ],
            "triann": [
                "triennial",
                "triannual"
            ],
            "truck": ["trucking"],
            "trust": ["trusteed"],
            "trvl": [
                "travel", 
                "traveller"
            ],
            "tv": ["television"],
            "unempl": ["unemployment"],
            "union": ["unionization"],
            "ui": ["user interface"],
            "uni": ["university"],
            "usa": [
                "u.s.a.", 
                "united states of america", 
                "united states"
            ],
            "util": ["utility"],
            "ux": ["user experience"],
            "vacc": ["vaccination"],
            "val": ["value"],
            "var": ["variable"],
            "veg": ["vegetable"],
            "vehic": ["vehicle"],
            "vend": [
                "vendor", 
                "vending"
            ],
            "vet": [
                "veterinary",
                "veteran"
            ],
            "victim": ["victimization"],
            "vid": ["video"],
            "voc": ["vocational"],
            "vict": ["victimization"],
            "vol": [
                "volunteer",
                "volunteering"
            ],
            "vul": ["vulnerability"],
            "ware": ["warehouse"],
            "web": ["website"],
            "who": ["world health organization"],
            "wkly": ["weekly"],
            "whole": ["wholesale"],
            "xmas": ["christmas"],
            "xsect": ["cross-sectional"],
            "yr": ["yearly"]
        }

        # Automatic plural handling - no manual list needed!
        
        # Pre-compute optimized substitution lookup for performance
        self._preprocessed_substitutions = self._build_optimized_substitution_lookup()
        
        print(f"Loaded {len(self.abbreviation_map)} abbreviation mappings")
        print(f"Pre-processed {len(self._preprocessed_substitutions)} substitution patterns")

    def _build_optimized_substitution_lookup(self) -> dict[str, str]:
        """
        Build an optimized lookup table for fast substitution.
        Ordered by: containment relationships first, then length (longest first).
        """
        # Collect all term -> abbreviation mappings
        term_abbrev_pairs = []
        for abbrev, possible_matches in self.abbreviation_map.items():
            for full_term in possible_matches:
                term_abbrev_pairs.append((full_term.lower(), abbrev))
        
        # Sort by intelligent hierarchy:
        # 1. Terms that contain other terms should be processed first
        # 2. Then by length (longest first) for better specificity
        def sort_key(pair):
            term, abbrev = pair
            
            # Count how many other terms this term contains
            containment_count = 0
            for other_term, _ in term_abbrev_pairs:
                if other_term != term and other_term in term:
                    containment_count += 1
            
            # Primary sort: containment count (descending)
            # Secondary sort: length (descending)
            return (-containment_count, -len(term))
        
        term_abbrev_pairs.sort(key=sort_key)
        
        # Build the lookup dictionary
        return dict(term_abbrev_pairs)

    def generate_tense_and_noun_variants(self, base_word: str) -> list[str]:
        """
        Generate tense and noun suffix variants for a given base word.
        Returns list of potential variants to search for in text.
        """
        variants = []
        word_lower = base_word.lower()
        
        # Past tense variants (-ed)
        variants.append(word_lower + 'ed')
        if word_lower.endswith('e'):
            variants.append(word_lower + 'd')  # dance -> danced
        elif word_lower.endswith('y') and len(word_lower) > 1 and word_lower[-2] not in 'aeiou':
            variants.append(word_lower[:-1] + 'ied')  # carry -> carried
        elif len(word_lower) > 1 and word_lower[-1] in 'bdfgklmnprstv' and word_lower[-2] in 'aeiou':
            variants.append(word_lower + word_lower[-1] + 'ed')  # stop -> stopped
        
        # Present participle / gerund (-ing)
        variants.append(word_lower + 'ing')
        if word_lower.endswith('e') and not word_lower.endswith('ee'):
            variants.append(word_lower[:-1] + 'ing')  # make -> making
        elif len(word_lower) > 1 and word_lower[-1] in 'bdfgklmnprstv' and word_lower[-2] in 'aeiou':
            variants.append(word_lower + word_lower[-1] + 'ing')  # run -> running
        
        # Noun forms (-tion, -sion, -ation, -ment, -ness, -ity, -ty)
        noun_suffixes = ['tion', 'sion', 'ation', 'ment', 'ness', 'ity', 'ty', 'er', 'or', 'ist', 'ism']
        for suffix in noun_suffixes:
            variants.append(word_lower + suffix)
            
            # Handle common transformations
            if word_lower.endswith('e') and suffix in ['tion', 'sion', 'ation']:
                variants.append(word_lower[:-1] + suffix)  # create -> creation
            elif word_lower.endswith('y') and suffix in ['tion', 'sion']:
                variants.append(word_lower[:-1] + 'i' + suffix)  # apply -> application
        
        # Adjective forms (-able, -ible, -ful, -less, -ous, -al, -ic)
        adj_suffixes = ['able', 'ible', 'ful', 'less', 'ous', 'al', 'ic', 'ive', 'ant', 'ent']
        for suffix in adj_suffixes:
            variants.append(word_lower + suffix)
            if word_lower.endswith('e') and suffix in ['able', 'ible', 'ous', 'al', 'ic', 'ive']:
                variants.append(word_lower[:-1] + suffix)
        
        # Remove duplicates and filter out very short results
        variants = [v for v in set(variants) if len(v) >= 3]
        return variants

    def apply_automatic_morphological_substitution(self, text: str) -> str:
        """
        Apply substitutions for tenses, noun forms, and other morphological variants.
        Uses the optimized lookup for fast processing.
        """
        result = text
        
        # Get all base words from abbreviation map
        base_words = set()
        for abbrev, word_list in self.abbreviation_map.items():
            for word in word_list:
                words = re.findall(r'\b[a-zA-Z]+\b', word.lower())
                base_words.update(words)
        
        # For each base word, generate variants and substitute
        for base_word in base_words:
            if len(base_word) < 3:  # Skip very short words
                continue
                
            variants = self.generate_tense_and_noun_variants(base_word)
            
            for variant in variants:
                if variant != base_word:  # Don't substitute word with itself
                    pattern = r'\b' + re.escape(variant) + r'\b'
                    result = re.sub(pattern, base_word, result, flags=re.IGNORECASE)
        
        return result

    def generate_plural_variants(self, singular_word: str) -> list[str]:
        """
        Generate all possible plural variants for a given singular word.
        Returns list of potential plurals to search for in text.
        """
        variants = []
        word_lower = singular_word.lower()
        
        # Standard plurals - add 's'
        variants.append(word_lower + 's')
        
        # Words ending in 'y' -> 'ies' (but not if preceded by vowel)
        if word_lower.endswith('y') and len(word_lower) > 1:
            if word_lower[-2] not in 'aeiou':  # consonant + y -> ies
                variants.append(word_lower[:-1] + 'ies')
        
        # Words ending in 's', 'ss', 'sh', 'ch', 'x', 'z' -> 'es'
        if word_lower.endswith(('s', 'ss', 'sh', 'ch', 'x', 'z')):
            variants.append(word_lower + 'es')
        
        # Words ending in 'f' or 'fe' -> 'ves'
        if word_lower.endswith('f'):
            variants.append(word_lower[:-1] + 'ves')
        elif word_lower.endswith('fe'):
            variants.append(word_lower[:-2] + 'ves')
        
        # Words ending in 'o' -> 'oes' (for some words)
        if word_lower.endswith('o'):
            variants.append(word_lower + 'es')
        
        # Irregular plurals for common words
        irregular_plurals = {
            'man': 'men',
            'woman': 'women', 
            'child': 'children',
            'person': 'people',
            'foot': 'feet',
            'tooth': 'teeth',
            'mouse': 'mice',
            'goose': 'geese'
        }
        
        if word_lower in irregular_plurals:
            variants.append(irregular_plurals[word_lower])
        
        # Remove duplicates and return
        return list(set(variants))

    def apply_optimized_substitutions(self, text: str) -> str:
        """
        Apply optimized substitutions using pre-computed lookup table.
        Much faster than the old hierarchical approach.
        """
        result = text.lower()
        
        # Apply substitutions in optimized order
        for full_term, abbrev in self._preprocessed_substitutions.items():
            if full_term in result:
                pattern = r'\b' + re.escape(full_term) + r'\b'
                matches = list(re.finditer(pattern, result, re.IGNORECASE))
                if matches:
                    # Replace from right to left to preserve positions
                    for match in reversed(matches):
                        start_pos = match.start()
                        original_text = text[start_pos:match.end()]  # Preserve original case
                        
                        # Preserve case of first character
                        if original_text[0].isupper():
                            abbrev_with_case = abbrev.capitalize()
                        else:
                            abbrev_with_case = abbrev
                        
                        result = result[:start_pos] + abbrev_with_case.lower() + result[match.end():]
                        text = text[:start_pos] + abbrev_with_case + text[match.end():]
        
        return text
    
    def apply_automatic_plural_substitution(self, text: str) -> str:
        """
        Automatically substitute plurals with singulars based on abbreviation map values.
        For each singular word in our abbreviation map, find and replace its plural forms.
        """
        result = text
        
        # Get all singular words from abbreviation map values
        singular_words = set()
        for abbrev, word_list in self.abbreviation_map.items():
            for word in word_list:
                # Split compound terms and collect individual words
                words = re.findall(r'\b[a-zA-Z]+\b', word.lower())
                singular_words.update(words)
        
        # For each singular word, generate plurals and substitute
        for singular in singular_words:
            if len(singular) < 3:  # Skip very short words
                continue
                
            plural_variants = self.generate_plural_variants(singular)
            
            for plural in plural_variants:
                if plural != singular:  # Don't substitute word with itself
                    # Use word boundary regex for precise replacement
                    pattern = r'\b' + re.escape(plural) + r'\b'
                    result = re.sub(pattern, singular, result, flags=re.IGNORECASE)
        
        return result

    def apply_string_cleanup(self, s: str) -> str:
        """Apply comprehensive string cleanup including automatic plurals and morphological handling"""
        if not s:
            return s

        # Apply automatic plural to singular conversions
        result = self.apply_automatic_plural_substitution(s)
        
        # Apply morphological transformations (tenses, noun forms, etc.)
        result = self.apply_automatic_morphological_substitution(result)

        # Remove extra whitespace and normalize
        result = ' '.join(result.split())
        
        # Remove common problematic characters
        result = result.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        
        return result

    def apply_enhanced_abbreviations(self, s: str) -> str:
        """Apply comprehensive abbreviations with optimized lookup"""
        if not s:
            return s

        # First apply string cleanup including plurals and morphological variants
        s_processed = self.apply_string_cleanup(s)

        # Apply optimized substitutions
        result = self.apply_optimized_substitutions(s_processed)

        return result

    def apply_smart_truncation_iterative(self, name: str, original_name: str, all_original_names: list[str], all_processed_names: dict[str, str]) -> str:
        """
        Iterative smart truncation that ensures no duplicates are created.
        
        Args:
            name: Current processed name
            original_name: Original unprocessed name
            all_original_names: List of all original names for uniqueness checking
            all_processed_names: Dict mapping original names to their processed versions
        """
        truncation_patterns = [' - ', ' including ', ', including ', ' (', ' [']
        
        for pattern in truncation_patterns:
            if pattern.lower() in original_name.lower():
                pattern_pos = original_name.lower().find(pattern.lower())
                if pattern_pos == -1:
                    continue

                before_pattern = original_name[:pattern_pos].strip()
                
                # Apply the same processing pipeline to the truncated version
                truncated_abbreviated = self.apply_enhanced_abbreviations(before_pattern)
                truncated_clean = cleanstr(truncated_abbreviated)
                
                # Check for conflicts with other processed names
                conflicts = 0
                for other_original, other_processed in all_processed_names.items():
                    if other_original != original_name and other_processed == truncated_clean:
                        conflicts += 1
                
                # Also check against remaining unprocessed names that would produce the same result
                for other_name in all_original_names:
                    if other_name != original_name and other_name not in all_processed_names:
                        # Simulate processing this other name
                        other_abbreviated = self.apply_enhanced_abbreviations(other_name)
                        other_clean = cleanstr(other_abbreviated)
                        if other_clean == truncated_clean:
                            conflicts += 1

                if conflicts == 0:
                    return truncated_clean

        return name

    async def get_codes_data(self) -> dict[str, Any]:
        """Get Statistics Canada codes data (cached or fresh)"""
        codes_file = Path('codes_data.json')
        if codes_file.exists():
            print("Loading cached codes data...")
            with open(codes_file) as f:
                return json.load(f)

        print("Fetching fresh codes data from Statistics Canada WDS API...")
        from statscan.wds.client import Client
        client = Client(timeout=30)
        codes = await client.get_code_sets()

        with open(codes_file, 'w') as f:
            json.dump(codes, f, indent=2)
        print("Codes data cached successfully")

        return codes

    def detect_keys(self, entry_dict: dict[str, Any]) -> tuple[str, str, set[str]]:
        """Smart detection of key and value fields in entry dictionaries"""
        remaining_keys = set()
        key_key = None
        value_key = None

        for k in entry_dict.keys():
            if k.endswith("DescEn"):
                key_key = k
            elif k.endswith("Code"):
                value_key = k
            else:
                remaining_keys.add(k)

        if key_key is None:
            for k in entry_dict.keys():
                if k.endswith("En"):
                    key_key = k
                    remaining_keys.discard(k)
                    break

        if value_key is None:
            for k in entry_dict.keys():
                if k.endswith("Id"):
                    value_key = k
                    remaining_keys.discard(k)
                    break

        if key_key is None or value_key is None:
            raise ValueError(f"Could not detect key fields. Available: {list(entry_dict.keys())}")

        return key_key, value_key, remaining_keys

    def camel_to_title_case(self, camel: str) -> str:
        """Convert camelCase to TitleCase for class names"""
        # Insert space before uppercase letters that follow lowercase letters
        spaced = re.sub(r'([a-z])([A-Z])', r'\1 \2', camel)
        # Title case each word and remove spaces
        return ''.join(word.capitalize() for word in spaced.split())

    def camel_to_snake(self, camel: str) -> str:
        """Convert camelCase to snake_case for file names"""
        return re.sub(r'(?<!^)(?=[A-Z])', '_', camel).lower()

    def generate_single_enum(self, code_set_name: str, code_set_data: list[dict], output_dir: Path) -> Path:
        """Generate a single enum file with enhanced processing"""
        print(f"\nProcessing: {code_set_name}")
        
        key_key, value_key, remaining_keys = self.detect_keys(code_set_data[0])
        print(f"  Detected keys - Name: {key_key}, Value: {value_key}")

        # First pass: collect and validate all entries
        all_original_names = []
        valid_entries_data = []
        skipped = 0
        
        for entry_dict in code_set_data:
            try:
                original_name = entry_dict[key_key]
                raw_value = entry_dict[value_key]

                if not original_name or original_name is None:
                    skipped += 1
                    continue

                if isinstance(raw_value, str):
                    value = int(raw_value)
                else:
                    value = int(raw_value)

                all_original_names.append(original_name)
                valid_entries_data.append({
                    'original_name': original_name,
                    'value': value,
                    'entry_dict': entry_dict
                })

            except (KeyError, ValueError, TypeError):
                skipped += 1
                continue

        # Second pass: process entries with iterative smart truncation
        entries: list[EnumEntry] = []
        processed_names: dict = {}
        print(f"  Processing {len(valid_entries_data)} entries...")

        for entry_data in tqdm(valid_entries_data, desc=f"  {code_set_name}", leave=False):
            original_name = entry_data['original_name']
            value = entry_data['value']
            entry_dict = entry_data['entry_dict']

            # Apply enhanced abbreviations and string cleanup
            abbreviated_name = self.apply_enhanced_abbreviations(original_name)
            
            # Apply iterative smart truncation
            final_name = self.apply_smart_truncation_iterative(
                abbreviated_name, 
                original_name, 
                all_original_names, 
                processed_names
            )
            
            # Store the processed name for duplicate checking
            processed_names[original_name] = final_name

            # Collect metadata for comment
            comment_data = {k: entry_dict[k] for k in remaining_keys if k in entry_dict}
            
            comment = f"({original_name})"
            if comment_data:
                comment += f" {comment_data}"

            comment = comment.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
            comment = ' '.join(comment.split())

            if len(comment) > 200:
                comment = comment[:197] + "..."

            entry = EnumEntry(
                key=final_name,
                value=value,
                comment=comment
            )
            entries.append(entry)

        if not entries:
            raise ValueError(f"No valid entries found for {code_set_name}")

        # Generate enum file
        output_dir.mkdir(parents=True, exist_ok=True)

        enum_name = self.camel_to_title_case(code_set_name)
        filename = self.camel_to_snake(code_set_name) + '.py'
        file_path = output_dir / filename

        imports = {'enum': 'Enum'}

        with enum_file(file_path, imports, overwrite=True) as f:
            f.write(f'\n\nclass {enum_name}(Enum):\n')
            f.write(f'    """Statistics Canada {enum_name} codes"""\n\n')

            written_keys = set()
            for entry in entries:
                suffix = ''
                idx = 0

                while entry.clean_key(uppercase=True, suffix=suffix) in written_keys:
                    idx += 1
                    suffix = f'_{idx}'

                if suffix:
                    print(f"    Duplicate key found: {entry.key} -> {entry.key}{suffix}")

                clean_key = entry.write_entry(f, indent=4, uppercase=True, suffix=suffix)
                written_keys.add(clean_key)

        success_msg = f"  Generated {filename} with {len(entries)} entries"
        if skipped > 0:
            success_msg += f" (skipped {skipped})"
        print(success_msg)

        return file_path

    async def generate_all_enums(self, output_dir: Path) -> dict[str, Path]:
        """Generate all Statistics Canada enums with comprehensive progress tracking"""
        print("Starting Enum Generation!")
        print("=" * 60)

        output_dir.mkdir(parents=True, exist_ok=True)

        codes_data = await self.get_codes_data()

        code_sets = list(codes_data.keys())
        total_sets = len(code_sets)
        print(f"Found {total_sets} Statistics Canada code sets to process")

        gen_map = {}
        fail_map: dict = {}

        print("\nProcessing all code sets...")
        for code_set_name in tqdm(code_sets, desc="Overall Progress"):
            code_set_data = codes_data[code_set_name]
            try:
                gen_map[code_set_name] = self.generate_single_enum(code_set_name, code_set_data, output_dir)
            except Exception as e:
                logger.error(f"Failed to generate enum for {code_set_name}: {e}")
                fail_map[code_set_name] = e

        print("\n" + "=" * 60)
        print("GENERATION COMPLETE!")
        print(f"Successfully generated: {len(gen_map)} enums")
        if (n_failed := len(fail_map)) > 0:
            print(f"Failed: {n_failed} enums")
        print(f"Output directory: {output_dir}")

        return gen_map

    # ===== OPTIMIZED PROCESSING METHODS =====
    
    def _build_complete_substitution_dict(self):
        """
        Build a complete dictionary of all original terms -> substitutions
        including abbreviations, plurals, and morphological variants.
        Returns dict in intelligent order (longer patterns first).
        """
        substitutions = {}
        
        # Add abbreviation mappings
        for abbrev, full_terms in self.abbreviation_map.items():
            for term in full_terms:
                substitutions[term] = abbrev
        
        # Add automatic plural conversions
        for abbrev, full_terms in self.abbreviation_map.items():
            for term in full_terms:
                # Generate plural forms and map them to singular abbreviations
                plural_variants = self.generate_plural_variants(term)
                for plural in plural_variants:
                    if plural != term:  # Don't override the singular
                        substitutions[plural] = abbrev
        
        # Add morphological variants (tenses, noun forms)
        for abbrev, full_terms in self.abbreviation_map.items():
            for term in full_terms:
                variants = self.generate_tense_and_noun_variants(term)
                for variant in variants:
                    if variant != term and variant not in substitutions:
                        substitutions[variant] = abbrev
        
        # Sort by length (longest first) for proper substitution order
        sorted_substitutions = dict(sorted(substitutions.items(), 
                                         key=lambda x: len(x[0]), 
                                         reverse=True))
        
        return sorted_substitutions

    def _find_applicable_substitutions(self, text: str, all_substitutions):
        """
        Find substitutions that apply to this specific text.
        Returns list of (original_term, replacement) tuples.
        """
        applicable = []
        text_lower = text.lower()
        
        for original, replacement in all_substitutions.items():
            if original.lower() in text_lower:
                # Check for word boundaries to avoid partial matches
                pattern = r'\b' + re.escape(original) + r'\b'
                if re.search(pattern, text, re.IGNORECASE):
                    applicable.append((original, replacement))
        
        return applicable

    def _apply_substitutions_optimized(self, text: str, substitutions):
        """
        Apply substitutions in the correct order (longest first).
        Preserves case and handles word boundaries.
        """
        result = text
        
        for original, replacement in substitutions:
            pattern = r'\b' + re.escape(original) + r'\b'
            
            def replace_with_case(match):
                matched_text = match.group()
                if matched_text[0].isupper():
                    return replacement.capitalize()
                else:
                    return replacement.lower()
            
            result = re.sub(pattern, replace_with_case, result, flags=re.IGNORECASE)
        
        return result

    def process_items_optimized(self, items):
        """
        Optimized processing pipeline:
        1. Build complete substitution dictionary
        2. For each item: find applicable subs, apply truncation, apply subs, clean
        3. Handle duplicate names with suffix strategy
        """
        print("Building complete substitution dictionary...")
        all_substitutions = self._build_complete_substitution_dict()
        print(f"Built {len(all_substitutions)} substitution patterns")
        
        processed_items = []
        name_usage = {}  # Track name usage for conflict resolution
        
        print("Processing items with optimized substitutions...")
        for item in tqdm(items, desc="Processing items"):
            original_name = item.get('name', '')
            if not original_name:
                continue
                
            # Store original for potential reversion
            item['original_name'] = original_name
            
            # Find applicable substitutions for this specific item
            applicable_subs = self._find_applicable_substitutions(original_name, all_substitutions)
            
            # Apply truncation first (before substitutions)
            truncated_name = self._apply_smart_truncation(original_name)
            
            # Apply substitutions to truncated name
            substituted_name = self._apply_substitutions_optimized(truncated_name, applicable_subs)
            
            # Apply final string cleanup
            clean_name = self._apply_final_cleanup(substituted_name)
            
            # Convert to enum-safe name
            enum_name = cleanstr(clean_name)
            
            # Track name usage
            if enum_name in name_usage:
                name_usage[enum_name] += 1
            else:
                name_usage[enum_name] = 1
                
            item['processed_name'] = enum_name
            item['truncated_name'] = truncated_name
            item['substituted_name'] = substituted_name
            processed_items.append(item)
        
        # Handle duplicate names
        print("Resolving name conflicts...")
        processed_items = self._resolve_name_conflicts(processed_items, name_usage)
        
        return processed_items

    def _apply_smart_truncation(self, text: str) -> str:
        """Apply smart truncation logic"""
        # For now, return as-is - can implement truncation rules here
        return text

    def _apply_final_cleanup(self, text: str) -> str:
        """Apply final string cleanup"""
        if not text:
            return text
            
        # Remove extra whitespace and normalize
        result = ' '.join(text.split())
        
        # Remove common problematic characters
        result = result.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        
        return result

    def _resolve_name_conflicts(self, items, name_usage):
        """
        Resolve duplicate names by trying reversion or adding suffixes.
        """
        # Find duplicates
        duplicates = {name: count for name, count in name_usage.items() if count > 1}
        
        if not duplicates:
            return items
            
        print(f"Resolving {len(duplicates)} name conflicts...")
        
        # Group items by conflicting names
        conflict_groups = {}
        for item in items:
            name = item['processed_name']
            if name in duplicates:
                if name not in conflict_groups:
                    conflict_groups[name] = []
                conflict_groups[name].append(item)
        
        # Resolve each conflict group
        for conflict_name, conflict_items in conflict_groups.items():
            # Try reverting truncation first
            non_truncated_names = set()
            for item in conflict_items:
                original = item['original_name']
                # Re-process without truncation
                applicable_subs = self._find_applicable_substitutions(original, self._build_complete_substitution_dict())
                non_truncated = self._apply_substitutions_optimized(original, applicable_subs)
                clean_non_truncated = cleanstr(self._apply_final_cleanup(non_truncated))
                non_truncated_names.add(clean_non_truncated)
            
            # If reversion resolves conflicts, use it
            if len(non_truncated_names) == len(conflict_items):
                for i, item in enumerate(conflict_items):
                    original = item['original_name']
                    applicable_subs = self._find_applicable_substitutions(original, self._build_complete_substitution_dict())
                    non_truncated = self._apply_substitutions_optimized(original, applicable_subs)
                    item['processed_name'] = cleanstr(self._apply_final_cleanup(non_truncated))
            else:
                # Use suffix strategy
                for i, item in enumerate(conflict_items):
                    if i > 0:  # Keep first item as-is
                        item['processed_name'] = f"{conflict_name}_{i}"
        
        return items

async def main():
    """Main entry point for the enum generator"""
    print("Enum Generator for WDS Code Sets\n")
    DEFAULT_OUTPUT_PATH = Path(__file__).parent.parent / 'scratch' / 'enums' / 'wds'
    
    generator = EnumGenerator()
    await generator.generate_all_enums(output_dir=DEFAULT_OUTPUT_PATH)

    print("\nGeneration complete! All enums ready for use.")

if __name__ == "__main__":
    asyncio.run(main())
