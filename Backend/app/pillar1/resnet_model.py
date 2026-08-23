import torch
import torch.nn as nn
import torch.nn.functional as F
# pyrefly: ignore [missing-import]
import torchvision.transforms as transforms
from PIL import Image
import os
from pathlib import Path

# Base class for the model
class ImageClassificationBase(nn.Module):
    def training_step(self, batch):
        images, labels = batch
        out = self(images)                  # Generate predictions
        loss = F.cross_entropy(out, labels) # Calculate loss
        return loss
    
    def validation_step(self, batch):
        images, labels = batch
        out = self(images)                   # Generate prediction
        loss = F.cross_entropy(out, labels)  # Calculate loss
        _, preds = torch.max(out, dim=1)
        acc = torch.tensor(torch.sum(preds == labels).item() / len(preds))
        return {"val_loss": loss.detach(), "val_accuracy": acc}
    
    def validation_epoch_end(self, outputs):
        batch_losses = [x["val_loss"] for x in outputs]
        batch_accuracy = [x["val_accuracy"] for x in outputs]
        epoch_loss = torch.stack(batch_losses).mean()       # Combine loss  
        epoch_accuracy = torch.stack(batch_accuracy).mean()
        return {"val_loss": epoch_loss, "val_accuracy": epoch_accuracy} # Combine accuracies
    
    def epoch_end(self, epoch, result):
        pass

# Convolution block with BatchNormalization
def ConvBlock(in_channels, out_channels, pool=False):
    layers = [nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
             nn.BatchNorm2d(out_channels),
             nn.ReLU(inplace=True)]
    if pool:
        layers.append(nn.MaxPool2d(4))
    return nn.Sequential(*layers)

# ResNet architecture 
class ResNet9(ImageClassificationBase):
    def __init__(self, in_channels, num_diseases):
        super().__init__()
        
        self.conv1 = ConvBlock(in_channels, 64)
        self.conv2 = ConvBlock(64, 128, pool=True) # out_dim : 128 x 64 x 64 
        self.res1 = nn.Sequential(ConvBlock(128, 128), ConvBlock(128, 128))
        
        self.conv3 = ConvBlock(128, 256, pool=True) # out_dim : 256 x 16 x 16
        self.conv4 = ConvBlock(256, 512, pool=True) # out_dim : 512 x 4 x 44
        self.res2 = nn.Sequential(ConvBlock(512, 512), ConvBlock(512, 512))
        
        self.classifier = nn.Sequential(nn.MaxPool2d(4),
                                       nn.Flatten(),
                                       nn.Linear(512, num_diseases))
        
    def forward(self, xb): # xb is the loaded batch
        out = self.conv1(xb)
        out = self.conv2(out)
        out = self.res1(out) + out
        out = self.conv3(out)
        out = self.conv4(out)
        out = self.res2(out) + out
        out = self.classifier(out)
        return out        

# Disease Classes from the notebook
DISEASES = [
    'Tomato___Late_blight', 'Tomato___healthy', 'Grape___healthy', 
    'Orange___Haunglongbing_(Citrus_greening)', 'Soybean___healthy', 
    'Squash___Powdery_mildew', 'Potato___healthy', 'Corn_(maize)___Northern_Leaf_Blight', 
    'Tomato___Early_blight', 'Tomato___Septoria_leaf_spot', 
    'Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot', 'Strawberry___Leaf_scorch', 
    'Peach___healthy', 'Apple___Apple_scab', 'Tomato___Tomato_Yellow_Leaf_Curl_Virus', 
    'Tomato___Bacterial_spot', 'Apple___Black_rot', 'Blueberry___healthy', 
    'Cherry_(including_sour)___Powdery_mildew', 'Peach___Bacterial_spot', 
    'Apple___Cedar_apple_rust', 'Tomato___Target_Spot', 'Pepper,_bell___healthy', 
    'Grape___Leaf_blight_(Isariopsis_Leaf_Spot)', 'Potato___Late_blight', 
    'Tomato___Tomato_mosaic_virus', 'Strawberry___healthy', 'Apple___healthy', 
    'Grape___Black_rot', 'Potato___Early_blight', 'Cherry_(including_sour)___healthy', 
    'Corn_(maize)___Common_rust_', 'Grape___Esca_(Black_Measles)', 'Raspberry___healthy', 
    'Tomato___Leaf_Mold', 'Tomato___Spider_mites Two-spotted_spider_mite', 
    'Pepper,_bell___Bacterial_spot', 'Corn_(maize)___healthy'
]

# Note: ImageFolder sorts classes alphabetically. We must use alphabetical order.
DISEASES.sort()

# Global Model Instance
_MODEL = None
_DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def get_resnet_model():
    global _MODEL
    if _MODEL is not None:
        return _MODEL
        
    model_path = Path(__file__).resolve().parent.parent.parent / "data" / "plant-disease-model.pth"
    if not model_path.exists():
        return None # Model weights not found, fallback to Gemini
        
    try:
        model = ResNet9(3, len(DISEASES))
        model.load_state_dict(torch.load(str(model_path), map_location=_DEVICE))
        model.to(_DEVICE)
        model.eval()
        _MODEL = model
        return _MODEL
    except Exception as e:
        print(f"Error loading ResNet9 model: {e}")
        return None

def predict_disease(image_path_or_bytes):
    """Predicts disease from an image using the local ResNet-9 PyTorch model."""
    model = get_resnet_model()
    if not model:
        return None
        
    try:
        from io import BytesIO
        if isinstance(image_path_or_bytes, bytes):
            image = Image.open(BytesIO(image_path_or_bytes)).convert("RGB")
        else:
            image = Image.open(image_path_or_bytes).convert("RGB")
            
        # The notebook dataset (PlantVillage) uses 256x256 images.
        transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.ToTensor()
        ])
        
        img_tensor = transform(image).unsqueeze(0).to(_DEVICE)
        
        with torch.no_grad():
            outputs = model(img_tensor)
            _, preds = torch.max(outputs, dim=1)
            predicted_class = DISEASES[preds[0].item()]
            
        return predicted_class
    except Exception as e:
        print(f"Error during ResNet9 prediction: {e}")
        return None
