from typing import Dict, List, Optional

import pandas as pd

from feast.data_source import DataSource
from feast.repo_config import FeastConfigBaseModel
from feast_postgres import PostgreSQLOfflineStoreConfig, PostgreSQLSource
from feast_postgres.utils import _get_conn, df_to_postgres_table
from tests.integration.feature_repos.integration_test_repo_config import (
    IntegrationTestRepoConfig,
)
from tests.integration.feature_repos.universal.data_source_creator import (
    DataSourceCreator,
)


class PostgreSQLDataSourceCreator(DataSourceCreator):

    tables: List[str] = []

    def __init__(self, project_name: str):
        super().__init__()
        self.project_name = project_name

        self.offline_store_config = PostgreSQLOfflineStoreConfig(
            type="feast_postgres.PostgreSQLOfflineStore",
            host="localhost",
            port=5432,
            database="postgres",
            db_schema="public",
            user="postgres",
            password="postgres",
        )

    def create_data_source(
        self,
        df: pd.DataFrame,
        destination_name: str,
        suffix: Optional[str] = None,
        event_timestamp_column="ts",
        created_timestamp_column="created_ts",
        field_mapping: Dict[str, str] = None,
    ) -> DataSource:

        destination_name = self.get_prefixed_table_name(destination_name)

        df_to_postgres_table(self.offline_store_config, df, destination_name)

        self.tables.append(destination_name)

        return PostgreSQLSource(
            query=f"SELECT * FROM {destination_name}",
            event_timestamp_column=event_timestamp_column,
            created_timestamp_column=created_timestamp_column,
            field_mapping=field_mapping,
        )

    def create_offline_store_config(self) -> FeastConfigBaseModel:
        return self.offline_store_config

    def get_prefixed_table_name(self, suffix: str) -> str:
        return f"{self.project_name}_{suffix}"

    def teardown(self):
        pass
        with _get_conn(self.offline_store_config) as conn, conn.cursor() as cur:
            for table in self.tables:
                cur.execute("DROP TABLE IF EXISTS " + table)


POSTGRES_ONLINE_CONFIG = {
    "type": "feast_postgres.PostgreSQLOnlineStore",
    "host": "localhost",
    "port": "5432",
    "database": "postgres",
    "db_schema": "feature_store",
    "user": "postgres",
    "password": "postgres",
}

FULL_REPO_CONFIGS = [
    IntegrationTestRepoConfig(
        provider="local",
        offline_store_creator=PostgreSQLDataSourceCreator,
        online_store=POSTGRES_ONLINE_CONFIG,
    ),
]
