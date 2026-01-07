from __future__ import annotations

import uuid
from typing import Dict, List, Optional

from fastapi import Body, Query, Request
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.background import BackgroundTask
from starlette.responses import Response

from src.app_config import app
from src.check_return_type import check_response
from src.dependencies import (
    ProvisionServiceDep,
    ReverseProvisionServiceDep,
    UpdateAclServiceDep,
    get_account_client,
    settings,
)
from src.models.api_models import (
    ProvisioningStatus,
    RequestValidationError,
    ReverseProvisioningRequest,
    ReverseProvisioningStatus,
    SystemErr,
    ValidationError,
    ValidationRequest,
    ValidationResult,
    ValidationStatus,
)
from src.models.custom_url_picker_models import (
    PickerOption,
    PickerResourcesRequest,
    PickerValidationRequest,
    PickerValidationResponse,
)
from src.models.databricks.databricks_workspace_info import DatabricksWorkspaceInfo
from src.service.clients.databricks.unity_catalog_manager import UnityCatalogManager
from src.service.clients.databricks.workspace_manager import WorkspaceManager
from src.service.validation.validation_service import (
    ValidatedDatabricksComponentDep,
    ValidatedUpdateACLDatabricksComponentDep,
)


def log_info(req_body, res_code, res_body):
    id = str(uuid.uuid4())
    logger.info("[{}] REQUEST: {}", id, req_body.decode("utf-8"))
    logger.info("[{}] RESPONSE({}): {}", id, res_code, res_body.decode("utf-8"))


@app.middleware("http")
async def log_request_response_middleware(request: Request, call_next):
    req_body = await request.body()
    response = await call_next(request)
    chunks = []
    async for chunk in response.body_iterator:
        chunks.append(chunk)
    res_body = b"".join(chunks)
    task = BackgroundTask(log_info, req_body, response.status_code, res_body)
    return Response(
        content=res_body,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.media_type,
        background=task,
    )


@app.post(
    "/v1/provision",
    response_model=None,
    responses={
        "200": {"model": ProvisioningStatus},
        "202": {"model": str},
        "400": {"model": RequestValidationError},
        "500": {"model": SystemErr},
    },
    tags=["TechAdapter"],
)
async def provision(request: ValidatedDatabricksComponentDep, provision_service: ProvisionServiceDep) -> Response:
    """
    Deploy a data product or a single component starting from a provisioning descriptor
    """

    if isinstance(request, RequestValidationError):
        return check_response(out_response=request)

    data_product, component, remove_data = request

    logger.info("Provisioning component with id: {}", component)

    provisioning_response = provision_service.provision(data_product, component, remove_data)
    logger.info("Provisioning started. Response: {}", provisioning_response)

    return check_response(out_response=provisioning_response)


@app.get(
    "/v1/provision/{token}/status",
    response_model=None,
    responses={
        "200": {"model": ProvisioningStatus},
        "400": {"model": RequestValidationError},
        "500": {"model": SystemErr},
    },
    tags=["TechAdapter"],
)
def get_status(token: str, provision_service: ProvisionServiceDep) -> Response:
    """
    Get the status for a provisioning request
    """

    resp = provision_service.get_provisioning_status(token)

    return check_response(out_response=resp)


@app.post(
    "/v1/unprovision",
    response_model=None,
    responses={
        "200": {"model": ProvisioningStatus},
        "202": {"model": str},
        "400": {"model": RequestValidationError},
        "500": {"model": SystemErr},
    },
    tags=["TechAdapter"],
)
async def unprovision(request: ValidatedDatabricksComponentDep, provision_service: ProvisionServiceDep) -> Response:
    """
    Undeploy a data product or a single component
    given the provisioning descriptor relative to the latest complete provisioning request
    """  # noqa: E501

    if isinstance(request, RequestValidationError):
        return check_response(out_response=request)

    data_product, component, remove_data = request

    logger.info("Unprovisioning component with id: {}", component)

    provisioning_response = provision_service.unprovision(data_product, component, remove_data)
    logger.info("Unprovisioning started. Response: {}", provisioning_response)

    return check_response(out_response=provisioning_response)


