import re
from typing import Optional
import logging

from tools.abbreviations import DEFAULT_ABBREVIATIONS

# Assume these runtime/dev dependencies exist in the environment; allow ImportError to surface
from tqdm import tqdm
from nltk.corpus import wordnet as wn  # type: ignore[import-untyped]
import nltk  # type: ignore[import-untyped]
import pyinflect  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


class SubstitutionEngine:
    # Class-level cache for shared substitution lookups
    _global_lookup_cache: dict[tuple, dict[str, str]] = {}

    def __init__(
        self,
        abbreviation_map: dict[str, list[str]] = DEFAULT_ABBREVIATIONS,
        include_inflections: bool = True,  # Enabled by default (optimized with caching)
        include_deriv_rel: bool = True,  # Enabled by default (optimized with caching)
    ):
        self.include_inflections = include_inflections
        self.include_deriv_rel = include_deriv_rel

        # Performance caches for morphological analysis
        self._inflection_cache: dict[str, set[str]] = {}
        self._derivation_cache: dict[str, set[str]] = {}
        self._variant_cache: dict[tuple, set[str]] = {}

        self.abbreviation_map = abbreviation_map  # Triggers setter

    @property
    def abbreviation_map(self) -> dict[str, list[str]]:
        return self._abbreviation_map

    @abbreviation_map.setter
    def abbreviation_map(self, new_map: dict[str, list[str]]):
        self._abbreviation_map = new_map
        logger.debug(f"Loaded {len(self.abbreviation_map)} abbreviation mappings")
        # Rebuild optimized lookup when map changes
        self.build_lookup()

    def build_lookup(self):
        # Create cache key from abbreviation map and settings
        abbrev_hash = hash(
            frozenset((k, tuple(v)) for k, v in self.abbreviation_map.items())
        )
        cache_key = (abbrev_hash, self.include_inflections, self.include_deriv_rel)

        # Check if we already built this exact lookup
        if cache_key in self._global_lookup_cache:
            logger.info("Using cached substitution lookup table")
            self._preprocessed_substitutions = self._global_lookup_cache[cache_key]
            return

        logger.info("Building new substitution lookup table...")
        self._preprocessed_substitutions = self._build_optimized_substitution_lookup(
            abbreviation_map=self.abbreviation_map,
            gen_inflections=self.include_inflections,
            gen_deriv_rel=self.include_deriv_rel,
        )

        # Cache the result for future instances
        if len(self._global_lookup_cache) < 10:  # Limit cache size
            self._global_lookup_cache[cache_key] = self._preprocessed_substitutions

        logger.info(
            f"✓ Built and cached {len(self._preprocessed_substitutions)} substitution patterns"
        )

    @property
    def preprocessed_substitutions(self) -> dict[str, str]:
        return self._preprocessed_substitutions

    @staticmethod
    def _build_optimized_substitution_lookup(
        abbreviation_map: dict[str, list[str]],
        gen_inflections: bool,
        gen_deriv_rel: bool,
    ) -> dict[str, str]:
        """
        Build an optimized lookup table for fast substitution.
        Ordered by: containment relationships first, then length (longest first).
        """
        logger.info(
            f"Building substitution lookup with inflections={gen_inflections}, derivations={gen_deriv_rel}"
        )

        # Collect all term -> abbreviation mappings
        term_abbrev_pairs = []

        # Create progress bar for processing abbreviations
        abbrev_items = list(abbreviation_map.items())
        progress_desc = "Processing abbreviations"
        abbrev_iter = tqdm(abbrev_items, desc=progress_desc, unit="abbrev")

        for abbrev, possible_matches in abbrev_iter:
            for full_term in possible_matches:
                # Always add the original term
                term_abbrev_pairs.append((full_term.lower(), abbrev))

                # Generate morphological variants for single words when requested
                if (gen_inflections or gen_deriv_rel) and len(full_term.split()) == 1:
                    try:
                        variants = SubstitutionEngine._generate_variants_static(
                            full_term,
                            include_inflections=gen_inflections,
                            include_deriv_rel=gen_deriv_rel,
                        )
                        for v in variants:
                            if v.lower() != full_term.lower():  # Avoid duplicates
                                term_abbrev_pairs.append((v.lower(), abbrev))
                    except Exception as e:
                        if (
                            gen_inflections or gen_deriv_rel
                        ):  # Only warn if we're actually trying variants
                            logger.debug(
                                f"Failed to generate variants for '{full_term}': {e}"
                            )

        # Remove duplicates while preserving order (first occurrence wins)
        logger.info(
            f"Removing duplicates from {len(term_abbrev_pairs)} term-abbreviation pairs..."
        )
        seen = set()
        unique_pairs = []

        pairs_iter = tqdm(term_abbrev_pairs, desc="Deduplicating", unit="pair")
        for term, abbrev in pairs_iter:
            if term not in seen:
                seen.add(term)
                unique_pairs.append((term, abbrev))

        # Sort by length (longest first) for better specificity
        logger.info("Sorting substitution patterns by length...")
        unique_pairs.sort(key=lambda pair: -len(pair[0]))

        logger.info(
            f"✓ Built {len(unique_pairs)} unique substitution patterns from {len(abbreviation_map)} abbreviations"
        )
        return dict(unique_pairs)

    @staticmethod
    def get_all_inflections(word: str) -> dict[str, tuple[str]]:
        """
        Generate all inflected forms of a given word using pyinflect.
        Returns a set of inflected forms.
        """
        return pyinflect.getAllInflections(word)

    def generate_inflections(self, word: str) -> set[str]:
        """Generate inflections with caching for performance."""
        if word in self._inflection_cache:
            return self._inflection_cache[word]

        inflections: set = set()
        try:
            for forms in self.get_all_inflections(word).values():
                inflections.update(forms)
        except Exception:
            # Fallback to original word if inflection fails
            inflections = {word}

        self._inflection_cache[word] = inflections
        return inflections

    @staticmethod
    def get_all_deriv_rel_forms(word: str) -> set:
        # Ensure wordnet data is available; raise if not
        try:
            nltk.data.find("corpora/wordnet")
        except LookupError:
            nltk.download("wordnet", quiet=True)
            nltk.download("omw-1.4", quiet=True)

        derivations: set = set()
        for syn in wn.synsets(word):
            for lemma in syn.lemmas():
                if not lemma.name() == word:
                    continue
                derivations.add(lemma)
                derivations.update(lemma.derivationally_related_forms())
        return derivations

    def generate_deriv_rel_forms(self, word: str) -> set[str]:
        """Generate derivational relations with caching for performance."""
        if word in self._derivation_cache:
            return self._derivation_cache[word]

        try:
            lemmas = self.get_all_deriv_rel_forms(word)
            derivations = set(lemma.name() for lemma in lemmas)
        except Exception:
            # Fallback to original word if derivation fails
            derivations = {word}

        self._derivation_cache[word] = derivations
        return derivations

    def generate_variants(
        self,
        word: str,
        include_inflections: bool = True,
        include_deriv_rel: bool = True,
    ) -> set[str]:
        """Generate variants with caching for performance."""
        cache_key = (word, include_inflections, include_deriv_rel)
        if cache_key in self._variant_cache:
            return self._variant_cache[cache_key]

        variants: set[str] = set([word])

        if include_deriv_rel:
            variants.update(self.generate_deriv_rel_forms(word=word))

        if include_inflections:
            # Process in batches to avoid exponential growth
            original_variants = variants.copy()
            for v in original_variants:
                variants.update(self.generate_inflections(word=v))

        self._variant_cache[cache_key] = variants
        return variants

    @staticmethod
    def _generate_variants_static(
        word: str,
        include_inflections: bool = True,
        include_deriv_rel: bool = True,
    ) -> set[str]:
        """Static variant generation for use during class construction."""
        variants: set[str] = set([word])

        # Reasonable limits for variant generation quality vs. scope
        MAX_VARIANTS = 50  # Balance between coverage and efficiency

        if include_deriv_rel and len(variants) < MAX_VARIANTS:
            try:
                lemmas = SubstitutionEngine.get_all_deriv_rel_forms(word)
                new_variants = set(lemma.name().replace("_", " ") for lemma in lemmas)
                # Limit the number of variants we add
                variants.update(list(new_variants)[: MAX_VARIANTS - len(variants)])
            except Exception:
                pass  # Keep original word if derivation fails

        if include_inflections and len(variants) < MAX_VARIANTS:
            original_variants = list(variants)[
                :10
            ]  # Only process first 10 to avoid explosion
            for v in original_variants:
                if len(variants) >= MAX_VARIANTS:
                    break
                try:
                    inflections = SubstitutionEngine.get_all_inflections(v)
                    for forms in inflections.values():
                        if len(variants) >= MAX_VARIANTS:
                            break
                        variants.update(
                            list(forms)[:5]
                        )  # Limit forms per inflection type
                except Exception:
                    pass  # Keep original variants if inflection fails

        return variants

    def substitute(
        self,
        text: str,
        truncate: bool = True,
        truncation_patterns: Optional[list[str]] = None,
    ) -> str:
        """
        Apply optimized substitutions using pre-computed lookup table with caching.
        Uses class-level caching for maximum performance across multiple instances.
        """
        if truncate:
            text = self.truncate(text, truncation_patterns=truncation_patterns)

        # Work with a copy for case-insensitive matching
        result = text

        # Cache compiled patterns for better performance
        if not hasattr(self, "_compiled_patterns"):
            self._compiled_patterns: dict[str, re.Pattern] = {}

        # Apply substitutions in optimized order (limited to prevent excessive processing)
        substitution_count = 0
        MAX_SUBSTITUTIONS = 10  # Reasonable limit to maintain readability

        for full_term, abbrev in self.preprocessed_substitutions.items():
            if substitution_count >= MAX_SUBSTITUTIONS:
                break

            # Use cached compiled pattern
            if full_term not in self._compiled_patterns:
                self._compiled_patterns[full_term] = re.compile(
                    r"\b" + re.escape(full_term) + r"\b", re.IGNORECASE
                )

            pattern = self._compiled_patterns[full_term]
            matches = list(pattern.finditer(result))

            if matches:
                substitution_count += len(matches)
                # Replace from right to left to preserve positions
                for match in reversed(matches):
                    start_pos = match.start()
                    end_pos = match.end()
                    original_text = result[start_pos:end_pos]

                    # Preserve case pattern of original text
                    if original_text.isupper():
                        abbrev_with_case = abbrev.upper()
                    elif original_text[0].isupper():
                        abbrev_with_case = abbrev.capitalize()
                    else:
                        abbrev_with_case = abbrev.lower()

                    # Replace in result
                    result = result[:start_pos] + abbrev_with_case + result[end_pos:]

        return result

    @staticmethod
    def truncate(s: str, truncation_patterns: Optional[list[str]] = None) -> str:
        """
        Truncate a string at the first occurrence of any specified pattern.
        Args:
            s: The input string to truncate.
            truncation_patterns: List of patterns to look for truncation points.
                                 Defaults to common patterns if None.
        Returns:
            The truncated string, or the original string if no patterns found.
        """
        if not s:
            return s

        if truncation_patterns is None:
            truncation_patterns = [" - ", " including ", ", including ", " (", " ["]

        s_lower = s.lower()
        for pattern in truncation_patterns:
            pattern_lower = pattern.lower()
            pos = s_lower.find(pattern_lower)
            if pos != -1:
                return s[:pos].strip()

        return s

    @staticmethod
    def snake_to_camel(s: str) -> str:
        """
        Convert a snake_case string to CamelCase.
        Args:
            s (str): The input snake_case string.
        Returns:
            str: The converted CamelCase string.
        """
        components = s.split("_")
        return "".join(x.title() for x in components if x)

    @staticmethod
    def camel_to_snake(s: str) -> str:
        """
        Convert a CamelCase string to snake_case.
        Args:
            s (str): The input CamelCase string.
        Returns:
            str: The converted snake_case string.
        """
        s_snake = re.sub(r"(?<!^)(?=[A-Z])", "_", s).lower()
        return s_snake

    @staticmethod
    def camel_to_title(s: str) -> str:
        """
        Convert a titleCaseString to TitleCaseString (first letter capitalized).
        """
        return s[0].upper() + (s[1:] if len(s) > 1 else "")

    @staticmethod
    def sub_chars(
        s: str, sub_chars: set[str], replacement: Optional[str] = None
    ) -> str:
        """
        Substitute or remove characters in a string.
        Args:
            s (str): The input string.
            sub_chars (set[str]): A set of characters to be substituted or removed.
            replacement (Optional[str]): The string to replace each character in sub_chars with.
                                        If None, the characters are removed.
        Returns:
            str: The modified string with specified characters substituted or removed.
        Raises:
            ValueError: If sub_chars contains non-single-character strings.
        """
        for c in sub_chars:
            if not isinstance(c, str) or len(c) != 1:
                raise ValueError(
                    f"sub_chars must be a set of single-character strings, got {c} of type {type(c)}"
                )
        replacement = replacement or ""
        return re.sub(f"[{re.escape(''.join(sub_chars))}]", replacement, s)
