from typing import Optional, Iterator
from statscan.wds.models.cube import Cube, CubeExistsError


class CubeManager:
    def __init__(self, cubes: Optional[list[Cube]] = None):
        self.__cubes: list[Cube] = cubes or []

    @property
    def cubes(self) -> dict[int, Cube]:
        return {cube.productId: cube for cube in self.__cubes}

    @property
    def latest_cube(self) -> Optional[Cube]:
        if not self.__cubes:
            return None
        return max(self.__cubes, key=lambda c: c.releaseTime)

    @property
    def product_ids(self) -> set[int]:
        return {cube.productId for cube in self.__cubes}

    def update_cube(self, cube: Cube) -> bool:
        """
        Update an existing cube in the manager.
        Args:
            cube (Cube): The cube to update or add.
        Returns:
            bool: True if the cube was updated, False if no changes were made.
        """
        if (existing_cube := self.cubes.get(cube.productId)) is not None:
            if existing_cube == cube:
                return False  # No changes
            else:
                self[cube.productId] = cube
            return True
        else:
            raise KeyError(f"Cube with product ID {cube.productId} does not exist.")

    def add_cube(self, cube: Cube, replace: bool = False) -> bool:
        """
        Add a cube to the manager. If a cube with the same productId already exists,
        it will not be added unless `replace` is set to True.

        Args:
            cube (Cube): The cube to add.
            replace (bool): Whether to replace an existing cube with the same productId.
        Returns:
            bool: True if the cube was added or updated.
        """
        if cube.productId in self.product_ids:
            if not replace:
                raise CubeExistsError(
                    f"Cube with product ID {cube.productId} already exists. Cannot add {cube}"
                )
            else:
                return self.update_cube(cube)
        else:
            self.__cubes.append(cube)
            return True

    def remove_cube(self, cube: int | Cube) -> None:
        if isinstance(cube, int):
            cube = self[cube]
        self.__cubes.remove(cube)

    def __getitem__(self, product_id: int) -> Cube:
        if (cube := self.cubes.get(product_id)) is None:
            raise KeyError(f"Cube with product ID {product_id} does not exist.")
        return cube

    def __setitem__(self, product_id: int, cube: Cube) -> None:
        if (existing_cube := self.cubes.get(product_id)) is not None:
            self.__cubes.remove(existing_cube)
        self.__cubes.append(cube)

    def __iter__(self) -> Iterator[Cube]:
        return iter(self.__cubes)

    def __len__(self) -> int:
        return len(self.__cubes)