@app.post(
    "/v1/updateacl",
    response_model=None,
    responses={
        "200": {"model": ProvisioningStatus},
        "202": {"model": str},
        "400": {"model": RequestValidationError},
        "500": {"model": SystemErr},
    },
    tags=["TechAdapter"],
)
def updateacl(request: ValidatedUpdateACLDatabricksComponentDep, update_acl_service: UpdateAclServiceDep) -> Response:
    """
    Request the access to a tech adapter component
    """

    if isinstance(request, RequestValidationError):
        return check_response(out_response=request)

    data_product, component, witboost_users = request

    resp = update_acl_service.update_acl(data_product, component, witboost_users)

    return check_response(out_response=resp)


@app.post(
    "/v1/validate",
    response_model=None,
    responses={"200": {"model": ValidationResult}, "500": {"model": SystemErr}},
    tags=["TechAdapter"],
)
def validate(request: ValidatedDatabricksComponentDep) -> Response:
    """
    Validate a provisioning request
    """

    if isinstance(request, RequestValidationError):
        return check_response(ValidationResult(valid=False, error=ValidationError(errors=request.errors)))

    return check_response(out_response=ValidationResult(valid=True))


@app.post(
    "/v2/validate",
    response_model=None,
    responses={
        "202": {"model": str},
        "400": {"model": ValidationError},
        "500": {"model": SystemErr},
    },
    tags=["TechAdapter"],
)
def async_validate(
    body: ValidationRequest,
) -> Response:
    """
    Validate a deployment request
    """

    # todo: define correct response. You can define your pydantic component type with the expected specific schema
    #  and use `.get_type_component_by_id` to extract it from the data product

    # componentToProvision = data_product.get_typed_component_by_id(component_id, MyTypedComponent)

    resp = SystemErr(error="Response not yet implemented")

    return check_response(out_response=resp)


@app.get(
    "/v2/validate/{token}/status",
    response_model=None,
    responses={
        "200": {"model": ValidationStatus},
        "400": {"model": ValidationError},
        "500": {"model": SystemErr},
    },
    tags=["TechAdapter"],
)
def get_validation_status(
    token: str,
) -> Response:
    """
    Get the status for a provisioning request
    """

    # todo: define correct response
    resp = SystemErr(error="Response not yet implemented")

    return check_response(out_response=resp)


@app.post(
    "/v1/reverse-provisioning",
    response_model=None,
    responses={
        "200": {"model": ReverseProvisioningStatus},
        "202": {"model": str},
        "400": {"model": RequestValidationError},
        "500": {"model": SystemErr},
    },
    tags=["SpecificProvisioner"],
)
def run_reverse_provisioning(
    body: ReverseProvisioningRequest, reverse_provision_service: ReverseProvisionServiceDep
) -> Response:
    """
    Execute a reverse provisioning operation
    """
    resp = reverse_provision_service.run_reverse_provisioning(body)

    return check_response(out_response=resp)


@app.get(
    "/v1/reverse-provisioning/{token}/status",
    response_model=None,
    responses={
        "200": {"model": ReverseProvisioningStatus},
        "400": {"model": RequestValidationError},
        "500": {"model": SystemErr},
    },
    tags=["SpecificProvisioner"],
)
def get_reverse_provisioning_status(
    token: str,
) -> Response:
    """
    Get status and results of a reverse provisioning operation
    """
    # todo: define correct response
    resp = SystemErr(error="Response not yet implemented")

    return check_response(out_response=resp)


# ============================================================================
# Custom URL Picker API Endpoints for Unity Catalog Resources
# ============================================================================


def _get_unity_catalog_manager(workspace_url: str) -> UnityCatalogManager:
    """Helper function to create Unity Catalog manager for a workspace."""
    from databricks.sdk import WorkspaceClient

    # Create workspace client with Azure authentication
    workspace_client = WorkspaceClient(
        auth_type="azure-client-secret",
        host=workspace_url,
        azure_tenant_id=settings.azure.auth.tenant_id,
        azure_client_id=settings.azure.auth.client_id,
        azure_client_secret=settings.azure.auth.client_secret,
    )
    workspace_info = DatabricksWorkspaceInfo(
        id="",  # Not needed for listing operations
        name=workspace_url,
        workspace_url=workspace_url,
    )
    return UnityCatalogManager(workspace_client, workspace_info)


