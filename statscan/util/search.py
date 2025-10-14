"""Fuzzy search utilities for text matching.

Provides fuzzy string matching capabilities for finding geographic entities,
dimension members, and other text-based searches in Statistics Canada data.

Uses difflib for efficient fuzzy matching without external dependencies.
"""

from collections.abc import Callable
from difflib import SequenceMatcher, get_close_matches
from typing import TypeVar

T = TypeVar("T")


def fuzzy_match_score(query: str, target: str, case_sensitive: bool = False) -> float:
    """Calculate similarity score between two strings.

    Uses SequenceMatcher to compute a ratio between 0.0 (no match) and 1.0
    (perfect match). This is the same algorithm used by difflib.get_close_matches.

    Args:
        query: The search string to match.
        target: The target string to compare against.
        case_sensitive: Whether to perform case-sensitive matching.
            Defaults to False.

    Returns:
        Similarity score between 0.0 and 1.0.

    Examples:
        >>> fuzzy_match_score("Toronto", "Toronto")
        1.0
        >>> fuzzy_match_score("Toronto", "toronto")
        1.0
        >>> fuzzy_match_score("Toronto", "Toranto")
        0.9285714285714286
        >>> fuzzy_match_score("Saugeen", "Saugeen Shores")
        0.7272727272727273

    """
    if not case_sensitive:
        query = query.lower()
        target = target.lower()

    return SequenceMatcher(None, query, target).ratio()


def fuzzy_search(
    query: str,
    candidates: list[str],
    n: int = 5,
    cutoff: float = 0.6,
    case_sensitive: bool = False,
) -> list[str]:
    """Find the best fuzzy matches for a query string.

    Uses difflib.get_close_matches for efficient fuzzy matching.

    Args:
        query: The search string to match.
        candidates: List of strings to search through.
        n: Maximum number of matches to return. Defaults to 5.
        cutoff: Minimum similarity score (0.0 to 1.0) for matches.
            Defaults to 0.6.
        case_sensitive: Whether to perform case-sensitive matching.
            Defaults to False.

    Returns:
        List of matching strings, sorted by similarity (best first).

    Examples:
        >>> candidates = ["Toronto", "Montreal", "Vancouver", "Toronta"]
        >>> fuzzy_search("Toront", candidates, n=3)
        ['Toronto', 'Toronta']
        >>> fuzzy_search("Saugeen", ["Saugeen Shores", "Saugeen 29"], n=2)
        ['Saugeen Shores', 'Saugeen 29']

    """
    if not case_sensitive:
        # Create a mapping of lowercase to original
        lower_to_original = {s.lower(): s for s in candidates}
        search_candidates = list(lower_to_original.keys())
        query_lower = query.lower()

        matches = get_close_matches(query_lower, search_candidates, n=n, cutoff=cutoff)
        # Map back to original case
        return [lower_to_original[match] for match in matches]

    return get_close_matches(query, candidates, n=n, cutoff=cutoff)


def fuzzy_search_objects(  # noqa: PLR0913
    query: str,
    objects: list[T],
    key_func: Callable[[T], str],
    n: int = 5,
    cutoff: float = 0.6,
    case_sensitive: bool = False,
) -> list[tuple[T, float]]:
    """Find the best fuzzy matches for objects based on a key function.

    Searches through a list of objects by extracting a search key from each
    object and computing similarity scores.

    Args:
        query: The search string to match.
        objects: List of objects to search through.
        key_func: Function to extract the searchable string from each object.
        n: Maximum number of matches to return. Defaults to 5.
        cutoff: Minimum similarity score (0.0 to 1.0) for matches.
            Defaults to 0.6.
        case_sensitive: Whether to perform case-sensitive matching.
            Defaults to False.

    Returns:
        List of (object, score) tuples, sorted by score (best first).

    Examples:
        >>> from dataclasses import dataclass
        >>> @dataclass
        ... class City:
        ...     name: str
        ...     population: int
        >>> cities = [
        ...     City("Toronto", 2930000),
        ...     City("Montreal", 1780000),
        ...     City("Vancouver", 675000)
        ... ]
        >>> results = fuzzy_search_objects("Toront", cities, lambda c: c.name)
        >>> results[0][0].name
        'Toronto'
        >>> results[0][1]  # Score
        0.9230769230769231

    """
    # Build list of (object, key_string, score) tuples
    scored_objects = []
    for obj in objects:
        key_str = key_func(obj)
        score = fuzzy_match_score(query, key_str, case_sensitive)
        if score >= cutoff:
            scored_objects.append((obj, score))

    # Sort by score descending
    scored_objects.sort(key=lambda x: x[1], reverse=True)

    # Return top n matches
    return scored_objects[:n]


