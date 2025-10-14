"""Example: HTTP Response Caching for Performance.

This example demonstrates the built-in HTTP response caching feature.
All API calls are automatically cached at the HTTP level for significant
performance improvements on repeated requests.

Key benefits:
- Transparent: Works automatically without code changes
- Universal: Benefits all API methods (DataFrame, metadata, geographic queries)
- Persistent: Cache survives across program runs
- Smart: Caches based on request method, URL, and parameters
- Manageable: Clear cache, view stats, list cached responses

Run this example twice to see the dramatic speed difference!
"""
import asyncio
import time
from pathlib import Path

from statscan.wds.client import Client


async def main():  # noqa: PLR0915
    """Demonstrate HTTP response caching."""
    print("=" * 70)
    print("HTTP Response Caching Example")
    print("=" * 70)

    # Option 1: Persistent cache (recommended for repeated use)
    # The cache file will be reused across program runs
    cache_path = "census_cache.db"

    # Option 2: Temporary cache (auto-deleted on exit)
    # cache_path = None  # Creates temp file

    # Option 3: Disable caching
    # Client(cache_path=False, enable_cache=False)

    async with Client(cache_path=cache_path) as client:
        print(f"\n✓ Using cache file: {cache_path}")

        # Show initial cache state
        stats = client.get_cache_stats()
        print(f"  Initial cache entries: {stats['total_entries']}\n")

        # =================================================================
        # Example 1: DataFrame downloads (large files)
        # =================================================================
        print("=" * 70)
        print("Example 1: DataFrame Download (Census Data)")
        print("=" * 70)

        product_id = 98100002  # Census subdivisions

        print("\nFirst call (may download from API)...")
        start1 = time.time()
        df1 = await client.get_dataframe(product_id, geo="Toronto")
        elapsed1 = time.time() - start1

        print(f"✓ Got DataFrame: {len(df1)} rows, {len(df1.columns)} columns")
        print(f"  Time: {elapsed1:.3f}s")

        print("\nSecond call (should use cache)...")
        start2 = time.time()
        df2 = await client.get_dataframe(product_id, geo="Toronto")
        elapsed2 = time.time() - start2

        print(f"✓ Got DataFrame: {len(df2)} rows, {len(df2.columns)} columns")
        print(f"  Time: {elapsed2:.4f}s")

        if elapsed2 < elapsed1:
            speedup = elapsed1 / elapsed2
            print(f"  🚀 Speed improvement: {speedup:.1f}x faster!")

        # =================================================================
        # Example 2: Metadata queries (JSON responses)
        # =================================================================
        print("\n" + "=" * 70)
        print("Example 2: Metadata Query")
        print("=" * 70)

        print("\nFirst metadata call...")
        start3 = time.time()
        metadata1 = await client.get_cube_metadata(product_id)
        elapsed3 = time.time() - start3

        print(f"✓ Got metadata for: {metadata1.cubeTitleEn[:50]}...")
        print(f"  Time: {elapsed3:.3f}s")

        print("\nSecond metadata call (should use cache)...")
        start4 = time.time()
        await client.get_cube_metadata(product_id)
        elapsed4 = time.time() - start4

        print("✓ Got metadata (from cache)")
        print(f"  Time: {elapsed4:.4f}s")

        if elapsed4 < elapsed3:
            speedup = elapsed3 / elapsed4
            print(f"  🚀 Speed improvement: {speedup:.1f}x faster!")

        # =================================================================
        # Cache Management
        # =================================================================
        print("\n" + "=" * 70)
        print("Cache Management")
        print("=" * 70)

        # Get cache statistics
        stats = client.get_cache_stats()
        print("\nCache Statistics:")
        print(f"  • Total cached responses: {stats['total_entries']}")
        print(f"  • Total cache hits: {stats['total_accesses']}")
        print(f"  • Cache size: {stats['cache_size_mb']:.2f} MB")
        print(f"  • Most accessed URL: {stats['most_accessed_url'][:50]}...")

        # List all cached responses
        print("\nCached Responses:")
        cached = client.list_cached_responses()
        max_display = 3
        for i, entry in enumerate(cached[:max_display], 1):  # Show first 3
            size_kb = entry['content_length'] / 1024
            print(f"\n  {i}. {entry['method']} {entry['url'][:45]}...")
            print(f"     Status: {entry['status_code']}")
            print(f"     Size: {size_kb:.1f} KB")
            print(f"     Accessed: {entry['access_count']} times")

        if len(cached) > max_display:
            print(f"\n  ... and {len(cached) - max_display} more cached responses")

        # Optional: Clear cache
        # count = client.clear_cache()
        # print(f"\n✓ Cleared {count} cached responses")

        print("\n" + "=" * 70)
        print("Key Takeaways")
        print("=" * 70)
        print("""
  ✓ Caching works transparently - no code changes needed
  ✓ All API methods benefit (DataFrames, metadata, etc.)
  ✓ Significant speed improvements for repeated requests
  ✓ Cache persists across program runs
  ✓ Easy cache management with clear(), get_stats(), list_cached_responses()

  💡 Tip: Use persistent cache (cache_path="my_cache.db") for best performance
        """)

        print(f"Cache file: {Path(cache_path).absolute()}")


if __name__ == "__main__":
    asyncio.run(main())
