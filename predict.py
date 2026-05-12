import torch
import torchvision.transforms as transforms
import torchvision.models as models
import torch.nn as nn
from PIL import Image
import pydicom
import numpy as np
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import io

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# 디바이스 설정
device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

# 모델 로드
model = models.resnet50(weights=None)
model.fc = nn.Linear(model.fc.in_features, 2)
model.load_state_dict(torch.load('model_epoch_5.pth', map_location=device))
model = model.to(device)
model.eval()

# 이미지 전처리
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.Grayscale(num_output_channels=3),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225])
])

def load_image(file_bytes: bytes) -> Image.Image:
    try:
        dcm = pydicom.dcmread(io.BytesIO(file_bytes))
        img_array = dcm.pixel_array.astype(np.float32)
        img_array = (img_array / img_array.max() * 255).astype(np.uint8)
        return Image.fromarray(img_array).convert('RGB')
    except:
        return Image.open(io.BytesIO(file_bytes)).convert('RGB')

@app.get("/")
def root():
    return FileResponse("static/index.html")

@app.post("/preview")
async def preview(file: UploadFile = File(...)):
    import base64
    file_bytes = await file.read()
    image = load_image(file_bytes)
    image = image.resize((512, 512))
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode()
    return {"image": f"data:image/png;base64,{img_base64}"}

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    file_bytes = await file.read()
    image = load_image(file_bytes)
    tensor = transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        outputs = model(tensor)
        probs = torch.softmax(outputs, dim=1)
        confidence = probs[0][1].item()
        predicted = outputs.argmax(1).item()

    normal_prob = probs[0][0].item()
    abnormal_prob = probs[0][1].item()

    return {
        "result": "ABNORMAL" if predicted == 1 else "NORMAL",
        "confidence": round(abnormal_prob * 100, 2) if predicted == 1 else round(normal_prob * 100, 2),
        "message": "폐렴 의심" if predicted == 1 else "정상"
    }