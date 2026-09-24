from pydantic import BaseModel, Field
from typing import List, Dict, Any


class FunctionSignature(BaseModel):
    name: str = Field(..., description="Name of the function/method")
    parameters: List[Dict[str, str]
                     ] = Field(..., description="List of parameters with name and type")
    return_type: str = Field(..., description="Return type")
    description: str = Field(..., description="What this function does")


class ClassDefinition(BaseModel):
    name: str = Field(..., description="Class name")
    methods: List[FunctionSignature] = Field(...,
                                             description="Methods in this class")
    attributes: List[Dict[str, str]] = Field(
        default=[], description="Class attributes with types")
    description: str = Field(..., description="Class purpose")


class FileDefinition(BaseModel):
    filename: str = Field(..., description="e.g., 'load_predictor.py'")
    classes: List[ClassDefinition] = Field(
        default=[], description="Classes in this file")
    functions: List[FunctionSignature] = Field(
        default=[], description="Standalone functions")
    imports: List[str] = Field(default=[], description="Required imports")
    description: str = Field(..., description="File purpose")


class ArchitectOutput(BaseModel):
    files: List[FileDefinition] = Field(...,
                                        description="All files to generate")
    dependencies: Dict[str, List[str]
                       ] = Field(..., description="File dependencies")
    configuration: Dict[str,
                        Any] = Field(..., description="Key parameters from paper")
    algorithm_flow: List[str] = Field(...,
                                      description="Step-by-step algorithm flow")
