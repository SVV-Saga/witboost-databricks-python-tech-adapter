# Unity Catalog Dynamic Dropdowns Implementation

## Overview
This implementation adds dynamic dropdown fields to the Witboost Databricks Data Contract template, allowing users to select Unity Catalog resources (catalogs, schemas, tables) and SQL warehouses from live data instead of free-text input.

## Files Modified

### Tech Adapter (`witboost-databricks-python-tech-adapter`)

#### 1. **src/models/custom_url_picker_models.py** (NEW)
- Added Pydantic models for Custom URL Picker API
- `PickerOption`: Response format for dropdown options
- `PickerResourcesRequest`, `PickerValidationRequest`, `PickerValidationResponse`: Request/response models

#### 2. **src/service/clients/databricks/unity_catalog_manager.py**
Added three new methods for listing Unity Catalog resources:
- `list_catalogs(filter_text)`: Lists all catalogs with optional filtering
- `list_schemas(catalog_name, filter_text)`: Lists schemas in a catalog
- `list_tables(catalog_name, schema_name, filter_text)`: Lists tables in a schema

#### 3. **src/service/clients/databricks/workspace_manager.py**
Added method:
- `list_warehouses()`: Lists all SQL warehouses in the workspace

#### 4. **src/service/custom_url_picker_service.py** (NEW - Not Used)
Created but not actively used. The endpoints in main.py directly use managers.

#### 5. **src/main.py**
Added Custom URL Picker API endpoints:
- `POST /custom-url-picker/v1/catalogs`: List Unity Catalog catalogs
- `POST /custom-url-picker/v1/schemas`: List schemas (requires catalog)
- `POST /custom-url-picker/v1/tables`: List tables (requires catalog + schema)
- `POST /custom-url-picker/v1/warehouses`: List SQL warehouses

Helper functions:
- `_get_unity_catalog_manager(workspace_url)`: Creates authenticated Unity Catalog manager
- `_get_workspace_manager(workspace_url)`: Creates authenticated Workspace manager

### Template Files (`witboost-databricks-data-contract-template`)

#### 1. **template.yaml** (lines 102-141)
Updated fields to use `CustomUrlPicker`:
- `catalogName`: Source Catalog Name
- `schemaName`: Source Schema Name (depends on catalogName)
- `tableName`: Source Table Name (depends on catalogName + schemaName)
- `sqlWarehouseName`: SQL Warehouse Name

#### 2. **edit-template.yaml** (lines 112-151)
Same fields updated with cascading dependencies using `{{workspaceOP}}` for workspace URL.

## API Specification

### Request Format
```json
POST /custom-url-picker/v1/catalogs?filter=&offset=0&limit=50
{
  "queryParameters": {
    "workspace_url": "https://adb-xxxxx.azuredatabricks.net"
  }
}
```

### Response Format
```json
[
  {
    "id": "catalog_name",
    "value": "catalog_name",
    "description": "Unity Catalog: catalog_name"
  }
]
```

## Authentication
All endpoints use Azure Client Secret authentication configured in the tech adapter settings:
- `azure_tenant_id`
- `azure_client_id`
- `azure_client_secret`

## CORS Configuration
The tech adapter includes CORS middleware to allow the Witboost UI (running on a different origin) to call the Custom URL Picker API endpoints. This is configured in `src/app_config.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to Witboost UI origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Deployment Instructions

### 1. Build Docker Image
```bash
cd /Users/evanjaasund/Documents/GitHub/witboost-databricks-python-tech-adapter

docker build -t crsvvsagamgmtprodswec001.azurecr.io/python-databricks-tech-adapter:latest \
  -f helm/Dockerfile .
```

### 2. Push to Registry
```bash
az acr login --name crsvvsagamgmtprodswec001
docker push crsvvsagamgmtprodswec001.azurecr.io/python-databricks-tech-adapter:latest
```

### 3. Deploy to Kubernetes
```bash
# Restart deployment to pull new image
kubectl rollout restart deployment/python-databricks-tech-adapter -n witboost

# Watch rollout status
kubectl rollout status deployment/python-databricks-tech-adapter -n witboost

# Verify pod is running
kubectl get pods -n witboost | grep databricks-tech-adapter
```

### 4. Update Templates
Commit and push the template changes to trigger Witboost to reload them:
```bash
cd /Users/evanjaasund/Documents/GitHub/witboost-databricks-data-contract-template
git add template.yaml edit-template.yaml
git commit -m "Add Unity Catalog dynamic dropdowns"
git push
```

## Testing

### Test API Endpoints
```bash
# Port forward
kubectl port-forward -n witboost svc/python-databricks-tech-adapter 5002:5002 &

# Test catalogs endpoint
curl -X POST "http://localhost:5002/custom-url-picker/v1/catalogs" \
  -H "Content-Type: application/json" \
  -d '{
    "queryParameters": {
      "workspace_url": "https://adb-7405616815694592.12.azuredatabricks.net"
    }
  }'

# Test schemas endpoint
curl -X POST "http://localhost:5002/custom-url-picker/v1/schemas" \
  -H "Content-Type: application/json" \
  -d '{
    "queryParameters": {
      "workspace_url": "https://adb-7405616815694592.12.azuredatabricks.net",
      "catalog_name": "your_catalog"
    }
  }'
```

### Test in Witboost UI
1. Navigate to Witboost marketplace
2. Select "Databricks Data Contract Template"
3. Fill initial fields (domain, data product, etc.)
4. In "Databricks Configuration" section:
   - **Source Catalog Name** should show dropdown with Unity Catalogs
   - **Source Schema Name** should populate after selecting catalog
   - **Source Table Name** should populate after selecting schema
   - **SQL Warehouse Name** should show available warehouses

## Features

### Cascading Dropdowns
- Schema dropdown only activates after catalog selection
- Table dropdown only activates after schema selection
- Each dropdown filters based on parent selections

### Search/Filter
All dropdowns support search functionality to filter results

### Error Handling
- Returns 400 if required parameters are missing
- Returns 500 with error message if Unity Catalog query fails
- Logs detailed errors for debugging

## Benefits

✅ **Prevents typos**: Users can only select existing resources
✅ **Faster workflow**: No need to look up exact names
✅ **Reduced errors**: Invalid combinations prevented
✅ **Better UX**: Searchable dropdowns with descriptions
✅ **Live data**: Dropdowns reflect current Unity Catalog state

## Troubleshooting

### Error: "default auth: cannot configure default credentials"
**Cause**: WorkspaceClient created without authentication
**Solution**: Ensure helper functions use `auth_type="azure-client-secret"`

### Error: "ae.map is not a function" in UI
**Cause**: CORS blocking requests from Witboost UI, or API returning wrong format
**Solution**:
1. **Most common**: Add CORS middleware to FastAPI app (see CORS Configuration section)
2. Check browser DevTools Network tab to see if requests are blocked by CORS policy
3. Verify endpoints return `JSONResponse(content=options)` where options is a list
4. Ensure `techadapterUrl` variable is configured in Witboost settings

### Error: Validation errors for DatabricksWorkspaceInfo
**Cause**: Using constructor instead of factory method
**Solution**: Use `DatabricksWorkspaceInfo.build_unmanaged()`

### Dropdowns not showing
**Cause**: Tech adapter not redeployed with new code
**Solution**: Rebuild Docker image and restart Kubernetes deployment
