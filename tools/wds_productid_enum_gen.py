from pathlib import Path
from typing import Iterable
import logging


from statscan.wds.client import Client
from statscan.wds.models.cube import Cube

from tools.enum_writer import AbstractEnumWriter, EnumEntry, InvalidEnumValueError


logger = logging.getLogger(__name__)

class ProductIdEnumWriter(AbstractEnumWriter):
    def generate_enum_entries(self, data: Iterable[Cube]) -> list[EnumEntry]:
        entries_dict: dict[int, EnumEntry] = {}

        for cube in data:
            pid = cube.productId
            if pid in entries_dict:
                raise InvalidEnumValueError(f"Duplicate productId detected: {pid}")
            titleEn = cube.cubeTitleEn or f'PRODUCT_{pid}'
            name = self.subs_engine.substitute(titleEn, truncate=True)
            try:
                name = EnumEntry.clean_name(name)
            except ValueError as ve:
                logger.warning(f'Error cleaning name for cube {pid}: {ve}')
                name = 'UNKNOWN'

            if cube.cubeTitleEn and cube.cubeTitleFr:
                desc = f'{cube.cubeTitleEn}  // {cube.cubeTitleFr}'
            elif cube.cubeTitleEn:
                desc = cube.cubeTitleEn
            elif cube.cubeTitleFr:
                desc = cube.cubeTitleFr
            else:
                desc = None

            e = EnumEntry(name=name, value=pid, comment=desc)
            entries_dict[pid] = e

        all_entries = list(entries_dict.values())
        self.resolve_duplicate_names(entries=all_entries, original_names=[cube.cubeTitleEn or 'UNKNOWN' for cube in data])

        return all_entries

    async def get_all_cubes(self) -> list[Cube]:
        """Fetch all available cubes from WDS."""
        logger.info("Fetching all cubes...")
        client = Client()
        cubes = await client.get_all_cubes_list_lite()
        logger.info(f"Successfully fetched {len(cubes)} cubes")
        return cubes

    async def fetch_and_create_enum(
        self,
        fp: Path,
        overwrite: bool = False,
    ) -> Path:
        logger.info("Starting fetch_and_create_enums...")
        cubes = await self.get_all_cubes()
        logger.info("Cubes fetched, starting enum generation...")
        entries = self.generate_enum_entries(data=cubes)
        imports = {'enum': 'Enum'}
        with self.enum_file(fp=fp, imports=imports, overwrite=overwrite) as f:
            self.write_class(
                f=f,
                entries=entries,
                cls_name='ProductID',
            )
        logger.info("Enum generation completed")
        return fp


if __name__ == "__main__":
    import asyncio
    from statscan.util.log import configure_logging

    configure_logging(level=logging.DEBUG)

    print("WDS Product ID Enum Generator\n")
    DEFAULT_OUTPUT_PATH = Path(__file__).parent.parent / 'scratch' / 'enums' / 'wds'

    generator = ProductIdEnumWriter()

    print("Starting enum generation...")
    logger.info("Fetching cubes...")
    try:
        asyncio.run(
            generator.fetch_and_create_enum(
                fp=DEFAULT_OUTPUT_PATH / 'product_id.py',
                overwrite=True,
            )
        )
        print("\nGeneration complete! All enums ready for use.")
    except Exception as e:
        logger.error(f"Error during generation: {e}", exc_info=True)
