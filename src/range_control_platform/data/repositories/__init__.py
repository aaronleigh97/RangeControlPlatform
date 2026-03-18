from range_control_platform.config import settings
from range_control_platform.data.repositories.in_memory_repo import (
    InMemoryReferenceDataRepository,
)
from range_control_platform.data.repositories.jd_bigquery_repo import (
    JDBigQueryReferenceDataRepository,
)


def build_reference_data_repository():
    if settings.ENV == "jd":
        return JDBigQueryReferenceDataRepository()
    return InMemoryReferenceDataRepository()
