#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Device Detection Utility for SentenceTransformer and PyTorch Models

Provides centralized device management with automatic detection of:
- CUDA (NVIDIA GPUs)
- MPS (Apple Silicon M1/M2/M3)
- CPU (fallback)

Author: Claude (SuperClaude)
Date: 2025-10-04
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def get_best_device(prefer_device: Optional[str] = None) -> str:
    """
    Auto-detect the best available device for PyTorch/SentenceTransformer

    Priority Order:
    1. User-specified device (if provided and available)
    2. CUDA (NVIDIA GPU)
    3. MPS (Apple Silicon)
    4. CPU (fallback)

    Args:
        prefer_device: Optional user preference ('cuda', 'mps', 'cpu')

    Returns:
        Device string ('cuda', 'mps', or 'cpu')

    Example:
        >>> device = get_best_device()
        >>> model = SentenceTransformer('model-name', device=device)
    """
    try:
        import torch

        # If user specified a preference, validate and use it
        if prefer_device:
            prefer_device = prefer_device.lower()

            if prefer_device == 'cuda' and torch.cuda.is_available():
                cuda_device = f"cuda:0"
                gpu_name = torch.cuda.get_device_name(0)
                logger.info(f"✓ Using user-preferred CUDA device: {gpu_name}")
                return 'cuda'

            elif prefer_device == 'mps' and torch.backends.mps.is_available():
                logger.info("✓ Using user-preferred MPS device (Apple Silicon)")
                return 'mps'

            elif prefer_device == 'cpu':
                logger.info("✓ Using user-preferred CPU device")
                return 'cpu'

            else:
                logger.warning(f"Preferred device '{prefer_device}' not available, auto-detecting...")

        # Auto-detection priority: CUDA > MPS > CPU
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            logger.info(f"✓ Auto-detected CUDA device: {gpu_name} ({gpu_memory:.2f} GB)")
            return 'cuda'

        elif torch.backends.mps.is_available():
            logger.info("✓ Auto-detected MPS device (Apple Silicon)")
            return 'mps'

        else:
            logger.info("ℹ No GPU detected, using CPU")
            return 'cpu'

    except ImportError:
        logger.warning("PyTorch not available, defaulting to CPU")
        return 'cpu'

    except Exception as e:
        logger.error(f"Error detecting device: {e}, defaulting to CPU")
        return 'cpu'


def get_device_info() -> dict:
    """
    Get detailed information about available devices

    Returns:
        Dictionary with device availability and specs

    Example:
        >>> info = get_device_info()
        >>> print(info['cuda_available'])
        True
    """
    info = {
        'cuda_available': False,
        'cuda_device_count': 0,
        'cuda_devices': [],
        'mps_available': False,
        'recommended_device': 'cpu'
    }

    try:
        import torch

        # CUDA info
        if torch.cuda.is_available():
            info['cuda_available'] = True
            info['cuda_device_count'] = torch.cuda.device_count()

            for i in range(torch.cuda.device_count()):
                device_props = torch.cuda.get_device_properties(i)
                info['cuda_devices'].append({
                    'id': i,
                    'name': torch.cuda.get_device_name(i),
                    'total_memory_gb': device_props.total_memory / (1024**3),
                    'compute_capability': f"{device_props.major}.{device_props.minor}"
                })

        # MPS info
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            info['mps_available'] = True

        # Recommended device
        info['recommended_device'] = get_best_device()

    except Exception as e:
        logger.error(f"Error getting device info: {e}")

    return info


def log_device_selection(device: str, model_name: str = "SentenceTransformer"):
    """
    Log device selection for tracking and debugging

    Args:
        device: Selected device string
        model_name: Name of the model being loaded
    """
    logger.info(f"🚀 {model_name} will use device: {device.upper()}")

    if device == 'cpu':
        logger.warning(
            "⚠️ Using CPU for embeddings. Performance may be slow. "
            "Consider using a GPU-enabled environment for faster processing."
        )
