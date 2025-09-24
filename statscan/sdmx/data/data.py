
from ..base import Base
from .dataset.dataset import Dataset
from .dataset.series import Series
from .structure.structure import Structure
from .structure.dimensions import Dimensions


class Data(Base):
    dataSets: list[Dataset]
    structures: list[Structure]


    # def get_dimensions(self, dataset_series: Series):
    #     for s in self.structures:
    #         if dataset_series.