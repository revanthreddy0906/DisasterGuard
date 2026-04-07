from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import endpoints
from app.services.model_loader import get_model_loader

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)
app.include_router(endpoints.router, prefix='/api/v1', tags=['prediction'])
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])

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
