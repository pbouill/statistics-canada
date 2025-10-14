"""HTTP response caching for WDS API client.

This module provides SQLite-based caching for HTTP responses to minimize
redundant API calls. The cache stores response status codes, headers, and
content bytes, keyed by request method, URL, and parameters.

The cache can operate in two modes:
1. Persistent: Cache stored in a specified file path
2. Temporary: Cache stored in a temp file (deleted on exit)

Example:
    >>> from statscan.wds.cache import ResponseCache
    >>> cache = ResponseCache(cache_path="wds_cache.db")
    >>>
    >>> # Store a response
    >>> cache.put(method="GET", url="https://api.example.com/data",
    ...          response_data=response.content, status_code=200,
    ...          headers=dict(response.headers))
    >>>
    >>> # Retrieve cached response
    >>> cached = cache.get(method="GET", url="https://api.example.com/data")
    >>> if cached:
    ...     print(f"Cache hit! Status: {cached['status_code']}")

"""
import hashlib
import json
import logging
import pickle
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


class ResponseCache:
    """SQLite-based cache for HTTP responses.

    This cache stores HTTP response data (status code, headers, content bytes)
    to avoid redundant API calls. Responses are keyed by a hash of the request
    method, URL, and any parameters.

    Attributes:
        cache_path: Path to SQLite database file (or None for temp file)
        enabled: Whether caching is active

    """

    def __init__(
        self,
        cache_path: str | Path | None = None,
        enabled: bool = True,
    ):
        """Initialize the response cache.

        Args:
            cache_path: Path to SQLite cache file. If None, uses a temp file.
                Set to False to disable caching.
            enabled: Whether to enable caching. Defaults to True.

        """
        self.enabled = enabled and cache_path is not False

        if not self.enabled:
            self.cache_path = None
            self._conn = None
            return

        # Set up cache file path
        if cache_path is None:
            # Create temp file for cache
            # Use delete=False so we can control when it's deleted
            temp_file = tempfile.NamedTemporaryFile(
                suffix=".db",
                delete=False,
                mode='wb'  # Binary mode for SQLite
            )
            self.cache_path = Path(temp_file.name)
            # Close the file handle so SQLite can open it
            temp_file.close()
            # Track that this is a temp file (for cleanup)
            self._is_temp = True
            logger.info(f"Using temporary cache: {self.cache_path}")
        else:
            self.cache_path = Path(cache_path)
            self._is_temp = False
            logger.info(f"Using persistent cache: {self.cache_path}")

        # Initialize database connection
        self._conn = sqlite3.connect(
            str(self.cache_path),
            check_same_thread=False  # Allow use from async contexts
        )
        self._initialize_cache()

    def _initialize_cache(self) -> None:
        """Create cache tables and indexes if they don't exist."""
        if not self._conn:
            return

        cursor = self._conn.cursor()

        # Create response cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS response_cache (
                cache_key TEXT PRIMARY KEY,
                method TEXT NOT NULL,
                url TEXT NOT NULL,
                params TEXT,
                status_code INTEGER NOT NULL,
                headers TEXT NOT NULL,
                content BLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                content_length INTEGER
            )
        """)

        # Create indexes for efficient lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_url
            ON response_cache(url, method)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_created
            ON response_cache(created_at)
        """)

        self._conn.commit()
        logger.debug("Cache tables initialized")

    def _generate_cache_key(
        self,
        method: str,
        url: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> str:
        """Generate a unique cache key for a request.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            params: Query parameters (optional)
            data: Request body data (optional)

        Returns:
            MD5 hash of the request signature

        """
        # Sort params and data to ensure consistent keys
        params_str = json.dumps(params or {}, sort_keys=True)
        data_str = json.dumps(data or {}, sort_keys=True)

        # Create signature string
        signature = f"{method.upper()}:{url}:{params_str}:{data_str}"

        # Generate MD5 hash
        return hashlib.md5(signature.encode()).hexdigest()  # noqa: S324

    def get(
        self,
        method: str,
        url: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Retrieve a cached response.

        Args:
            method: HTTP method used for the request
            url: Request URL
            params: Query parameters (optional)
            data: Request body data (optional)

        Returns:
            Dictionary with cached response data:
                - status_code: HTTP status code
                - headers: Response headers (dict)
                - content: Response content (bytes)
                - cached_at: When the response was cached
                - access_count: Number of times accessed
            Returns None if not found in cache.

        """
        if not self.enabled or not self._conn:
            return None

        cache_key = self._generate_cache_key(method, url, params, data)

        try:
            cursor = self._conn.cursor()
            cursor.execute("""
                SELECT status_code, headers, content, created_at, access_count
                FROM response_cache
                WHERE cache_key = ?
            """, (cache_key,))

            row = cursor.fetchone()
            if row is None:
                logger.debug(f"Cache miss: {method} {url}")
                return None

            status_code, headers_json, content, created_at, access_count = row

            # Update access statistics
            cursor.execute("""
                UPDATE response_cache
                SET accessed_at = CURRENT_TIMESTAMP,
                    access_count = access_count + 1
                WHERE cache_key = ?
            """, (cache_key,))
            self._conn.commit()

            logger.info(
                f"Cache hit: {method} {url} "
                f"(cached {created_at}, accessed {access_count + 1} times)"
            )

            return {
                "status_code": status_code,
                "headers": json.loads(headers_json),
                "content": content,
                "cached_at": created_at,
                "access_count": access_count + 1,
            }

        except sqlite3.Error as e:
            logger.error(f"Cache retrieval error: {e}")
            return None

    def put(  # noqa: PLR0913
        self,
        method: str,
        url: str,
        response_data: bytes,
        status_code: int,
        headers: dict[str, str],
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Store a response in the cache.

        Args:
            method: HTTP method used for the request
            url: Request URL
            response_data: Response content bytes
            status_code: HTTP status code
            headers: Response headers
            params: Query parameters (optional)
            data: Request body data (optional)

        """
        if not self.enabled or not self._conn:
            return

        cache_key = self._generate_cache_key(method, url, params, data)
        headers_json = json.dumps(dict(headers))
        params_json = json.dumps(params or {})

        try:
            cursor = self._conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO response_cache
                (cache_key, method, url, params, status_code, headers,
                 content, content_length, created_at, accessed_at, access_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0)
            """, (
                cache_key,
                method.upper(),
                url,
                params_json,
                status_code,
                headers_json,
                response_data,
                len(response_data),
            ))
            self._conn.commit()

            logger.info(
                f"Cached response: {method} {url} "
                f"(status: {status_code}, size: {len(response_data)} bytes)"
            )

        except sqlite3.Error as e:
            logger.error(f"Cache storage error: {e}")

    def clear(self) -> int:
        """Delete all cached responses.

        Returns:
            Number of cache entries removed.

        """
        if not self.enabled or not self._conn:
            return 0

        try:
            cursor = self._conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM response_cache")
            count = cursor.fetchone()[0]

            cursor.execute("DELETE FROM response_cache")
            self._conn.commit()

            logger.info(f"Cleared {count} cached responses")
            return count

        except sqlite3.Error as e:
            logger.error(f"Cache clear error: {e}")
            return 0

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics:
                - total_entries: Number of cached responses
                - total_accesses: Total cache hits across all entries
                - cache_size_mb: Total size of cached content in MB
                - oldest_entry: Timestamp of oldest cached response
                - newest_entry: Timestamp of newest cached response
                - most_accessed_url: URL with most cache hits

        """
        if not self.enabled or not self._conn:
            return {
                "total_entries": 0,
                "total_accesses": 0,
                "cache_size_mb": 0.0,
                "oldest_entry": None,
                "newest_entry": None,
                "most_accessed_url": None,
            }

        try:
            cursor = self._conn.cursor()

            # Get basic stats
            cursor.execute("""
                SELECT
                    COUNT(*) as total_entries,
                    SUM(access_count) as total_accesses,
                    SUM(content_length) as total_bytes,
                    MIN(created_at) as oldest,
                    MAX(created_at) as newest
                FROM response_cache
            """)
            row = cursor.fetchone()
            total_entries, total_accesses, total_bytes, oldest, newest = row

            # Get most accessed URL
            cursor.execute("""
                SELECT url, MAX(access_count)
                FROM response_cache
                GROUP BY url
                ORDER BY MAX(access_count) DESC
                LIMIT 1
            """)
            most_accessed = cursor.fetchone()
            most_accessed_url = most_accessed[0] if most_accessed else None

            return {
                "total_entries": total_entries or 0,
                "total_accesses": total_accesses or 0,
                "cache_size_mb": (total_bytes or 0) / (1024 * 1024),
                "oldest_entry": oldest,
                "newest_entry": newest,
                "most_accessed_url": most_accessed_url,
            }

        except sqlite3.Error as e:
            logger.error(f"Cache stats error: {e}")
            return {
                "total_entries": 0,
                "total_accesses": 0,
                "cache_size_mb": 0.0,
                "oldest_entry": None,
                "newest_entry": None,
                "most_accessed_url": None,
            }

    def list_cached_urls(self) -> list[dict[str, Any]]:
        """List all cached URLs with metadata.

        Returns:
            List of cache entries, each containing:
                - method: HTTP method
                - url: Request URL
                - status_code: Response status code
                - content_length: Size of cached content
                - created_at: When the entry was cached
                - accessed_at: Last access timestamp
                - access_count: Number of times accessed

        """
        if not self.enabled or not self._conn:
            return []

        try:
            cursor = self._conn.cursor()
            cursor.execute("""
                SELECT method, url, status_code, content_length,
                       created_at, accessed_at, access_count
                FROM response_cache
                ORDER BY created_at DESC
            """)

            return [
                {
                    "method": row[0],
                    "url": row[1],
                    "status_code": row[2],
                    "content_length": row[3],
                    "created_at": row[4],
                    "accessed_at": row[5],
                    "access_count": row[6],
                }
                for row in cursor.fetchall()
            ]

        except sqlite3.Error as e:
            logger.error(f"Cache list error: {e}")
            return []

    def close(self) -> None:
        """Close the cache connection and clean up temp files.

        Note:
            This is typically only called on garbage collection (__del__).
            The cache is designed to persist across multiple client instances
            for better performance.

        """
        if self._conn:
            try:
                self._conn.close()
                logger.debug("Cache connection closed")
            except Exception as e:
                logger.warning(f"Error closing cache connection: {e}")
            finally:
                self._conn = None

        # Clean up temp file if this was a temporary cache
        if hasattr(self, '_is_temp') and self._is_temp and self.cache_path:
            try:
                if self.cache_path.exists():
                    self.cache_path.unlink()
                    logger.debug(f"Cleaned up temp cache: {self.cache_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp cache: {e}")

    def __del__(self):
        """Cleanup on garbage collection - close connection and remove temp files."""
        self.close()


class DataFrameCache:
    """SQLite-based cache for Statistics Canada DataFrames.

    Caches downloaded DataFrames to avoid repeated API calls. Uses SQLite for
    efficient storage and retrieval. Supports both persistent and temporary caches.

    Attributes:
        cache_path: Path to SQLite cache file (None for temp file)
        conn: SQLite database connection
        enabled: Whether caching is enabled

    """

    def __init__(self, cache_path: str | Path | None = None, enabled: bool = True):
        """Initialize the DataFrame cache.

        Args:
            cache_path: Path to SQLite cache file. If None, uses a temp file.
            enabled: Whether to enable caching. Defaults to True.

        """
        self.enabled = enabled
        self.cache_path = cache_path
        self.conn: sqlite3.Connection | None = None
        self._temp_file: tempfile._TemporaryFileWrapper[bytes] | None = None

        if self.enabled:
            self._initialize_cache()

    def _initialize_cache(self) -> None:
        """Initialize the SQLite cache database."""
        if self.cache_path is None:
            # Create temp file
            self._temp_file = tempfile.NamedTemporaryFile(
                suffix=".db", delete=False, prefix="statscan_cache_"
            )
            db_path = self._temp_file.name
            logger.info(f"Using temporary cache: {db_path}")
        else:
            db_path = str(Path(self.cache_path).expanduser().resolve())
            # Ensure directory exists
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"Using persistent cache: {db_path}")

        # Connect to database
        self.conn = sqlite3.connect(db_path, check_same_thread=False)

        # Create cache table
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS dataframe_cache (
                cache_key TEXT PRIMARY KEY,
                product_id INTEGER NOT NULL,
                language TEXT NOT NULL,
                filters TEXT,
                dataframe BLOB NOT NULL,
                created_at TIMESTAMP NOT NULL,
                accessed_at TIMESTAMP NOT NULL,
                access_count INTEGER DEFAULT 1,
                row_count INTEGER,
                column_count INTEGER
            )
            """
        )

        # Create index for faster lookups
        self.conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_product_language
            ON dataframe_cache(product_id, language)
            """
        )

        self.conn.commit()
        logger.info("Cache initialized successfully")

    def _generate_cache_key(
        self, product_id: int, language: str, filters: dict[str, str]
    ) -> str:
        """Generate a unique cache key for a request.

        Args:
            product_id: The product ID
            language: Response language
            filters: Filter parameters

        Returns:
            MD5 hash of the request parameters

        """
        # Sort filters for consistent hashing
        filter_str = str(sorted(filters.items())) if filters else ""
        key_str = f"{product_id}:{language}:{filter_str}"
        return hashlib.md5(key_str.encode()).hexdigest()  # noqa: S324

    def get(
        self, product_id: int, language: str, filters: dict[str, str] | None = None
    ) -> pd.DataFrame | None:
        """Retrieve DataFrame from cache.

        Args:
            product_id: The product ID
            language: Response language
            filters: Filter parameters applied to the DataFrame

        Returns:
            Cached DataFrame if found, None otherwise

        """
        if not self.enabled or self.conn is None:
            return None

        filters = filters or {}
        cache_key = self._generate_cache_key(product_id, language, filters)

        try:
            cursor = self.conn.execute(
                """
                SELECT dataframe, access_count
                FROM dataframe_cache
                WHERE cache_key = ?
                """,
                (cache_key,),
            )

            row = cursor.fetchone()
            if row is None:
                logger.debug(f"Cache MISS: {cache_key}")
                return None

            # Deserialize DataFrame
            df_bytes, access_count = row
            df = pickle.loads(df_bytes)  # noqa: S301

            # Update access statistics
            self.conn.execute(
                """
                UPDATE dataframe_cache
                SET accessed_at = ?, access_count = ?
                WHERE cache_key = ?
                """,
                (datetime.now(), access_count + 1, cache_key),
            )
            self.conn.commit()

            logger.info(
                f"Cache HIT: {cache_key} (accessed {access_count + 1} times)"
            )
            return df

        except Exception as e:
            logger.warning(f"Cache retrieval error: {e}")
            return None

    def put(
        self,
        product_id: int,
        language: str,
        df: pd.DataFrame,
        filters: dict[str, str] | None = None,
    ) -> None:
        """Store DataFrame in cache.

        Args:
            product_id: The product ID
            language: Response language
            df: DataFrame to cache
            filters: Filter parameters applied to the DataFrame

        """
        if not self.enabled or self.conn is None:
            return

        filters = filters or {}
        cache_key = self._generate_cache_key(product_id, language, filters)

        try:
            # Serialize DataFrame
            df_bytes = pickle.dumps(df, protocol=pickle.HIGHEST_PROTOCOL)

            # Store in cache
            self.conn.execute(
                """
                INSERT OR REPLACE INTO dataframe_cache
                (cache_key, product_id, language, filters, dataframe,
                 created_at, accessed_at, access_count, row_count, column_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (
                    cache_key,
                    product_id,
                    language,
                    str(filters),
                    df_bytes,
                    datetime.now(),
                    datetime.now(),
                    len(df),
                    len(df.columns),
                ),
            )
            self.conn.commit()

            logger.info(
                f"Cache STORE: {cache_key} ({len(df)} rows, {len(df.columns)} cols)"
            )

        except Exception as e:
            logger.warning(f"Cache storage error: {e}")

    def clear(self) -> int:
        """Clear all cached DataFrames.

        Returns:
            Number of cache entries deleted

        """
        if not self.enabled or self.conn is None:
            return 0

        cursor = self.conn.execute("SELECT COUNT(*) FROM dataframe_cache")
        count = cursor.fetchone()[0]

        self.conn.execute("DELETE FROM dataframe_cache")
        self.conn.commit()

        logger.info(f"Cache cleared: {count} entries deleted")
        return count

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics

        """
        if not self.enabled or self.conn is None:
            return {"enabled": False}

        cursor = self.conn.execute(
            """
            SELECT
                COUNT(*) as total_entries,
                SUM(access_count) as total_accesses,
                SUM(row_count) as total_rows,
                AVG(access_count) as avg_accesses,
                MAX(accessed_at) as last_access
            FROM dataframe_cache
            """
        )

        row = cursor.fetchone()
        total, accesses, rows, avg_accesses, last_access = row

        # Get cache file size
        cache_size = 0
        if self.cache_path:
            cache_size = Path(self.cache_path).stat().st_size
        elif self._temp_file:
            cache_size = Path(self._temp_file.name).stat().st_size

        return {
            "enabled": True,
            "cache_path": str(self.cache_path)
            if self.cache_path
            else self._temp_file.name if self._temp_file else "unknown",
            "total_entries": total or 0,
            "total_accesses": accesses or 0,
            "total_rows_cached": rows or 0,
            "avg_accesses_per_entry": float(avg_accesses) if avg_accesses else 0.0,
            "last_access": last_access,
            "cache_size_bytes": cache_size,
            "cache_size_mb": round(cache_size / (1024 * 1024), 2),
        }

    def list_cached_products(self) -> list[dict[str, Any]]:
        """List all cached products.

        Returns:
            List of dictionaries with cache entry information

        """
        if not self.enabled or self.conn is None:
            return []

        cursor = self.conn.execute(
            """
            SELECT
                product_id,
                language,
                filters,
                created_at,
                accessed_at,
                access_count,
                row_count,
                column_count
            FROM dataframe_cache
            ORDER BY accessed_at DESC
            """
        )

        results = []
        for row in cursor.fetchall():
            results.append(
                {
                    "product_id": row[0],
                    "language": row[1],
                    "filters": row[2],
                    "created_at": row[3],
                    "accessed_at": row[4],
                    "access_count": row[5],
                    "row_count": row[6],
                    "column_count": row[7],
                }
            )

        return results

    def close(self) -> None:
        """Close the cache database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Cache connection closed")

    def __enter__(self) -> DataFrameCache:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()

    def __del__(self) -> None:
        """Cleanup on deletion."""
        self.close()
