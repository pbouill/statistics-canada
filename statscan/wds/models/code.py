from pydantic import model_validator, RootModel
from typing import Any, Iterable, Iterator, Optional
from .base import WDSBaseModel


class Code(WDSBaseModel):
    value: int
    desc_en: Optional[str] = None
    desc_fr: Optional[str] = None

    # lets add a method for model_validate to intercept dict keys that should be renamed
    @model_validator(mode='before')
    @classmethod
    def rename_keys(cls, data: dict[str, Any]) -> dict[str, Any]:
        key_map = cls.get_model_key_map(data.keys())
        for k, v in key_map.items():
            data[v] = data.pop(k)  # rename key k to v
        return data

    @classmethod
    def get_model_key_map(cls, keys: Iterable[str]):
        detected_keys: dict[str, str] = {}
        for k in keys:
            if k.endswith("DescEn"):
                detected_keys[k] = "desc_en"
            elif k.endswith("DescFr"):
                detected_keys[k] = "desc_fr"
            elif k.endswith("Code"):
                detected_keys[k] = "value"

        # Fallback patterns for English descriptions
        if 'desc_en' not in detected_keys.values():
            for k in keys:
                if k.endswith('En'):
                    detected_keys[k] = 'desc_en'
                    break
        
        # Fallback patterns for French descriptions  
        if 'desc_fr' not in detected_keys.values():
            for k in keys:
                if k.endswith('Fr') and k not in detected_keys:
                    detected_keys[k] = 'desc_fr'
                    break

        # Fallback patterns for value
        if 'value' not in detected_keys.values():
            for k in keys:
                if k.endswith('Id'):
                    detected_keys[k] = 'value'
                    break
                    
        return detected_keys
    

class CodeSet(RootModel):
    root: list[Code]
    
    def codes(self) -> Iterator[Code]:
        """Iterate over codes in this codeset."""
        return iter(self.root)
    
    def find_code(
        self, 
        value: int | None = None, 
        desc_en: str | None = None,
        desc_fr: str | None = None,
    ) -> Code | None:
        if all(v is None for v in (value, desc_en, desc_fr)):
            raise ValueError("At least one of value, desc_en, or desc_fr must be provided.")
        for code in self.root:
            if ((value is not None and code.value == value) or
                (desc_en is not None and code.desc_en == desc_en) or
                (desc_fr is not None and code.desc_fr == desc_fr)):
                return code
        return None
    
    def code_dict(self) -> dict[int, Code]:
        """Return a dictionary mapping code values to Code objects."""
        return {code.value: code for code in self.root}
    
    def __contains__(self, code_value: int) -> bool:
        """Support 'code_value in codeset' syntax."""
        return code_value in self.code_dict()
        
    def __len__(self) -> int:
        """Return the number of codes in this codeset."""
        return len(self.root)
    
    def __getitem__(self, index: int) -> Code:
        """Support indexing like codeset[0]."""
        return self.code_dict()[index]


class CodeSets(RootModel):
    root: dict[str, CodeSet]
    
    def codesets(self) -> Iterator[tuple[str, CodeSet]]:
        """Iterate over all codesets as (name, codeset) pairs."""
        return iter(self.root.items())
    
    def count(self) -> int:
        """Return the total number of codes across all codesets."""
        return sum(len(codeset) for codeset in self.root.values())
    
    def codes(self) -> Iterator[Code]:
        """Iterate over all codes in all codesets."""
        for codeset in self.root.values():
            for code in codeset.codes():
                yield code
                        
    def has_code(self, code_value: int) -> bool:
        """Check if any codeset contains the specified code value."""
        return any(code_value in codeset for codeset in self.root.values())

    def get_codeset(self, name: str) -> Optional[CodeSet]:
        """Get a specific codeset by name."""
        return self.root.get(name)
    
    def __contains__(self, codeset_name: str) -> bool:
        """Support 'codeset_name in codesets' syntax."""
        return codeset_name in self.root
        
    def __getitem__(self, codeset_name: str) -> CodeSet:
        """Support codesets['name'] syntax."""
        return self.root[codeset_name]
        
    def keys(self) -> Iterator[str]:
        """Get all codeset names."""
        return iter(self.root.keys())
        
    def values(self) -> Iterator[CodeSet]:
        """Get all codesets."""
        return iter(self.root.values())
        
    def items(self) -> Iterator[tuple[str, CodeSet]]:
        """Get all (name, codeset) pairs."""
        return iter(self.root.items())
        
    def __len__(self) -> int:
        """Return the number of codesets."""
        return len(self.root)
    