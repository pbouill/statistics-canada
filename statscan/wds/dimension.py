from pydantic import BaseModel

from .footnote import Footnote
from .link import Link
from .member import Member


'''
example response:
[
    {
        "status": "SUCCESS",
        "object": {
        "responseStatusCode": 0,
        "productId": "35100003",
        "cansimId": "251-0008",
        "cubeTitleEn": "Average counts of young persons in provincial and territorial correctional services",
        "cubeTitleFr": "Comptes moyens des adolescents dans les services correctionnels provinciaux et territoriaux",
        "cubeStartDate": "1997-01-01",
        "cubeEndDate": "2015-01-01",
        "frequencyCode": 12,
        "nbSeriesCube": 171,
        "nbDatapointsCube": 3129,
        "releaseTime": "2015-05-09T08:30",
        "archiveStatusCode": "2",
        "archiveStatusEn": "CURRENT - a cube available to the public and that is current",
        "archiveStatusFr": "ACTIF - un cube qui est disponible au public et qui est toujours mise a jour",
        "subjectCode": [
            "350102",
            "4211"
        ],
            "surveyCode": [
            "3313"
        ],
        "dimension": [
            {
                "dimensionPositionId": 1,
                "dimensionNameEn": "Geography",
                "dimensionNameFr": "Géographie",
                "hasUom": false,
                "member": [
                    {
                    "memberId": 1,
                    "parentMemberId": 15,
                    "memberNameEn": "Newfoundland and Labrador",
                    "memberNameFr": "Terre-Neuve-et-Labrador",
                    "classificationCode": "10",
                    "classificationTypeCode": "1",
                    "geoLevel": 2,
                    "vintage": 2011,
                    "terminated": 0,
                    "memberUomCode": null
                    },
                    … repeating objects
                "footnote":[
                    {
                        "footnoteId":1,
                        "footnotesEn":"Corrections Key Indicator Report for Youth, Canadian Centre for Justice and Community Safety Statistics (CCJCSS), Statistics Canada. Fiscal year (April 1 through March 31). Due to rounding,
                    … repeating objects
                "link":{
                    "footnoteId":22,
                    "dimensionPositionId":2,
                    "memberId":12
                }
            }
        ],
        "correctionFootnote":[],
        "geoAttribute":[],
        "correction":[],
        "issueDate":"2021-04-13"
    }
]
'''







class Dimension(BaseModel):
    dimensionPositionId: int
    dimensionNameEn: str
    dimensionNameFr: str
    hasUom: bool
    member: list[Member]
    footnote: list[Footnote]
    link: list[Link]


class DimensionManager:
    def __init__(self, dimensions: list[Dimension]):
        self._dimensions = dimensions

    

    def get_dimension(self, dimension_id: int) -> Dimension | None:
        for dimension in self.dimensions:
            if dimension.dimensionPositionId == dimension_id:
                return dimension
        return None

    def get_all_dimensions(self) -> list[Dimension]:
        return self.dimensions