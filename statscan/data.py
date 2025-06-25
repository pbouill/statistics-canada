from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

"""
Pydantic models for handling data retrieved from the Stats Canada API.
These models are designed to parse SDMX-JSON format responses.
"""

# ============================================================================
# Base Models
# ============================================================================

class SDMXBaseModel(BaseModel):
    """Base model with common configuration for SDMX models."""
    model_config = ConfigDict(extra='allow')


# ============================================================================
# Metadata Models
# ============================================================================

class SDMXSender(SDMXBaseModel):
    """Represents the sender information in SDMX metadata."""
    id: str = Field(description="Sender identifier")
    name: Optional[str] = Field(None, description="Sender name")
    names: Optional[dict[str, str]] = Field(None, description="Localized names")


class SDMXReceiver(SDMXBaseModel):
    """Represents the receiver information in SDMX metadata."""
    id: str = Field(description="Receiver identifier")


class SDMXMeta(SDMXBaseModel):
    """Represents the metadata section of an SDMX response."""
    schema_url: str = Field(alias="schema", description="SDMX schema URL")
    id: str = Field(description="Message identifier")
    prepared: datetime = Field(description="Message preparation timestamp")
    test: Optional[bool] = Field(None, description="Whether this is test data")
    content_languages: list[str] = Field(alias="contentLanguages", description="Content languages")
    sender: SDMXSender = Field(description="Message sender")
    receiver: Optional[list[SDMXReceiver]] = Field(None, description="Message receivers")


# ============================================================================
# Data Structure Models
# ============================================================================

class SDMXLink(SDMXBaseModel):
    """Represents a link in SDMX data."""
    urn: str = Field(description="URN identifier")
    rel: str = Field(description="Relationship type")


class SDMXObservation(SDMXBaseModel):
    """Represents an observation in SDMX data."""
    value: str | float | int | None = Field(description="Observation value")
    status: Optional[int] = Field(None, description="Observation status")
    attributes: Optional[list[Any]] = Field(None, description="Additional attributes")


class SDMXSeries(SDMXBaseModel):
    """Represents a data series in SDMX format."""
    attributes: Optional[list[Any]] = Field(None, description="Series attributes")
    annotations: Optional[list[Any]] = Field(None, description="Series annotations")
    observations: dict[str, list[Any]] = Field(description="Time series observations")


class SDMXDataSet(SDMXBaseModel):
    """Represents a dataset in SDMX format."""
    structure: int = Field(description="Structure reference")
    action: str = Field(description="Dataset action")
    links: Optional[list[SDMXLink]] = Field(None, description="Related links")
    annotations: Optional[list[int]] = Field(None, description="Annotation references")
    series: dict[str, SDMXSeries] = Field(description="Data series")


# ============================================================================
# Structure Models
# ============================================================================

class SDMXAnnotation(SDMXBaseModel):
    """Represents an annotation in SDMX structures."""
    id: Optional[str] = Field(None, description="Annotation identifier")
    title: Optional[str] = Field(None, description="Annotation title")
    type: Optional[str] = Field(None, description="Annotation type")
    text: Optional[str] = Field(None, description="Annotation text")
    texts: Optional[dict[str, str]] = Field(None, description="Localized text")


class SDMXConcept(SDMXBaseModel):
    """Represents a concept in SDMX structures."""
    id: str = Field(description="Concept identifier")
    name: str = Field(description="Concept name")
    names: dict[str, str] = Field(description="Localized names")
    annotations: Optional[list[SDMXAnnotation]] = Field(None, description="Concept annotations")


class SDMXCode(SDMXBaseModel):
    """Represents a code in SDMX code lists."""
    id: str = Field(description="Code identifier")
    name: str = Field(description="Code name")
    names: dict[str, str] = Field(description="Localized names")
    description: Optional[str] = Field(None, description="Code description")
    descriptions: Optional[dict[str, str]] = Field(None, description="Localized descriptions")


class SDMXCodeList(SDMXBaseModel):
    """Represents a code list in SDMX structures."""
    id: str = Field(description="Code list identifier")
    version: str = Field(description="Code list version")
    agency_id: str = Field(alias="agencyID", description="Agency identifier")
    is_final: bool = Field(alias="isFinal", description="Whether the code list is final")
    name: str = Field(description="Code list name")
    names: dict[str, str] = Field(description="Localized names")
    description: Optional[str] = Field(None, description="Code list description")
    descriptions: Optional[dict[str, str]] = Field(None, description="Localized descriptions")
    annotations: Optional[list[SDMXAnnotation]] = Field(None, description="Code list annotations")
    is_partial: bool = Field(alias="isPartial", description="Whether the code list is partial")
    codes: list[SDMXCode] = Field(description="Codes in the list")


