import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api import endpoints
from app.core.config import settings
from app.core.observability import RequestMetrics, configure_request_logger, log_request
from app.services.model_loader import get_model_loader

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)
app.include_router(endpoints.router, prefix='/api/v1', tags=['prediction'])
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])

request_metrics = RequestMetrics()
request_logger = configure_request_logger(settings.LOG_LEVEL)


@app.middleware('http')
async def request_observability_middleware(request: Request, call_next):
    request_id = request.headers.get(settings.REQUEST_ID_HEADER) or uuid.uuid4().hex
    request.state.request_id = request_id

    started_at = time.perf_counter()
    status_code = 500
    response = None

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        latency_ms = (time.perf_counter() - started_at) * 1000.0
        request_metrics.record_request(
            method=request.method,
            path=request.url.path,
            status_code=status_code,
            latency_ms=latency_ms,
        )
        if response is not None:
            response.headers[settings.REQUEST_ID_HEADER] = request_id
        log_request(
            request_logger,
            {
                'event': 'http_request',
                'request_id': request_id,
                'method': request.method,
                'path': request.url.path,
                'status_code': status_code,
                'latency_ms': round(latency_ms, 3),
                'client_ip': request.client.host if request.client else None,
            },
        )


@app.get('/')
def read_root():
    return {'message': f'Welcome to {settings.PROJECT_NAME}'}


@app.get('/health')
def health_check():
    model_error = None
    try:
        get_model_loader()
        model_loaded = True
    except Exception as exc:
        model_loaded = False
        model_error = str(exc)

    return {
        'status': 'healthy' if model_loaded else 'degraded',
        'model_loaded': model_loaded,
        'model_error': model_error,
        'device': settings.DEVICE,
    }


@app.get('/metrics')
def metrics():
    return {
        'request_metrics': request_metrics.snapshot(),
        'predict_metrics': endpoints.get_predict_metrics(),
    }
