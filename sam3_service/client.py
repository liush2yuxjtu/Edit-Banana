"""
SAM3 Service Client
SAM3 服务客户端
"""

import requests
import json
from typing import Dict, Any, Optional, List
from pathlib import Path


class SAM3Client:
    """SAM3 服务客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def segment_image(self, image_path: str, **kwargs) -> Dict[str, Any]:
        """
        分割图像
        
        Args:
            image_path: 图像路径
            
        Returns:
            Dict: 分割结果
        """
        try:
            with open(image_path, 'rb') as f:
                files = {'image': f}
                params = kwargs
                
                response = self.session.post(
                    f"{self.base_url}/api/v1/segment",
                    files=files,
                    params=params
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {
                        "error": f"Segmentation failed with status {response.status_code}",
                        "details": response.text
                    }
                    
        except Exception as e:
            return {"error": str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def list_models(self) -> Dict[str, Any]:
        """列出可用模型"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/models")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
