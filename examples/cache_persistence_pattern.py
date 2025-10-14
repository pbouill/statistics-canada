"""Example: Cache Persistence Across Client Instances.

This example demonstrates how the cache persists across multiple
`async with Client()` blocks, enabling optimal performance for
scripts that break work into multiple sections.

Key Concept:
- First context manager: Downloads data and caches
- Subsequent contexts: Instant responses from cache
- Cache cleanup: Only when Python process exits

This is the RECOMMENDED pattern for production scripts!
"""
import asyncio
import time

from statscan.wds.client import Client


async def main():  # noqa: PLR0915
    """Demonstrate cache persistence across multiple client instances."""
    print("=" * 70)
    print("Cache Persistence Demo")
    print("=" * 70)
    print("\nThis example shows cache persisting across multiple")
    print("`async with Client()` blocks for optimal performance.")
    print("=" * 70)

    # =================================================================
    # Phase 1: Initial Data Download
    # =================================================================
    print("\n📥 Phase 1: Initial Data Download")
    print("-" * 70)

    async with Client(cache_path="demo_cache.db") as client:
        print("✓ Client created with persistent cache")

        # Get code sets (metadata)
        print("\nDownloading code sets metadata...")
        start = time.time()
        codes = await client.get_code_sets()
        elapsed1 = time.time() - start

        print(f"✓ Downloaded {len(codes.code_set)} code sets")
        print(f"  Time: {elapsed1:.3f}s")

        # Get cube list
        print("\nDownloading cube list...")
        start = time.time()
        cubes = await client.get_all_cubes_list_lite()
        elapsed2 = time.time() - start

        print(f"✓ Downloaded {len(cubes)} cubes")
        print(f"  Time: {elapsed2:.3f}s")

        stats = client.get_cache_stats()
        print("\n📊 Cache Status:")
        print(f"  • Cached responses: {stats['total_entries']}")
        print(f"  • Total size: {stats['cache_size_mb']:.2f} MB")

    print("\n🔍 Context 1 closed (HTTP connection terminated)")
    print("   Cache file: Still exists ✅")

    # =================================================================
    # Phase 2: Data Analysis (Using Cached Data!)
    # =================================================================
    print("\n\n📊 Phase 2: Data Analysis")
    print("-" * 70)

    async with Client(cache_path="demo_cache.db") as client:
        print("✓ New client instance (same cache file)")

        # Same requests - should be instant!
        print("\nRequesting code sets metadata...")
        start = time.time()
        codes = await client.get_code_sets()
        cached_elapsed1 = time.time() - start

        print(f"✓ Got {len(codes.code_set)} code sets (CACHED!)")
        print(f"  Time: {cached_elapsed1:.4f}s")

        speedup1 = elapsed1 / cached_elapsed1
        print(f"  🚀 Speed improvement: {speedup1:.0f}x faster!")

        print("\nRequesting cube list...")
        start = time.time()
        cubes = await client.get_all_cubes_list_lite()
        cached_elapsed2 = time.time() - start

        print(f"✓ Got {len(cubes)} cubes (CACHED!)")
        print(f"  Time: {cached_elapsed2:.4f}s")

        speedup2 = elapsed2 / cached_elapsed2
        print(f"  🚀 Speed improvement: {speedup2:.0f}x faster!")

        # Analyze the data (simulated)
        print("\n📈 Analyzing data...")
        print(f"  • Total code sets: {len(codes.code_set)}")
        print(f"  • Total cubes: {len(cubes)}")

        # Check cache stats
        stats = client.get_cache_stats()
        print("\n📊 Cache Status:")
        print(f"  • Cached responses: {stats['total_entries']}")
        print(f"  • Total accesses: {stats['total_accesses']}")
        print(f"  • Cache hits: {stats['total_accesses'] - stats['total_entries']}")

    print("\n🔍 Context 2 closed (HTTP connection terminated)")
    print("   Cache file: Still exists ✅")

    # =================================================================
    # Phase 3: Generate Report (Still Using Cache!)
    # =================================================================
    print("\n\n📝 Phase 3: Generate Report")
    print("-" * 70)

    async with Client(cache_path="demo_cache.db") as client:
        print("✓ New client instance (same cache file)")

        # Yet another request - still cached!
        print("\nGenerating statistics report...")
        start = time.time()
        codes = await client.get_code_sets()
        elapsed = time.time() - start

        print("✓ Retrieved metadata (CACHED!)")
        print(f"  Time: {elapsed:.4f}s")

        # Show cache statistics
        stats = client.get_cache_stats()
        print("\n📊 Final Cache Statistics:")
        print(f"  • Cached responses: {stats['total_entries']}")
        print(f"  • Total accesses: {stats['total_accesses']}")
        print(f"  • Cache size: {stats['cache_size_mb']:.2f} MB")
        print(f"  • Oldest entry: {stats['oldest_entry']}")
        print(f"  • Newest entry: {stats['newest_entry']}")

        # List cached responses
        print("\n📋 Cached Responses:")
        cached = client.list_cached_responses()
        for entry in cached:
            size_kb = entry['content_length'] / 1024
            print(f"  • {entry['method']} {entry['url']}")
            print(
                f"    Size: {size_kb:.1f} KB, "
                f"Accessed: {entry['access_count']} times"
            )

    print("\n🔍 Context 3 closed (HTTP connection terminated)")
    print("   Cache file: Still exists ✅")

    # =================================================================
    # Summary
    # =================================================================
    print("\n" + "=" * 70)
    print("✅ Demo Complete!")
    print("=" * 70)
    print("""
Key Takeaways:
  • Cache persists across all `async with Client()` blocks
  • First request downloads, subsequent requests instant
  • Perfect for multi-phase scripts (download → analyze → report)
  • Cache file only deleted when you remove it manually

Performance:
  • First call: Downloads from API (slower)
  • Cached calls: Instant responses (10-500x faster!)

Next Steps:
  • Use persistent cache in your scripts
  • Delete cache file when you want fresh data
  • Use temp cache (cache_path=None) for one-off scripts
    """)

    print("\nCache file location: demo_cache.db")
    print("Run this script again to see instant responses from cache!")


if __name__ == "__main__":
    asyncio.run(main())
