import torch
from fastapi import APIRouter
from app.services.processor import processor

router= APIRouter()

@router.post("/analyze")
async def analyze_document(content: str):
    # 1. làm sạch văn bảng bằng processor
    refined_text = processor.clean_historical_text(content)

    # 2. giả sử ta biến văn bản thành Tensor để hiểu AI
    mock_tensor = torch.randn(3, 3)
    gpu_tensor = processor.move_to_gpu(mock_tensor)

    return {
        "original": content,
        "refined": refined_text,
        "processed_on": str(gpu_tensor.device), # Trả về 'mps:0' nếu chạy trên GPU Mac
        "status": "Success"
    }