import asyncio
from app.services.model_loader import get_model_loader
import numpy as np
from PIL import Image
import io

def test_predict():
    loader = get_model_loader()
    print("Transforms:", loader.transforms)
    print("Model:", type(loader.model))
    
    # create dummy images
    dummy_img = Image.new('RGB', (224, 224), color = 'red')
    buf = io.BytesIO()
    dummy_img.save(buf, format='PNG')
    dummy_bytes = buf.getvalue()
    
    try:
        res = loader.predict(dummy_bytes, dummy_bytes)
        print("Success:", res)
    except Exception as e:
        import traceback
        traceback.print_exc()

test_predict()
