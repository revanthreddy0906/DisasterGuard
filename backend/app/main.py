from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import endpoints

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)
app.include_router(endpoints.router, prefix='/api/v1', tags=['prediction'])
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])

@app.get('/')
def read_root():
    return {'message': f'Welcome to {settings.PROJECT_NAME}'}

@app.get('/health')
def health_check():
    return {'status': 'healthy', 'model_loaded': True}
