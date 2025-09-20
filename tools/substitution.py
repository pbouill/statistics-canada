import re
from typing import Optional
import logging

from nltk.corpus import wordnet as wn  # type: ignore[import-untyped]
from nltk.corpus.reader.wordnet import Lemma, Synset  # type: ignore[import-untyped]
import pyinflect  # type: ignore[import-untyped]

from tools.abbreviations import DEFAULT_ABBREVIATIONS

try:
    import nltk  # type: ignore[import-untyped]
    # Only download NLTK data if not already present
    try:
        nltk.data.find('corpora/wordnet')
    except LookupError:
        nltk.download('wordnet', quiet=True)
        nltk.download('omw-1.4', quiet=True)
except:
    pass

logger = logging.getLogger(__name__)


class SubstitutionEngine:
    def __init__(
        self, 
        abbreviation_map: dict[str, list[str]] = DEFAULT_ABBREVIATIONS,
        include_inflections: bool = True,
        include_deriv_rel: bool = True,
    ):
        self.include_inflections = include_inflections
        self.include_deriv_rel = include_deriv_rel
        
        # Performance caches - now enabled by default
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
        self._preprocessed_substitutions = self._build_optimized_substitution_lookup(
            abbreviation_map=self.abbreviation_map,
            gen_inflections=self.include_inflections,
            gen_deriv_rel=self.include_deriv_rel
        )
        logger.debug(f"Built {len(self._preprocessed_substitutions)} substitution patterns")

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
        # Collect all term -> abbreviation mappings
        term_abbrev_pairs = []
        for abbrev, possible_matches in abbreviation_map.items():
            for full_term in possible_matches:
                if len(full_term.split()) > 1:  # is a phrase or compound term, no need find variants
                    term_abbrev_pairs.append((full_term.lower(), abbrev))
                    continue
                for v in SubstitutionEngine._generate_variants_static(
                    full_term,
                    include_inflections=gen_inflections,
                    include_deriv_rel=gen_deriv_rel
                ):
                    term_abbrev_pairs.append((v.lower(), abbrev))


        # Sort by intelligent hierarchy:
        # 1. Terms that contain other terms should be processed first
        # 2. Then by length (longest first) for better specificity
        def sort_key(pair):
            term, abbrev = pair
            # Optimized: Just sort by length (descending) for better performance
            # Containment checking is expensive and length-based sorting captures most cases
            return -len(term)

        term_abbrev_pairs.sort(key=sort_key)

        # Build the lookup dictionary
        return dict(term_abbrev_pairs)

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
    def get_all_deriv_rel_forms(word: str) -> set[Lemma]:
        syn: Synset
        lemma: Lemma
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
        
        if include_deriv_rel:
            try:
                lemmas = SubstitutionEngine.get_all_deriv_rel_forms(word)
                variants.update(lemma.name() for lemma in lemmas)
            except Exception:
                pass  # Keep original word if derivation fails
        
        if include_inflections:
            original_variants = variants.copy()
            for v in original_variants:
                try:
                    for forms in SubstitutionEngine.get_all_inflections(v).values():
                        variants.update(forms)
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
        Apply optimized substitutions using pre-computed lookup table.
        Much faster than the old hierarchical approach.
        """
        if truncate:
            text = self.truncate(text, truncation_patterns=truncation_patterns)

        # Work with a copy for case-insensitive matching
        result = text

        # Apply substitutions in optimized order
        for full_term, abbrev in self.preprocessed_substitutions.items():
            # Use case-insensitive search
            pattern = r"\b" + re.escape(full_term) + r"\b"
            matches = list(re.finditer(pattern, result, re.IGNORECASE))
            if matches:
                # Replace from right to left to preserve positions
                for match in reversed(matches):
                    start_pos = match.start()
                    end_pos = match.end()
                    original_text = result[start_pos:end_pos]

                    # Preserve case pattern of original text
                    if original_text.isupper():
                        # All uppercase -> abbreviation in uppercase
                        abbrev_with_case = abbrev.upper()
                    elif original_text[0].isupper():
                        # First letter uppercase -> abbreviation capitalized
                        abbrev_with_case = abbrev.capitalize()
                    else:
                        # All lowercase -> abbreviation in lowercase
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
        components = s.split('_')
        return ''.join(x.title() for x in components if x)
    
    @staticmethod
    def camel_to_snake(s: str) -> str:
        """
        Convert a CamelCase string to snake_case.
        Args:
            s (str): The input CamelCase string.
        Returns:
            str: The converted snake_case string.
        """
        s_snake = re.sub(r'(?<!^)(?=[A-Z])', '_', s).lower()
        return s_snake
    
    @staticmethod
    def camel_to_title(s: str) -> str:
        """
        Convert a titleCaseString to TitleCaseString (first letter capitalized).
        """
        return s[0].upper() + (s[1:] if len(s) > 1 else "")
    
    @staticmethod
    def sub_chars(s: str, sub_chars: set[str], replacement: Optional[str] = None) -> str:
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