def _get_workspace_manager(workspace_url: str) -> WorkspaceManager:
    """Helper function to create Workspace manager for a workspace."""
    from databricks.sdk import WorkspaceClient

    # Create workspace client with Azure authentication
    workspace_client = WorkspaceClient(
        auth_type="azure-client-secret",
        host=workspace_url,
        azure_tenant_id=settings.azure.auth.tenant_id,
        azure_client_id=settings.azure.auth.client_id,
        azure_client_secret=settings.azure.auth.client_secret,
    )
    account_client = get_account_client(settings)
    return WorkspaceManager(workspace_client, account_client)


@app.post(
    "/custom-url-picker/v1/catalogs",
    response_model=List[PickerOption],
    responses={
        "200": {"model": List[PickerOption]},
        "500": {"model": SystemErr},
    },
    tags=["CustomUrlPicker"],
)
def list_catalogs_picker(
    filter: str = Query("", description="Optional filter text for catalog names"),
    offset: int = Query(0, description="Pagination offset"),
    limit: int = Query(50, description="Maximum number of results"),
    body: Dict = Body(default={}),
) -> JSONResponse:
    """
    List available Unity Catalog catalogs for Custom URL Picker dropdown.

    Args:
        filter: Optional filter text for catalog names
        offset: Pagination offset
        limit: Maximum number of results
        body: Request body containing queryParameters like workspace_url
    """
    try:
        # Debug logging
        logger.info("Received request - filter: {}, offset: {}, limit: {}, body: {}", filter, offset, limit, body)

        # Extract workspace_url from body or queryParameters
        query_params = body.get("queryParameters", {}) if body else {}
        workspace_url = query_params.get("workspace_url")

        logger.info("Extracted workspace_url: {}", workspace_url)

        if not workspace_url:
            logger.error("Missing workspace_url in request")
            return JSONResponse(
                status_code=400,
                content={"error": "workspace_url is required in queryParameters"}
            )

        uc_manager = _get_unity_catalog_manager(workspace_url)
        catalog_names = uc_manager.list_catalogs(filter_text=filter if filter else None)

        logger.info("Found {} catalogs", len(catalog_names))

        # Apply pagination
        paginated = catalog_names[offset : offset + limit]

        options = [
            {
                "id": name,
                "value": name,
                "description": f"Unity Catalog: {name}",
            }
            for name in paginated
        ]

        logger.info("Returning {} options: {}", len(options), options)

        # Return as JSON array directly
        return JSONResponse(
            status_code=200,
            content=options,
            headers={"Content-Type": "application/json"}
        )
    except Exception as e:
        logger.error("Error listing catalogs: {}", e)
        import traceback
        logger.error("Traceback: {}", traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.post(
    "/custom-url-picker/v1/schemas",
    response_model=List[PickerOption],
    responses={
        "200": {"model": List[PickerOption]},
        "500": {"model": SystemErr},
    },
    tags=["CustomUrlPicker"],
)
def list_schemas_picker(
    filter: str = Query("", description="Optional filter text for schema names"),
    offset: int = Query(0, description="Pagination offset"),
    limit: int = Query(50, description="Maximum number of results"),
    body: Dict = Body(default={}),
) -> JSONResponse:
    """
    List available schemas in a catalog for Custom URL Picker dropdown.

    Args:
        filter: Optional filter text for schema names
        offset: Pagination offset
        limit: Maximum number of results
        body: Request body containing queryParameters like workspace_url and catalog_name
    """
    try:
        # Extract parameters from body
        query_params = body.get("queryParameters", {}) if body else {}
        workspace_url = query_params.get("workspace_url")
        catalog_name = query_params.get("catalog_name")

        if not workspace_url or not catalog_name:
            logger.error("Missing required parameters: workspace_url={}, catalog_name={}", workspace_url, catalog_name)
            return JSONResponse(
                status_code=400,
                content={"error": "workspace_url and catalog_name are required in queryParameters"}
            )

        uc_manager = _get_unity_catalog_manager(workspace_url)
        schema_names = uc_manager.list_schemas(
            catalog_name=catalog_name, filter_text=filter if filter else None
        )

        # Apply pagination
        paginated = schema_names[offset : offset + limit]

        options = [
            {
                "id": name,
                "value": name,
                "description": f"Schema in {catalog_name}: {name}",
            }
            for name in paginated
        ]

        return JSONResponse(content=options)
    except Exception as e:
        logger.error("Error listing schemas: {}", e)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.post(
    "/custom-url-picker/v1/tables",
    response_model=List[PickerOption],
    responses={
        "200": {"model": List[PickerOption]},
        "500": {"model": SystemErr},
    },
    tags=["CustomUrlPicker"],
)
def list_tables_picker(
    filter: str = Query("", description="Optional filter text for table names"),
    offset: int = Query(0, description="Pagination offset"),
    limit: int = Query(50, description="Maximum number of results"),
    body: Dict = Body(default={}),
) -> JSONResponse:
    """
    List available tables in a schema for Custom URL Picker dropdown.

    Args:
        filter: Optional filter text for table names
        offset: Pagination offset
        limit: Maximum number of results
        body: Request body containing queryParameters like workspace_url, catalog_name, and schema_name
    """
    try:
        # Extract parameters from body
        query_params = body.get("queryParameters", {}) if body else {}
        workspace_url = query_params.get("workspace_url")
        catalog_name = query_params.get("catalog_name")
        schema_name = query_params.get("schema_name")

        if not workspace_url or not catalog_name or not schema_name:
            logger.error(
                "Missing required parameters: workspace_url={}, catalog_name={}, schema_name={}",
                workspace_url, catalog_name, schema_name
            )
            return JSONResponse(
                status_code=400,
                content={"error": "workspace_url, catalog_name, and schema_name are required in queryParameters"}
            )

        uc_manager = _get_unity_catalog_manager(workspace_url)
        table_names = uc_manager.list_tables(
            catalog_name=catalog_name,
            schema_name=schema_name,
            filter_text=filter if filter else None,
        )

        # Apply pagination
        paginated = table_names[offset : offset + limit]

        options = [
            {
                "id": name,
                "value": name,
                "description": f"Table in {catalog_name}.{schema_name}: {name}",
            }
            for name in paginated
        ]

        return JSONResponse(content=options)
    except Exception as e:
        logger.error("Error listing tables: {}", e)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.post(
    "/custom-url-picker/v1/warehouses",
    response_model=List[PickerOption],
    responses={
        "200": {"model": List[PickerOption]},
        "500": {"model": SystemErr},
    },
    tags=["CustomUrlPicker"],
)
def list_warehouses_picker(
    filter: str = Query("", description="Optional filter text for warehouse names"),
    offset: int = Query(0, description="Pagination offset"),
    limit: int = Query(50, description="Maximum number of results"),
    body: Dict = Body(default={}),
) -> JSONResponse:
    """
    List available SQL warehouses for Custom URL Picker dropdown.

    Args:
        filter: Optional filter text for warehouse names
        offset: Pagination offset
        limit: Maximum number of results
        body: Request body containing queryParameters like workspace_url
    """
    try:
        # Extract parameters from body
        query_params = body.get("queryParameters", {}) if body else {}
        workspace_url = query_params.get("workspace_url")

        if not workspace_url:
            logger.error("Missing workspace_url in request")
            return JSONResponse(
                status_code=400,
                content={"error": "workspace_url is required in queryParameters"}
            )

        ws_manager = _get_workspace_manager(workspace_url)
        warehouses = ws_manager.list_warehouses()

        warehouse_names = [wh.name for wh in warehouses if wh.name]

        # Apply filter
        if filter:
            filter_lower = filter.lower()
            warehouse_names = [name for name in warehouse_names if filter_lower in name.lower()]

        warehouse_names = sorted(warehouse_names)

        # Apply pagination
        paginated = warehouse_names[offset : offset + limit]

        options = [
            {
                "id": name,
                "value": name,
                "description": f"SQL Warehouse: {name}",
            }
            for name in paginated
        ]

        return JSONResponse(content=options)
    except Exception as e:
        logger.error("Error listing warehouses: {}", e)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )
