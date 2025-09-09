import os
import numpy as np
from pathlib import Path
from PIL import Image
import torch
import torchvision.models as models
import torchvision.transforms as transforms

# Paths
IMAGE_FOLDER = 'static/uploads'
FEATURES_FOLDER = 'static/features'
FEATURES_FILE = os.path.join(FEATURES_FOLDER, 'house_features.npy')
FILENAMES_FILE = os.path.join(FEATURES_FOLDER, 'filenames.npy')

# Create features folder if it doesn't exist
os.makedirs(FEATURES_FOLDER, exist_ok=True)

# Load pre-trained ResNet18 model (remove last layer)
model = models.resnet18(pretrained=True)
model = torch.nn.Sequential(*(list(model.children())[:-1]))
model.eval()

def extract_feature(image_path, model, transform):
    image = Image.open(image_path).convert('RGB')
    image = transform(image)
    image = image.unsqueeze(0)
    with torch.no_grad():
        features = model(image)
        features = features.squeeze()
        features = features / torch.norm(features)  # L2 normalization
        return features.numpy()

# Image transformations
transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# Gather all image files
image_files = []
for ext in ['*.jpg', '*.jpeg', '*.png']:
    image_files.extend(Path(IMAGE_FOLDER).glob(ext))
image_files = sorted(image_files)

features = []
filenames = []

print(f"Extracting features from {len(image_files)} images...")
for img_path in image_files:
    try:
        feat = extract_feature(str(img_path), model, transform)
        features.append(feat)
        filenames.append(str(img_path.name))
        print(f"Processed: {img_path.name}")
    except Exception as e:
        print(f"Error processing {img_path}: {e}")

features = np.stack(features)
np.save(FEATURES_FILE, features)
np.save(FILENAMES_FILE, np.array(filenames))
print(f"Saved features to {FEATURES_FILE} and filenames to {FILENAMES_FILE}") 