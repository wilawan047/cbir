import numpy as np
import torch
from PIL import Image
import torchvision.models as models
import torchvision.transforms as transforms
import os

# Paths
FEATURES_FILE = 'static/features/house_features.npy'
FILENAMES_FILE = 'static/features/filenames.npy'

# Load pre-trained ResNet18 model (remove last layer)
model = models.resnet18(pretrained=True)
model = torch.nn.Sequential(*(list(model.children())[:-1]))
model.eval()

# Image transformations
transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

def extract_feature(image_path):
    image = Image.open(image_path).convert('RGB')
    image = transform(image)
    image = image.unsqueeze(0)
    with torch.no_grad():
        features = model(image)
        features = features.squeeze()
        features = features / torch.norm(features)  # L2 normalization
        return features.numpy()

def search_similar_images(query_image_path, top_k=6):
    # Extract features for the query image
    query_feat = extract_feature(query_image_path)

    # Load database features and filenames
    db_features = np.load(FEATURES_FILE)
    db_filenames = np.load(FILENAMES_FILE)

    # Compute cosine similarity
    similarities = np.dot(db_features, query_feat) / (
        np.linalg.norm(db_features, axis=1) * np.linalg.norm(query_feat) + 1e-10
    )

    # Get top-k indices
    top_k_idx = np.argsort(similarities)[::-1][:top_k]
    results = []
    for idx in top_k_idx:
        results.append({
            'filename': db_filenames[idx],
            'similarity': float(similarities[idx])
        })
    return results 