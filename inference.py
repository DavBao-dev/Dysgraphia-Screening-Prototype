"""
inference.py - Chay inference that cho Model B (Model A la feature-extraction
thuan tuy, xem model_a_adapter.py).

Model B - kien truc thuc te suy ra tu chinh file weight ban dua (khong doan):
  state_dict co cac key: net.0 (Linear 2050->128), net.3 (Linear 128->32),
  net.5 (Linear 32->1). 2050 = 2048 (embedding tu ResNet50 pretrained
  ImageNet, bo lop fc cuoi) + 2 (feature thu cong: do day muc, chenh lech
  duong ke). Output 1 gia tri -> sigmoid -> xac suat lop duong tinh.
"""
import torch
import torch.nn as nn
from PIL import Image
from torchvision import models as tv_models
from torchvision import transforms

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ---------------------------------------------------------------------------
# MODEL B - ResNet50 embedding (backbone) + MLP head (weight ban dua)
# ---------------------------------------------------------------------------
class MLPHead(nn.Module):
    """
    Kien truc suy ra CHINH XAC tu state_dict cua ban (net.0 / net.3 / net.5).
    Neu load_state_dict o load_model_b_head() bao loi size mismatch, nghia la
    con so 2050 (dim dau vao) khong khop - kiem tra lai xem ban dung dung 2
    feature thu cong nao khi train (co the khac thu tu hoac khac cong thuc
    voi 2 feature trong models.py).
    """

    def __init__(self, in_dim: int = 2050, hidden1: int = 128, hidden2: int = 32):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, hidden1),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden1, hidden2),
            nn.ReLU(),
            nn.Linear(hidden2, 1),
        )

    def forward(self, x):
        return self.net(x)


def load_resnet50_backbone() -> nn.Module:
    """
    Backbone ResNet50 pretrained tren ImageNet (chuan, KHONG phai file weight
    ban upload - file ban upload chi la MLP head o tren). Bo lop fc cuoi,
    lay thang vector embedding 2048 chieu truoc do.
    """
    resnet = tv_models.resnet50(weights=tv_models.ResNet50_Weights.IMAGENET1K_V2)
    resnet.fc = nn.Identity()  # bo lop phan loai cuoi, giu lai embedding 2048-d
    resnet.to(DEVICE)
    resnet.eval()
    return resnet


def load_model_b_head(weight_path: str, in_dim: int = 2050) -> nn.Module:
    """Load dung file weight ban upload (MLP head, khong phai backbone)."""
    state_dict = torch.load(weight_path, map_location=DEVICE, weights_only=False)
    model = MLPHead(in_dim=in_dim)
    try:
        model.load_state_dict(state_dict)
    except Exception as e:
        raise RuntimeError(
            "Khong load duoc weight vao MLPHead. Kien truc trong inference.py "
            "duoc suy ra tu shape cua file .pt (net.0: 2050->128, net.3: "
            "128->32, net.5: 32->1). Neu ban thay doi kien truc luc train, "
            f"sua class MLPHead cho khop. Chi tiet loi goc: {e}"
        )
    model.to(DEVICE)
    model.eval()
    return model


_IMAGENET_TRANSFORM = transforms.Compose(
    [
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ]
)


def run_model_b(backbone: nn.Module, head: nn.Module, image_bytes: bytes, extra_features: list[float]):
    """
    1) Anh -> ResNet50 backbone -> embedding 2048-d.
    2) Ghep voi 2 feature thu cong (extra_features, DUNG THU TU nhu luc train).
    3) Dua qua MLP head -> sigmoid -> xac suat -> nguong 0.5 -> nhan 0/1.

    extra_features: list 2 gia tri, vi du [ink_thickness_mean, baseline_deviation].
    THU TU NAY PHAI KHOP CHINH XAC voi thu tu luc ban train MLP head, neu
    khong ket qua se sai dù model load thanh cong khong bao loi gi ca.
    """
    import io

    pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    input_tensor = _IMAGENET_TRANSFORM(pil_img).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        embedding = backbone(input_tensor)  # (1, 2048)
        extra = torch.tensor([extra_features], dtype=torch.float32, device=DEVICE)  # (1, 2)
        combined = torch.cat([embedding, extra], dim=1)  # (1, 2050)

        logit = head(combined)  # (1, 1)
        prob = torch.sigmoid(logit).item()
        pred = 1 if prob >= 0.5 else 0

    return pred, prob
