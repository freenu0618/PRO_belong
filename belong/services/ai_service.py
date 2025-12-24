# belong/services/ai_service.py
"""
[DEPRECATED] 이 파일은 하위 호환성을 위해 유지됩니다.
새 코드는 belong.services.ai 패키지를 직접 사용하세요.

새 구조:
    from belong.services.ai import AIService
    # 또는
    from belong.services.ai.translation import TranslationService
"""

# 새 패키지에서 re-export
from belong.services.ai import AIService, ModelLoaderService, UTILITY_MODELS

# 기존 함수들도 re-export (registry.py 등에서 사용)
from belong.services.ai.model_loader import get_pipeline, preload_models

__all__ = ['AIService', 'ModelLoaderService', 'UTILITY_MODELS', 'get_pipeline', 'preload_models']