class SDMXConceptScheme(SDMXBaseModel):
    """Represents a concept scheme in SDMX structures."""
    id: str = Field(description="Concept scheme identifier")
    version: str = Field(description="Concept scheme version")
    agency_id: str = Field(alias="agencyID", description="Agency identifier")
    is_final: bool = Field(alias="isFinal", description="Whether the concept scheme is final")
    name: str = Field(description="Concept scheme name")
    names: dict[str, str] = Field(description="Localized names")
    is_partial: bool = Field(alias="isPartial", description="Whether the concept scheme is partial")
    concepts: list[SDMXConcept] = Field(description="Concepts in the scheme")


class SDMXDataflow(SDMXBaseModel):
    """Represents a dataflow in SDMX structures."""
    id: str = Field(description="Dataflow identifier")
    version: str = Field(description="Dataflow version")
    agency_id: str = Field(alias="agencyID", description="Agency identifier")
    is_final: bool = Field(alias="isFinal", description="Whether the dataflow is final")
    name: str = Field(description="Dataflow name")
    names: dict[str, str] = Field(description="Localized names")
    annotations: Optional[list[SDMXAnnotation]] = Field(None, description="Dataflow annotations")
    structure: str = Field(description="Data structure reference")


class SDMXDimension(SDMXBaseModel):
    """Represents a dimension in SDMX data structures."""
    id: str = Field(description="Dimension identifier")
    position: int = Field(description="Dimension position")
    concept_identity: str = Field(alias="conceptIdentity", description="Concept identity reference")
    local_representation: Optional[dict[str, Any]] = Field(None, alias="localRepresentation", description="Local representation")


class SDMXAttribute(SDMXBaseModel):
    """Represents an attribute in SDMX data structures."""
    id: str = Field(description="Attribute identifier")
    assignment_status: str = Field(alias="assignmentStatus", description="Assignment status")
    concept_identity: str = Field(alias="conceptIdentity", description="Concept identity reference")
    local_representation: Optional[dict[str, Any]] = Field(None, alias="localRepresentation", description="Local representation")


class SDMXDataStructureComponents(SDMXBaseModel):
    """Represents the components of a data structure."""
    dimension_list: Optional[dict[str, Any]] = Field(None, alias="dimensionList", description="Dimension list")
    attribute_list: Optional[dict[str, Any]] = Field(None, alias="attributeList", description="Attribute list")
    measure_list: Optional[dict[str, Any]] = Field(None, alias="measureList", description="Measure list")


class SDMXDataStructure(SDMXBaseModel):
    """Represents a data structure definition in SDMX."""
    id: str = Field(description="Data structure identifier")
    version: str = Field(description="Data structure version")
    agency_id: str = Field(alias="agencyID", description="Agency identifier")
    is_final: bool = Field(alias="isFinal", description="Whether the data structure is final")
    name: str = Field(description="Data structure name")
    names: dict[str, str] = Field(description="Localized names")
    data_structure_components: SDMXDataStructureComponents = Field(alias="dataStructureComponents", description="Structure components")


class SDMXContentConstraint(SDMXBaseModel):
    """Represents a content constraint in SDMX structures."""
    id: str = Field(description="Constraint identifier")
    version: str = Field(description="Constraint version")
    agency_id: str = Field(alias="agencyID", description="Agency identifier")
    is_final: bool = Field(alias="isFinal", description="Whether the constraint is final")
    name: str = Field(description="Constraint name")
    names: dict[str, str] = Field(description="Localized names")
    type: str = Field(description="Constraint type")


class SDMXStructureData(SDMXBaseModel):
    """Represents the data section of an SDMX structure message."""
    dataflows: Optional[list[SDMXDataflow]] = Field(None, description="Available dataflows")
    concept_schemes: Optional[list[SDMXConceptScheme]] = Field(None, alias="conceptSchemes", description="Concept schemes")
    codelists: Optional[list[SDMXCodeList]] = Field(None, description="Code lists")
    data_structures: Optional[list[SDMXDataStructure]] = Field(None, alias="dataStructures", description="Data structures")
    content_constraints: Optional[list[SDMXContentConstraint]] = Field(None, alias="contentConstraints", description="Content constraints")


