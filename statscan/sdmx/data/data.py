from ..base import Base
from .dataset.dataset import Dataset
from .structure.structure import Structure


class Data(Base):
    dataSets: list[Dataset]
    structures: list[Structure]

    # def get_dimensions(self, dataset_series: Series):
    #     for s in self.structures:
    #         if dataset_series.