def find_best_match(
    query: str,
    candidates: list[str],
    cutoff: float = 0.6,
    case_sensitive: bool = False,
) -> str | None:
    """Find the single best fuzzy match for a query string.

    Convenience function that returns only the best match, or None if no
    match meets the cutoff threshold.

    Args:
        query: The search string to match.
        candidates: List of strings to search through.
        cutoff: Minimum similarity score (0.0 to 1.0) for matches.
            Defaults to 0.6.
        case_sensitive: Whether to perform case-sensitive matching.
            Defaults to False.

    Returns:
        The best matching string, or None if no match found.

    Examples:
        >>> candidates = ["Toronto", "Montreal", "Vancouver"]
        >>> find_best_match("Toront", candidates)
        'Toronto'
        >>> find_best_match("xyz", candidates)  # No good match
        None

    """
    matches = fuzzy_search(
        query, candidates, n=1, cutoff=cutoff, case_sensitive=case_sensitive
    )
    return matches[0] if matches else None


def contains_fuzzy(
    query: str,
    target: str,
    cutoff: float = 0.8,
    case_sensitive: bool = False,
) -> bool:
    """Check if query is fuzzily contained in target string.

    Useful for checking if a search term appears within a longer string,
    with tolerance for typos.

    Args:
        query: The search string to look for.
        target: The target string to search within.
        cutoff: Minimum similarity score (0.0 to 1.0) for matching.
            Defaults to 0.8 (stricter than other functions).
        case_sensitive: Whether to perform case-sensitive matching.
            Defaults to False.

    Returns:
        True if query is found in target with similarity >= cutoff.

    Examples:
        >>> contains_fuzzy("Saugeen", "Saugeen Shores")
        True
        >>> contains_fuzzy("Toronto", "Greater Toronto Area")
        True
        >>> contains_fuzzy("xyz", "abcdef")
        False

    """
    if not case_sensitive:
        query = query.lower()
        target = target.lower()

    # Try exact substring first
    if query in target:
        return True

    # Try fuzzy matching on words in target
    words = target.split()
    for word in words:
        if fuzzy_match_score(query, word, case_sensitive=True) >= cutoff:
            return True

    return False


def get_match_details(
    query: str,
    candidates: list[str],
    n: int = 5,
    cutoff: float = 0.6,
    case_sensitive: bool = False,
) -> list[tuple[str, float]]:
    """Find fuzzy matches with their similarity scores.

    Similar to fuzzy_search, but returns tuples of (match, score) for
    detailed analysis.

    Args:
        query: The search string to match.
        candidates: List of strings to search through.
        n: Maximum number of matches to return. Defaults to 5.
        cutoff: Minimum similarity score (0.0 to 1.0) for matches.
            Defaults to 0.6.
        case_sensitive: Whether to perform case-sensitive matching.
            Defaults to False.

    Returns:
        List of (match, score) tuples, sorted by score (best first).

    Examples:
        >>> candidates = ["Toronto", "Toronta", "Montreal"]
        >>> matches = get_match_details("Toront", candidates, n=2)
        >>> matches[0]
        ('Toronto', 0.9230769230769231)
        >>> matches[1]
        ('Toronta', 0.9230769230769231)

    """
    # Get matches
    matches = fuzzy_search(
        query, candidates, n=n, cutoff=cutoff, case_sensitive=case_sensitive
    )

    # Calculate scores for matches
    return [
        (match, fuzzy_match_score(query, match, case_sensitive)) for match in matches
    ]
