from typing import Optional
from fastapi_filter.contrib.sqlalchemy import Filter

from app.models.log import Log


class LogFilter(Filter):
    class Constants(Filter.Constants):
        model = Log
        ordering_field_name = "created_at"