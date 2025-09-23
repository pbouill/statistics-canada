
from statscan.wds.models.code import CodeSets, CodeSet, Code
from statscan.wds.models.cube import Cube
from statscan.enums.auto.wds.scalar import Scalar
# from statscan.enums.auto.wds.product_id import ProductID


class TestWDSModels:
    def test_codesets_model(self, codesets_data: dict) -> None:
        """Test that CodeSets model can be created from API response data."""
        assert isinstance(codesets_data, dict)
        assert "object" in codesets_data
        codesets = CodeSets.model_validate(codesets_data["object"])
        assert isinstance(codesets, CodeSets)
        assert 'scalar' in codesets
        scalar_codeset = codesets['scalar']
        assert isinstance(scalar_codeset, CodeSet)
        units_code = scalar_codeset.find_code(desc_en=Scalar.UNITS.name.lower())
        assert isinstance(units_code, Code)
        assert units_code.value == Scalar.UNITS.value
        assert scalar_codeset[Scalar.UNITS.value] == units_code

    def test_cube_model(self, cubeslist_lite_data: list[dict]) -> None:
        """Test that Cube model can be created from API response data."""
        assert isinstance(cubeslist_lite_data, list)
        assert len(cubeslist_lite_data) > 0
        first_cube_data = cubeslist_lite_data[0]
        cube = Cube.model_validate(first_cube_data)
        assert isinstance(cube, Cube)

    