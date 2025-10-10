"""SDMX data container with datasets and structures."""

from ..base import Base
from .dataset.dataset import Dataset
from .structure.structure import Structure


class Data(Base):
    """Container for SDMX datasets and structure definitions."""

    dataSets: list[Dataset]  # noqa: N815
    structures: list[Structure]

    # def get_dimensions(self, dataset_series: Series):
    #     for s in self.structures:
    #         if dataset_series.
