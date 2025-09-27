from pathlib import Path
import logging
from tqdm import tqdm

from statscan.wds.client import Client
from statscan.wds.models.code import CodeSet, CodeSets

from tools.enum_writer import AbstractEnumWriter, EnumEntry, InvalidEnumValueError


logger = logging.getLogger(__name__)


class CodeSetEnumWriter(AbstractEnumWriter):
    pass

    def generate_enum_entries(
        self, data: CodeSet, codeset_name: str = "unknown"
    ) -> list[EnumEntry]:
        entries_dict: dict[int, EnumEntry] = {}
        code_dict = data.code_dict()
        total_codes = len(code_dict)
        logger.info(f"Processing {total_codes} codes...")

        # Use tqdm for progress tracking
        code_iter = tqdm(
            code_dict.items(), desc="Processing codes", unit="code", total=total_codes
        )

        for code_value, code in code_iter:
            # Handle empty or None descriptions more efficiently
            desc_en = code.desc_en or f"CODE_{code_value}"

            # Process text with substitution and word tracking
            name = self.process_text_with_substitution(
                original_text=desc_en,
                source_identifier=f"CodeSet:{codeset_name}",
                truncate=True,
            )

            try:
                name = EnumEntry.clean_name(name)
            except ValueError:
                name = "UNKNOWN"

            # Build comment more efficiently - avoid None concatenation
            if code.desc_en and code.desc_fr:
                desc = f"{code.desc_en}  // {code.desc_fr}"
            elif code.desc_en:
                desc = code.desc_en
            elif code.desc_fr:
                desc = code.desc_fr
            else:
                desc = None

            if code_value in entries_dict:
                raise InvalidEnumValueError(
                    f"Duplicate code value detected: {code_value}"
                )
            entries_dict[code_value] = EnumEntry(
                name=name, value=code_value, comment=desc
            )

        logger.info(f"Completed processing {total_codes} codes")
        all_entries = list(entries_dict.values())

        # Resolve duplicates
        original_names = [code.desc_en or "UNKNOWN" for code in code_dict.values()]
        self.resolve_duplicate_names(entries=all_entries, original_names=original_names)

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
        filename = self.subs_engine.camel_to_snake(codeset_name) + ".py"
        file_path = output_dir / filename

        logger.info(f"Generating enum entries for {codeset_name}...")
        entries = self.generate_enum_entries(code_set, codeset_name=codeset_name)
        logger.info(f"Generated {len(entries)} entries for {codeset_name}")

        imports = {"enum": "Enum"}

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
        codeset_items = list(codesets.root.items())
        total_codesets = len(codeset_items)
        logger.info(f"Processing {total_codesets} codesets...")

        # Use tqdm for codeset progress tracking
        codeset_iter = tqdm(codeset_items, desc="Processing codesets", unit="codeset")

        for codeset_name, code_set in codeset_iter:
            try:
                gen_map[codeset_name] = self.write_codeset_enum(
                    codeset_name=codeset_name,
                    code_set=code_set,
                    output_dir=output_dir,
                    overwrite=overwrite,
                )
                codeset_iter.set_postfix_str(f"✓ {codeset_name}")
            except Exception as e:
                logger.error(f"✗ Failed {codeset_name}: {e}")
                codeset_iter.set_postfix_str(f"✗ {codeset_name}")
        return gen_map

    async def process(
        self,
        output_dir: Path,
        overwrite: bool = False,
    ) -> dict[str, Path]:
        """
        Main processing method that fetches all codesets and generates all enums.

        Args:
            output_dir: Output directory for generated files
            overwrite: Whether to overwrite existing files

        Returns:
            Dictionary mapping codeset names to generated file paths
        """
        logger.info("Starting CodeSet enum processing...")

        # Fetch all codesets first
        codesets = await self.get_all_codesets()
        logger.info(
            f"Codesets fetched, starting enum generation for {len(codesets)} codesets..."
        )

        # Use the existing write_codesets_enums method to avoid duplication
        return self.write_codesets_enums(
            codesets=codesets, output_dir=output_dir, overwrite=overwrite
        )

    async def fetch_and_create_enums(
        self,
        output_dir: Path,
        overwrite: bool = False,
        track_words: bool = False,
    ) -> dict[str, Path]:
        """Legacy method for backward compatibility."""
        # Update tracking settings
        self.track_words = track_words
        if track_words:
            from tools.word_tracker import get_word_tracker

            self.word_tracker = get_word_tracker()
        else:
            self.word_tracker = None

        return await self.process(output_dir=output_dir, overwrite=overwrite)

    async def process_single(
        self,
        codeset_name: str,
        fp: Path,
        overwrite: bool = False,
    ) -> Path:
        """
        Process a single codeset and generate its enum.

        Args:
            codeset_name: Name of the codeset to process
            fp: Output file path
            overwrite: Whether to overwrite existing files

        Returns:
            Path to the generated file
        """
        logger.info(f"Starting single codeset processing: {codeset_name}")

        # Fetch all codesets first to find the target
        codesets = await self.get_all_codesets()

        if codeset_name not in codesets:
            available = ", ".join(sorted(codesets.keys()))
            raise ValueError(
                f"Codeset '{codeset_name}' not found. Available: {available}"
            )

        logger.info(f"Found codeset '{codeset_name}', generating enum...")

        # Use the existing write_codeset_enum method to avoid duplication
        # Note: we need to use the output directory from fp and ensure consistent naming
        output_dir = fp.parent
        generated_fp = self.write_codeset_enum(
            codeset_name=codeset_name,
            code_set=codesets[codeset_name],
            output_dir=output_dir,
            overwrite=overwrite,
        )

        # If the caller specified a different filename, rename the generated file
        if generated_fp != fp:
            logger.info(f"Renaming {generated_fp} to {fp}")
            generated_fp.rename(fp)

        logger.info(f"Single enum generation completed: {fp}")
        return fp

    async def fetch_and_create_single_enum(
        self,
        codeset_name: str,
        fp: Path,
        overwrite: bool = False,
        track_words: bool = False,
    ) -> Path:
        """Legacy method for backward compatibility."""
        # Update tracking settings
        self.track_words = track_words
        if track_words:
            from tools.word_tracker import get_word_tracker

            self.word_tracker = get_word_tracker()
        else:
            self.word_tracker = None

        return await self.process_single(
            codeset_name=codeset_name, fp=fp, overwrite=overwrite
        )


if __name__ == "__main__":
    import asyncio
    from statscan.util.log import configure_logging

    configure_logging(level=logging.DEBUG)

    print("WDS Code Set Enum Generator\n")
    DEFAULT_OUTPUT_PATH = Path(__file__).parent.parent / "scratch" / "enums" / "wds"

    generator = CodeSetEnumWriter()

    print("Starting enum generation...")
    logger.info("Fetching codesets...")

    try:
        asyncio.run(
            generator.fetch_and_create_enums(
                output_dir=DEFAULT_OUTPUT_PATH, overwrite=True
            )
        )
        print("\nGeneration complete! All enums ready for use.")
    except Exception as e:
        logger.error(f"Error during generation: {e}", exc_info=True)
