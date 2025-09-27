from pathlib import Path
from typing import Iterable
import logging
from tqdm import tqdm

from statscan.wds.client import Client
from statscan.wds.models.cube import Cube

from tools.enum_writer import AbstractEnumWriter, EnumEntry, InvalidEnumValueError


logger = logging.getLogger(__name__)


class ProductIdEnumWriter(AbstractEnumWriter):
    pass

    def generate_enum_entries(self, data: Iterable[Cube]) -> list[EnumEntry]:
        entries_dict: dict[int, EnumEntry] = {}
        cubes_list = list(data)  # Convert to list for efficient processing
        total_cubes = len(cubes_list)

        logger.info(f"Processing {total_cubes} product IDs...")

        original_names = []  # Collect for duplicate resolution

        # Use tqdm for progress tracking
        cubes_iter = tqdm(cubes_list, desc="Processing ProductIDs", unit="cube")

        for cube in cubes_iter:
            pid = cube.productId
            if pid in entries_dict:
                raise InvalidEnumValueError(f"Duplicate productId detected: {pid}")

            titleEn = cube.cubeTitleEn or f"PRODUCT_{pid}"
            original_names.append(titleEn)

            # Process text with substitution and word tracking
            name = self.process_text_with_substitution(
                original_text=titleEn, source_identifier="ProductID", truncate=True
            )

            try:
                name = EnumEntry.clean_name(name)
            except ValueError:
                name = "UNKNOWN"

            if cube.cubeTitleEn and cube.cubeTitleFr:
                desc = f"{cube.cubeTitleEn}  // {cube.cubeTitleFr}"
            elif cube.cubeTitleEn:
                desc = cube.cubeTitleEn
            elif cube.cubeTitleFr:
                desc = cube.cubeTitleFr
            else:
                desc = None

            e = EnumEntry(name=name, value=pid, comment=desc)
            entries_dict[pid] = e

        # tqdm will show completion automatically
        all_entries = list(entries_dict.values())
        self.resolve_duplicate_names(entries=all_entries, original_names=original_names)

        return all_entries

    async def get_all_cubes(self) -> list[Cube]:
        """Fetch all available cubes from WDS."""
        logger.info("Fetching all cubes...")
        client = Client()
        cubes = await client.get_all_cubes_list_lite()
        logger.info(f"Successfully fetched {len(cubes)} cubes")
        return cubes

    async def process(
        self,
        fp: Path,
        overwrite: bool = False,
    ) -> Path:
        """
        Main processing method that fetches data, generates enums, and writes files.

        Args:
            fp: Output file path
            overwrite: Whether to overwrite existing files

        Returns:
            Path to the generated file
        """
        logger.info("Starting ProductID enum processing...")

        cubes = await self.get_all_cubes()
        logger.info("Cubes fetched, starting enum generation...")
        entries = self.generate_enum_entries(data=cubes)
        imports = {"enum": "Enum"}
        with self.enum_file(fp=fp, imports=imports, overwrite=overwrite) as f:
            self.write_class(
                f=f,
                entries=entries,
                cls_name="ProductID",
            )
        logger.info("Enum generation completed")
        return fp

    async def fetch_and_create_enum(
        self,
        fp: Path,
        overwrite: bool = False,
        track_words: bool = False,
    ) -> Path:
        """Legacy method for backward compatibility."""
        # Update tracking settings
        self.track_words = track_words
        if track_words:
            from tools.cli.word_tracker import get_word_tracker

            self.word_tracker = get_word_tracker()
        else:
            self.word_tracker = None

        return await self.process(fp=fp, overwrite=overwrite)


if __name__ == "__main__":
    import asyncio
    from statscan.util.log import configure_logging

    configure_logging(level=logging.DEBUG)

    print("WDS Product ID Enum Generator\n")
    DEFAULT_OUTPUT_PATH = Path(__file__).parent.parent / "scratch" / "enums" / "wds"

    generator = ProductIdEnumWriter()

    print("Starting enum generation...")
    logger.info("Fetching cubes...")
    try:
        asyncio.run(
            generator.fetch_and_create_enum(
                fp=DEFAULT_OUTPUT_PATH / "product_id.py",
                overwrite=True,
            )
        )
        print("\nGeneration complete! All enums ready for use.")
    except Exception as e:
        logger.error(f"Error during generation: {e}", exc_info=True)
