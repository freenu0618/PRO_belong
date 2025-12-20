
import os
import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

app = FastAPI(title="Belong AI Inference Server")

# 전역 변수로 모델과 토크나이저 저장
model = None
tokenizer = None

# 요청 모델 스키마 정의
class GenerateRequest(BaseModel):
    prompt: str
    max_new_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    model: str = "constant-100"

@app.on_event("startup")
async def startup_event():
    global model, tokenizer
    print("🚀 Loading Models...")

    # 1. Base Model ID
    base_model_id = "meta-llama/Meta-Llama-3-8B"
    repo_id = "freenu0618/belong-adapter"
    hf_token = os.environ.get("HF_TOKEN")

    try:
        # 3. Base Model 로드
        # BFloat16 for efficiency
        torch_dtype = torch.bfloat16 if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else torch.float16
        print(f"Loading Base Model: {base_model_id}")
        
        model = AutoModelForCausalLM.from_pretrained(
            base_model_id,
            torch_dtype=torch_dtype,
            device_map="auto",
            token=hf_token
        )
        tokenizer = AutoTokenizer.from_pretrained(base_model_id, token=hf_token)
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "right"

        # 4. Multi-Adapter Loading (Dynamic)
        # 기본적으로 peft로 래핑
        print("Initializing PeftModel...")
        # 첫 번째 어댑터(Default) 로드 - Constant-100 (branch: constant-100)
        # 주의: 처음 로드할 때 'default'라는 이름으로 들어감.
        model = PeftModel.from_pretrained(model, repo_id, revision="constant-100", adapter_name="constant-100", token=hf_token)
        
        print("Loading Additional Adapters...")
        # Cosine-100
        model.load_adapter(repo_id, revision="cosine-100", adapter_name="cosine-100", token=hf_token)
        # Cosine-1000
        model.load_adapter(repo_id, revision="cosine-1000", adapter_name="cosine-1000", token=hf_token)
        
        print("✅ Models Loaded: [constant-100, cosine-100, cosine-1000]")
        
    except Exception as e:
        print(f"❌ Critical Error loading model: {e}")
        raise e

@app.post("/generate")
async def generate_text(request: GenerateRequest):
    global model, tokenizer
    
    if not model or not tokenizer:
        raise HTTPException(status_code=500, detail="Model is not loaded.")

    try:
        # 모델 선택 로직
        # request에 'model' 필드가 있다고 가정 (GenerateRequest 업데이트 필요할 수도 있음, 
        # 하지만 Pydantic에 없으면 extra ignore 되거나, payload로 받을 때 주의)
        # 여기서는 request body를 직접 파싱하거나, GenerateRequest에 field 추가를 제안해야 함.
        # 일단 Pydantic 모델을 수정하지 않고, 그냥 기본 adapter 사용하거나
        # request.model 이라는 필드가 있다면 그것을 사용 (AttributeError 방지 위해 getattr)
        
        target_model = getattr(request, "model", "constant-100") 
        
        # Base Model 요청 시
        if target_model == "base" or "base" in target_model:
            # 어댑터 비활성화
            context = model.disable_adapter()
        else:
            # 어댑터 활성화 (존재하는지 확인 필요)
            if target_model in model.peft_config:
                model.set_adapter(target_model)
                context = None # set_adapter는 영구적 변경 (context manager 아님)
            else:
                # 없는 모델이면 Default(constant-100) 사용
                model.set_adapter("constant-100")
                context = None

        # 생성 (Context Manager 사용하여 Base 모델일 때만 disable 되도록 할 수도 있으나, 
        # set_adapter는 global state를 바꾸므로 주의. 
        # API 요청은 순차적(또는 Uvicorn worker)이라 경쟁 상태 주의. 
        # 간단한 구현을 위해 요청마다 set_adapter 호출)
        
        inputs = tokenizer(request.prompt, return_tensors="pt").to(model.device)
        
        # Base Model Context 처리
        if target_model == "base" or "base" in target_model:
             with model.disable_adapter():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=request.max_new_tokens,
                    temperature=request.temperature,
                    top_p=request.top_p,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id,
                    eos_token_id=[tokenizer.eos_token_id, tokenizer.convert_tokens_to_ids("<|eot_id|>")]
                )
        else:
            outputs = model.generate(
                **inputs,
                max_new_tokens=request.max_new_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=[tokenizer.eos_token_id, tokenizer.convert_tokens_to_ids("<|eot_id|>")]
            )
            
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        prompt_len = len(tokenizer.decode(inputs.input_ids[0], skip_special_tokens=True))
        response_text = generated_text[prompt_len:]

        return {"output": response_text.strip()}

    except Exception as e:
        print(f"Generation Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Belong AI Inference Server is Running!"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
