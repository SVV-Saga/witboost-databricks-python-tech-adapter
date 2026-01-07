from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PickerOption(BaseModel):
    """Response model for a single picker option"""

    id: str = Field(..., description="Unique identifier for the option")
    value: str = Field(..., description="Display value shown to the user")
    description: Optional[str] = Field(
        None, description="Optional description for the option"
    )


class PickerResourcesRequest(BaseModel):
    """Request model for Custom URL Picker resources endpoint"""

    queryParameters: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional parameters for filtering"
    )


class PickerValidationRequest(BaseModel):
    """Request model for validating picker selections"""

    selectedObjects: List[str] = Field(..., description="List of selected option IDs")
    queryParameters: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional context for validation"
    )


class PickerValidationResponse(BaseModel):
    """Response model for picker validation"""

    valid: bool = Field(..., description="Whether the selection is valid")
    errors: Optional[List[str]] = Field(
        default=None, description="List of validation errors if invalid"
    )
