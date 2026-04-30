from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator


def setup_metrics(app: FastAPI) -> None:
    Instrumentator().instrument(app).expose(
        app,
        include_in_schema=False,
        should_gzip=True,
        endpoint="/metrics",
    )