class SDMXStructure(SDMXBaseModel):
    """Represents a structure definition in SDMX data."""
    name: str = Field(description="Structure name")
    names: dict[str, str] = Field(description="Localized names")
    dimensions: dict[str, Any] = Field(description="Structure dimensions")
    attributes: dict[str, Any] = Field(description="Structure attributes")
    annotations: list[Any] = Field(description="Structure annotations")
    data_sets: list[Any] = Field(alias="dataSets", description="Associated datasets")


class SDMXData(SDMXBaseModel):
    """Represents the data section of an SDMX message."""
    data_sets: list[SDMXDataSet] = Field(alias="dataSets", description="Data sets")
    structures: Optional[list[SDMXStructure]] = Field(None, description="Data structures")


# ============================================================================
# Main Response Models
# ============================================================================

class SDMXDataResponse(SDMXBaseModel):
    """
    Represents a complete SDMX data response from the Stats Canada API.
    This is used for data retrieval responses containing actual statistical data.
    """
    meta: SDMXMeta = Field(description="Response metadata")
    data: SDMXData = Field(description="Response data")
    errors: Optional[list[Any]] = Field(None, description="Response errors")


class SDMXStructureResponse(SDMXBaseModel):
    """
    Represents a complete SDMX structure response from the Stats Canada API.
    This is used for metadata retrieval responses containing structure definitions.
    """
    meta: SDMXMeta = Field(description="Response metadata")
    data: SDMXStructureData = Field(description="Structure data")


class DataflowsResponse(SDMXBaseModel):
    """
    Represents a dataflows response containing available data flows.
    """
    resources: list[Any] = Field(description="Resource list")
    references: dict[str, SDMXDataflow] = Field(description="Dataflow references")


# ============================================================================
# Legacy/Simplified Models
# ============================================================================

class SDMXResponse(SDMXBaseModel):
    """
    Legacy/simplified SDMX response model for backward compatibility.
    Can handle both data and structure responses.
    """
    meta: Optional[SDMXMeta] = Field(None, description="Response metadata")
    data: Optional[SDMXData | SDMXStructureData] = Field(None, description="Response data")
    resources: Optional[list[Any]] = Field(None, description="Resources (for dataflows)")
    references: Optional[dict[str, Any]] = Field(None, description="References (for dataflows)")
    errors: Optional[list[Any]] = Field(None, description="Response errors")


# ============================================================================
# Helper Functions
# ============================================================================

def parse_sdmx_response(json_data: dict[str, Any]) -> SDMXDataResponse | SDMXStructureResponse | DataflowsResponse | SDMXResponse:
    """
    Parse a JSON response from the Stats Canada API into the appropriate Pydantic model.
    
    Args:
        json_data: Raw JSON data from the API response
        
    Returns:
        Parsed Pydantic model instance
        
    Raises:
        ValueError: If the response format is not recognized
    """
    # Check if it's a dataflows response
    if "references" in json_data and "resources" in json_data:
        return DataflowsResponse(**json_data)
    
    # Check if it has data section
    if "data" in json_data:
        data_section = json_data["data"]
        
        # Check if it's a structure response (has dataflows, conceptSchemes, etc.)
        if any(key in data_section for key in ["dataflows", "conceptSchemes", "codelists", "dataStructures"]):
            return SDMXStructureResponse(**json_data)
        
        # Check if it's a data response (has dataSets)
        elif "dataSets" in data_section:
            return SDMXDataResponse(**json_data)
    
    # Fallback to legacy model
    return SDMXResponse(**json_data)


def extract_observations(series_data: dict[str, SDMXSeries]) -> list[dict[str, Any]]:
    """
    Extract observations from SDMX series data into a flattened list.
    
    Args:
        series_data: Dictionary of series data from SDMX response
        
    Returns:
        List of observation dictionaries
    """
    observations = []
    
    for series_key, series in series_data.items():
        for time_key, obs_data in series.observations.items():
            observation = {
                "series_key": series_key,
                "time_period": time_key,
                "value": obs_data[0] if obs_data else None,
                "status": obs_data[1] if len(obs_data) > 1 else None,
                "attributes": series.attributes,
                "annotations": series.annotations
            }
            observations.append(observation)
    
    return observations
