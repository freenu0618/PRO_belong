
import os
import gc
import torch
import subprocess
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# ==========================================
# 설정 (Configuration)
# ==========================================

# 1. GPU 비활성화 (OOM 방지 핵심)
os.environ["CUDA_VISIBLE_DEVICES"] = ""

BASE_MODEL_ID = "meta-llama/Meta-Llama-3-8B"

# 작업 경로 설정 (현재 스크립트 위치 기준)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
LLAMA_CPP_PATH = os.path.join(CURRENT_DIR, "llama.cpp")

# 변환 스크립트 위치 찾기 (최신 버전 vs 구 버전 대응)
CONVERT_SCRIPT = os.path.join(LLAMA_CPP_PATH, "convert_hf_to_gguf.py")
if not os.path.exists(CONVERT_SCRIPT):
    CONVERT_SCRIPT = os.path.join(LLAMA_CPP_PATH, "convert.py")

# 대상 모델 리스트
TARGET_MODELS = [
    # 1. Base Model (병합 없음)
    {
        "type": "base",
        "name": "llama3-8b-base",
        "path": os.path.join(CURRENT_DIR, "merged_models", "base_model_fp16") # 저장 경로
    },
    # 2. Adapter 1: Constant Step 100
    {
        "type": "adapter",
        "name": "llama3-8b-constant-100",
        "path": os.path.join(CURRENT_DIR, "output") 
    },
    # 3. Adapter 2: Cosine Step 100
    {
        "type": "adapter",
        "name": "llama3-8b-cosine-100",
        "path": os.path.join(CURRENT_DIR, "output", "checkpoint-100")
    },
    # 4. Adapter 3: Cosine Step 1000
    {
        "type": "adapter",
        "name": "llama3-8b-cosine-1000",
        "path": os.path.join(CURRENT_DIR, "output", "checkpoint-1000")
    }
]

# 출력 폴더 생성
MERGED_MODELS_DIR = os.path.join(CURRENT_DIR, "merged_models")
GGUF_MODELS_DIR = os.path.join(CURRENT_DIR, "gguf_models")

os.makedirs(MERGED_MODELS_DIR, exist_ok=True)
os.makedirs(GGUF_MODELS_DIR, exist_ok=True)

# ==========================================
# 유틸리티 함수
# ==========================================

def clear_memory():
    """메모리 강제 정리 함수"""
    gc.collect()
    torch.cuda.empty_cache() # CPU 모드라도 혹시 몰라 호출
    print("   [System] Memory Cleared.")

def merge_and_save(target):
    name = target["name"]
    model_type = target["type"]
    path = target["path"]
    save_path = os.path.join(MERGED_MODELS_DIR, name)
    
    print(f"\n>>> [Step 1] Loading & Merging: {name}...")
    
    # 이미 병합된 폴더가 있으면 스킵할지 여부? (여기서는 안전하게 덮어쓰기)
    
    try:
        if model_type == "adapter":
            print(f"   Loading Base Model: {BASE_MODEL_ID}")
            base_model = AutoModelForCausalLM.from_pretrained(
                BASE_MODEL_ID,
                low_cpu_mem_usage=True,
                return_dict=True,
                torch_dtype=torch.float16,
                device_map="cpu"
            )
            
            print(f"   Loading Adapter: {path}")
            model = PeftModel.from_pretrained(base_model, path)
            print(f"   Merging Adapter...")
            model = model.merge_and_unload()
            
            print(f"   Saving to disk: {save_path}")
            model.save_pretrained(save_path)
            tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID)
            tokenizer.save_pretrained(save_path)
            
            # 메모리 해제
            del model
            del base_model
            del tokenizer
            
        elif model_type == "base":
            print(f"   Loading Base Model to save locally...")
            model = AutoModelForCausalLM.from_pretrained(
                BASE_MODEL_ID,
                low_cpu_mem_usage=True,
                torch_dtype=torch.float16,
                device_map="cpu"
            )
            print(f"   Saving to disk: {save_path}")
            model.save_pretrained(save_path)
            tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID)
            tokenizer.save_pretrained(save_path)
            
            del model
            del tokenizer

        print(f"   Successfully saved {name}.")
        
    except Exception as e:
        print(f"   !!! Error during merge/save of {name}: {e}")
        return False
    
    finally:
        clear_memory()
        
    return True

def convert_to_gguf(target):
    name = target["name"]
    save_path = os.path.join(MERGED_MODELS_DIR, name)
    outfile = os.path.join(GGUF_MODELS_DIR, f"{name}.gguf")
    
    print(f"\n>>> [Step 2] Converting to GGUF: {name}...")
    
    # 명령어 구성
    cmd = [
        "python",
        CONVERT_SCRIPT,
        save_path,
        "--outfile", outfile,
        "--outtype", "f16"
    ]
    
    try:
        # subprocess로 실행 (별도 프로세스 -> 메모리 격리 효과)
        result = subprocess.run(cmd, check=True)
        print(f"   Conversion successfully finished. Output: {outfile}")
    except subprocess.CalledProcessError as e:
        print(f"   !!! Error during GGUF conversion for {name}: {e}")
    except Exception as e:
        print(f"   !!! Unexpected error: {e}")

# ==========================================
# 메인 실행
# ==========================================
if __name__ == "__main__":
    print("==========================================================")
    print(" Safe Merge Script for LLaMa-3 8B")
    print(" Target: 4 Models | Mode: CPU Only (Sequential)")
    print("==========================================================")
    
    for i, target in enumerate(TARGET_MODELS):
        print(f"\n##########################################################")
        print(f" Processing Model {i+1}/{len(TARGET_MODELS)}: {target['name']}")
        print(f"##########################################################")
        
        # 1. 병합 및 저장
        success = merge_and_save(target)
        
        # 2. 성공 시 GGUF 변환 수행
        if success:
            convert_to_gguf(target)
        
        print(f"\n[Info] Completed processing for {target['name']}.")
        print("Waiting 5 seconds for system stabilization...")
        import time
        time.sleep(5)
        
    print("\n==========================================================")
    print(" All jobs finished. Please check 'gguf_models' directory.")
    print("==========================================================")
