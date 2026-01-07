from __future__ import annotations

from typing import List, Optional

from loguru import logger

from src.models.custom_url_picker_models import PickerOption
from src.service.clients.databricks.unity_catalog_manager import UnityCatalogManager
from src.service.clients.databricks.workspace_manager import WorkspaceManager


class CustomUrlPickerService:
    """
    Service for providing Unity Catalog resources to Custom URL Picker fields.
    """

    def __init__(self, unity_catalog_manager: UnityCatalogManager, workspace_manager: WorkspaceManager):
        self.unity_catalog_manager = unity_catalog_manager
        self.workspace_manager = workspace_manager

    def get_catalogs(
        self, filter_text: Optional[str] = None, offset: int = 0, limit: int = 50
    ) -> List[PickerOption]:
        """
        Retrieve available Unity Catalog catalogs as picker options.

        Args:
            filter_text: Optional text to filter catalog names.
            offset: Number of results to skip (pagination).
            limit: Maximum number of results to return.

        Returns:
            List of PickerOption objects representing available catalogs.
        """
        try:
            logger.info("Fetching catalogs for Custom URL Picker (filter='{}', offset={}, limit={})",
                       filter_text, offset, limit)

            catalog_names = self.unity_catalog_manager.list_catalogs(filter_text=filter_text)

            # Apply pagination
            paginated_catalogs = catalog_names[offset : offset + limit]

            options = [
                PickerOption(
                    id=catalog_name,
                    value=catalog_name,
                    description=f"Unity Catalog: {catalog_name}",
                )
                for catalog_name in paginated_catalogs
            ]

            logger.info("Returning {} catalog options out of {} total", len(options), len(catalog_names))
            return options
        except Exception as e:
            logger.error("Error fetching catalogs for Custom URL Picker: {}", e)
            raise

    def get_schemas(
        self, catalog_name: str, filter_text: Optional[str] = None, offset: int = 0, limit: int = 50
    ) -> List[PickerOption]:
        """
        Retrieve available schemas within a catalog as picker options.

        Args:
            catalog_name: The parent catalog name.
            filter_text: Optional text to filter schema names.
            offset: Number of results to skip (pagination).
            limit: Maximum number of results to return.

        Returns:
            List of PickerOption objects representing available schemas.
        """
        try:
            logger.info("Fetching schemas for catalog '{}' (filter='{}', offset={}, limit={})",
                       catalog_name, filter_text, offset, limit)

            schema_names = self.unity_catalog_manager.list_schemas(
                catalog_name=catalog_name, filter_text=filter_text
            )

            # Apply pagination
            paginated_schemas = schema_names[offset : offset + limit]

            options = [
                PickerOption(
                    id=schema_name,
                    value=schema_name,
                    description=f"Schema in {catalog_name}: {schema_name}",
                )
                for schema_name in paginated_schemas
            ]

            logger.info("Returning {} schema options out of {} total", len(options), len(schema_names))
            return options
        except Exception as e:
            logger.error("Error fetching schemas for Custom URL Picker: {}", e)
            raise

    def get_tables(
        self,
        catalog_name: str,
        schema_name: str,
        filter_text: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> List[PickerOption]:
        """
        Retrieve available tables within a schema as picker options.

        Args:
            catalog_name: The parent catalog name.
            schema_name: The parent schema name.
            filter_text: Optional text to filter table names.
            offset: Number of results to skip (pagination).
            limit: Maximum number of results to return.

        Returns:
            List of PickerOption objects representing available tables.
        """
        try:
            logger.info(
                "Fetching tables for schema '{}.{}' (filter='{}', offset={}, limit={})",
                catalog_name,
                schema_name,
                filter_text,
                offset,
                limit,
            )

            table_names = self.unity_catalog_manager.list_tables(
                catalog_name=catalog_name, schema_name=schema_name, filter_text=filter_text
            )

            # Apply pagination
            paginated_tables = table_names[offset : offset + limit]

            options = [
                PickerOption(
                    id=table_name,
                    value=table_name,
                    description=f"Table in {catalog_name}.{schema_name}: {table_name}",
                )
                for table_name in paginated_tables
            ]

            logger.info("Returning {} table options out of {} total", len(options), len(table_names))
            return options
        except Exception as e:
            logger.error("Error fetching tables for Custom URL Picker: {}", e)
            raise

    def get_sql_warehouses(
        self, filter_text: Optional[str] = None, offset: int = 0, limit: int = 50
    ) -> List[PickerOption]:
        """
        Retrieve available SQL warehouses as picker options.

        Args:
            filter_text: Optional text to filter warehouse names.
            offset: Number of results to skip (pagination).
            limit: Maximum number of results to return.

        Returns:
            List of PickerOption objects representing available SQL warehouses.
        """
        try:
            logger.info("Fetching SQL warehouses (filter='{}', offset={}, limit={})",
                       filter_text, offset, limit)

            warehouses = self.workspace_manager.list_warehouses()

            warehouse_names = [wh.name for wh in warehouses if wh.name]

            # Apply filter if provided
            if filter_text:
                filter_lower = filter_text.lower()
                warehouse_names = [name for name in warehouse_names if filter_lower in name.lower()]

            warehouse_names = sorted(warehouse_names)

            # Apply pagination
            paginated_warehouses = warehouse_names[offset : offset + limit]

            options = [
                PickerOption(
                    id=warehouse_name,
                    value=warehouse_name,
                    description=f"SQL Warehouse: {warehouse_name}",
                )
                for warehouse_name in paginated_warehouses
            ]

            logger.info("Returning {} SQL warehouse options out of {} total", len(options), len(warehouse_names))
            return options
        except Exception as e:
            logger.error("Error fetching SQL warehouses for Custom URL Picker: {}", e)
            raise

    def validate_catalog(self, catalog_name: str) -> bool:
        """
        Validate that a catalog exists.

        Args:
            catalog_name: The catalog name to validate.

        Returns:
            True if the catalog exists, False otherwise.
        """
        try:
            return self.unity_catalog_manager.check_catalog_existence(catalog_name)
        except Exception as e:
            logger.error("Error validating catalog '{}': {}", catalog_name, e)
            return False

    def validate_schema(self, catalog_name: str, schema_name: str) -> bool:
        """
        Validate that a schema exists within a catalog.

        Args:
            catalog_name: The parent catalog name.
            schema_name: The schema name to validate.

        Returns:
            True if the schema exists, False otherwise.
        """
        try:
            return self.unity_catalog_manager.check_schema_existence(catalog_name, schema_name)
        except Exception as e:
            logger.error("Error validating schema '{}.{}': {}", catalog_name, schema_name, e)
            return False

    def validate_table(self, catalog_name: str, schema_name: str, table_name: str) -> bool:
        """
        Validate that a table exists within a schema.

        Args:
            catalog_name: The parent catalog name.
            schema_name: The parent schema name.
            table_name: The table name to validate.

        Returns:
            True if the table exists, False otherwise.
        """
        try:
            return self.unity_catalog_manager.check_table_existence(catalog_name, schema_name, table_name)
        except Exception as e:
            logger.error("Error validating table '{}.{}.{}': {}", catalog_name, schema_name, table_name, e)
            return False
