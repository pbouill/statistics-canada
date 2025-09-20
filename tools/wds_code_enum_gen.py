from pathlib import Path
import logging

from statscan.wds.client import Client
from statscan.wds.models.code import CodeSet, CodeSets

from tools.enum_writer import AbstractEnumWriter, EnumEntry, InvalidEnumValueError


logger = logging.getLogger(__name__)

class CodeSetEnumWriter(AbstractEnumWriter):
    def generate_enum_entries(self, data: CodeSet) -> list[EnumEntry]:
        entries_dict: dict[int, EnumEntry] = {}
        code_dict = data.code_dict()
        logger.info(f"Starting first pass with {len(code_dict)} codes...")

        # first pass, try truncation (optimized for performance)
        for i, (code_value, code) in enumerate(code_dict.items()):
            if i % 250 == 0:  # Reduced logging frequency for better performance
                logger.info(f"  Processing entry {i+1}/{len(code_dict)}: code {code_value}")
            
    
            # Handle empty or None descriptions more efficiently
            desc_en = code.desc_en or f'CODE_{code_value}'
            
            # Apply substitution and cleaning in one pass
            name = self.subs_engine.substitute(desc_en, truncate=True)
            try:
                name = EnumEntry.clean_name(name)
            except ValueError as ve:
                logger.warning(f'Error cleaning name for code {code_value}: {ve}')
                name = 'UNKNOWN'
            
            # Build comment more efficiently - avoid None concatenation
            if code.desc_en and code.desc_fr:
                desc = f'{code.desc_en}  // {code.desc_fr}'
            elif code.desc_en:
                desc = code.desc_en
            elif code.desc_fr:
                desc = code.desc_fr
            else:
                desc = None
            
            if code_value in entries_dict:
                raise InvalidEnumValueError(f"Duplicate code value detected: {code_value}")
            entries_dict[code_value] = EnumEntry(name=name, value=code_value, comment=desc)

        all_entries = list(entries_dict.values())
        self.resolve_duplicate_names(entries=all_entries, original_names=[code.desc_en or 'UNKNOWN' for code in code_dict.values()])
        return all_entries

    async def get_all_codesets(self) -> CodeSets:
        """Fetch all available codesets from WDS."""
        logger.info("Fetching all codesets...")
        client = Client()
        
        codesets = await client.get_code_sets()
        
        logger.info(f"Successfully fetched {len(codesets.root)} codesets")
        
        return codesets
    
    def write_codeset_enum(
        self, 
        codeset_name: str, 
        code_set: CodeSet, 
        output_dir: Path,
        overwrite: bool = False,
    ) -> Path:
        logger.info(f"Processing codeset: {codeset_name}")
        cls_name = self.subs_engine.camel_to_title(codeset_name)
        filename = self.subs_engine.camel_to_snake(codeset_name) + '.py'
        file_path = output_dir / filename

        logger.info(f"Generating enum entries for {codeset_name}...")
        entries = self.generate_enum_entries(code_set)
        logger.info(f"Generated {len(entries)} entries for {codeset_name}")

        imports = {'enum': 'Enum'}

        logger.info(f"Writing enum file: {file_path}")
        with self.enum_file(file_path, imports=imports, overwrite=overwrite) as f:
            self.write_class(
                f=f, 
                entries=entries, 
                cls_name=cls_name,
            )
        logger.info(f"Completed processing {codeset_name}")
        return file_path

    def write_codesets_enums(
        self,
        codesets: CodeSets,
        output_dir: Path,
        overwrite: bool = False,
    ) -> dict[str, Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        gen_map = {}
        
        # Get codeset items properly (CodeSets is RootModel)
        codeset_items = codesets.root.items()
        total_codesets = len(list(codeset_items))
        logger.info(f"Processing {total_codesets} codesets...")
        
        for i, (codeset_name, code_set) in enumerate(codeset_items, 1):
            logger.info(f"[{i}/{total_codesets}] Starting {codeset_name}")
            try:
                gen_map[codeset_name] = self.write_codeset_enum(
                    codeset_name=codeset_name,
                    code_set=code_set,
                    output_dir=output_dir,
                    overwrite=overwrite,
                )
                logger.info(f"[{i}/{total_codesets}] Completed {codeset_name}")
            except Exception as e:
                logger.error(f"Failed to write enum for {codeset_name}: {e}", exc_info=True)
        return gen_map
    
    async def fetch_and_create_enums(
        self,
        output_dir: Path,
        overwrite: bool = False,
    ) -> dict[str, Path]:
        logger.info("Starting fetch_and_create_enums...")
        codesets = await self.get_all_codesets()
        logger.info("Codesets fetched, starting enum generation...")
        result = self.write_codesets_enums(
            codesets=codesets,
            output_dir=output_dir,
            overwrite=overwrite,
        )
        logger.info("Enum generation completed")
        return result
    

if __name__ == "__main__":
    import asyncio
    from statscan.util.log import configure_logging

    configure_logging(level=logging.DEBUG)


    print("WDS Code Set Enum Generator\n")
    DEFAULT_OUTPUT_PATH = Path(__file__).parent.parent / 'scratch' / 'enums' / 'wds'

    generator = CodeSetEnumWriter()
    
    print("Starting enum generation...")
    logger.info("Fetching codesets...")
    
    try:
        asyncio.run(generator.fetch_and_create_enums(output_dir=DEFAULT_OUTPUT_PATH, overwrite=True))
        print("\nGeneration complete! All enums ready for use.")
    except Exception as e:
        logger.error(f"Error during generation: {e}", exc_info=True)

