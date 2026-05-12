import torch
import torchvision.transforms as transforms
import torchvision.models as models
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from PIL import Image
import pandas as pd
import os

# 디바이스 설정 (M1 MPS 가속)
device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
print(f"Using device: {device}")

# 이미지 전처리
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.Grayscale(num_output_channels=3),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225])
])

# 데이터셋 클래스
class XRayDataset(Dataset):
    def __init__(self, labels_csv, images_dir, transform=None):
        df = pd.read_csv(labels_csv)
        self.df = df.drop_duplicates(subset='patientId').reset_index(drop=True)
        self.images_dir = images_dir
        self.transform = transform

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        import pydicom
        import numpy as np
        row = self.df.iloc[idx]
        img_path = os.path.join(self.images_dir, row['patientId'] + '.dcm')
        dcm = pydicom.dcmread(img_path)
        img_array = dcm.pixel_array.astype(np.float32)
        img_array = (img_array / img_array.max() * 255).astype(np.uint8)
        image = Image.fromarray(img_array).convert('RGB')
        if self.transform:
            image = self.transform(image)
        label = int(row['Target'])
        return image, label

# 모델 설정
model = models.resnet50(weights='IMAGENET1K_V1')
model.fc = nn.Linear(model.fc.in_features, 2)
model = model.to(device)

print("모델 로드 완료!")
print(f"학습 파라미터 수: {sum(p.numel() for p in model.parameters()):,}")

# 데이터 로드
dataset = XRayDataset(
    labels_csv='stage_2_train_labels.csv',
    images_dir='stage_2_train_images',
    transform=transform
)

# 학습/검증 분할 (8:2)
train_size = int(0.8 * len(dataset))
val_size = len(dataset) - train_size
train_dataset, val_dataset = torch.utils.data.random_split(dataset, [train_size, val_size])

train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True, num_workers=0)
val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False, num_workers=0)

print(f"학습 데이터: {train_size}장")
print(f"검증 데이터: {val_size}장")

# 손실함수 & 옵티마이저
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.0001)

# 학습 루프
for epoch in range(5):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for i, (images, labels) in enumerate(train_loader):
        images, labels = images.to(device), labels.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item()
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()

        if i % 10 == 0:
            print(f"Epoch [{epoch+1}/5] Step [{i}/{len(train_loader)}] "
                  f"Loss: {running_loss/(i+1):.4f} "
                  f"Acc: {100.*correct/total:.2f}%")

    # 모델 저장
    torch.save(model.state_dict(), f'model_epoch_{epoch+1}.pth')
    print(f"Epoch {epoch+1} 완료! 모델 저장됨")