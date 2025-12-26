# inference_server/services/training.py
"""파인튜닝 학습 서비스"""

import os
import threading
import time
import logging
from fastapi import HTTPException

from .. import state
from ..schemas import TrainRequest

logger = logging.getLogger(__name__)


def run_training_task(job_id: str, params: dict):
    """
    백그라운드 파인튜닝 실행
    
    Args:
        job_id: 작업 ID
        params: 학습 파라미터 (UI에서 전달)
    """
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig, TrainingArguments, TrainerCallback
        from peft import LoraConfig
        from trl import SFTTrainer, DataCollatorForCompletionOnlyLM
        from datasets import load_dataset
        import torch

        state.training_jobs[job_id]["status"] = "loading"
        state.training_jobs[job_id]["logs"].append("📦 모델 로딩 준비 중...")

        # ✅ 추론 모델 언로드하여 GPU 메모리 확보
        import gc
        if state.model is not None:
            state.training_jobs[job_id]["logs"].append("🔄 추론 모델 언로드 중 (GPU 메모리 확보)...")
            try:
                del state.model
                state.model = None
            except Exception:
                pass
        if state.tokenizer is not None:
            try:
                del state.tokenizer
                state.tokenizer = None
            except Exception:
                pass
        
        # GPU 캐시 및 가비지 컬렉션 (중요)
        gc.collect()
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
        state.training_jobs[job_id]["logs"].append("✅ GPU 메모리 정리 완료")
        
        state.training_jobs[job_id]["logs"].append("📦 학습용 모델 로딩 중...")

        # HF Token
        hf_token = os.environ.get("HF_TOKEN")
        if not hf_token:
            raise ValueError("HF_TOKEN not set")

        # 1. 양자화 설정 (UI 선택에 따라)
        quant_type = params.get("quantization", "4bit") or "4bit"  # None 방지
        use_double_quant = params.get("use_double_quant", True)
        if use_double_quant is None:
            use_double_quant = True

        quantization_config = None
        if quant_type == "4bit":
            state.training_jobs[job_id]["logs"].append("🔧 4-bit 양자화 (NF4) 적용")
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=use_double_quant,
                bnb_4bit_quant_type="nf4"
            )
        elif quant_type == "8bit":
            state.training_jobs[job_id]["logs"].append("🔧 8-bit 양자화 적용")
            quantization_config = BitsAndBytesConfig(
                load_in_8bit=True
            )
        else:
            state.training_jobs[job_id]["logs"].append("🔧 Full Precision (양자화 없음)")

        # 2. 모델 로드
        base_model_id = "meta-llama/Meta-Llama-3-8B"
        state.training_jobs[job_id]["logs"].append(f"📥 Loading {base_model_id}...")

        model_kwargs = {
            "device_map": "auto",
            "token": hf_token
        }
        if quantization_config:
            model_kwargs["quantization_config"] = quantization_config
        else:
            model_kwargs["torch_dtype"] = torch.bfloat16

        train_model = AutoModelForCausalLM.from_pretrained(base_model_id, **model_kwargs)
        train_model.config.use_cache = False

        train_tokenizer = AutoTokenizer.from_pretrained(base_model_id, token=hf_token)
        train_tokenizer.pad_token = train_tokenizer.eos_token
        train_tokenizer.padding_side = "right"

        state.training_jobs[job_id]["logs"].append("✅ 모델 로드 완료")

        # 3. LoRA Config (고정)
        peft_config = LoraConfig(
            lora_alpha=16,
            lora_dropout=0,
            r=16,
            bias="none",
            task_type="CAUSAL_LM",
            target_modules=["q_proj", "v_proj", "k_proj", "gate_proj", "up_proj", "down_proj"]
        )

        # 4. 데이터셋 로드 (Alpaca Clean)
        state.training_jobs[job_id]["logs"].append("📊 Alpaca 데이터셋 로딩...")
        dataset = load_dataset("yahma/alpaca-cleaned", split="train")

        # 데이터셋 포맷팅
        def format_alpaca(example):
            instruction = example["instruction"]
            input_text = example["input"] if example["input"] else ""
            output = example["output"]

            if input_text:
                text = f"### Instruction:\n{instruction}\n\n### Input:\n{input_text}\n\n### Response:\n{output}"
            else:
                text = f"### Instruction:\n{instruction}\n\n### Response:\n{output}"
            return {"text": text}

        dataset = dataset.map(format_alpaca)
        state.training_jobs[job_id]["logs"].append(f"✅ 데이터셋 로드 완료: {len(dataset)}개 샘플")

        # ✅ max_steps를 먼저 정의 (데이터 분할에서 사용하기 위해)
        max_steps = params.get("max_steps", 100)
        state.training_jobs[job_id]["logs"].append(f"⚙️ max_steps 설정: {max_steps}")

        # Train/Eval 분할 (80/20) - 노트북과 동일
        train_test = dataset.train_test_split(test_size=0.2, seed=42)
        train_dataset = train_test["train"]
        # ✅ Eval 데이터셋 크기를 max_steps와 정확히 동일하게 설정
        eval_size = max_steps
        eval_dataset = train_test["test"].select(range(min(eval_size, len(train_test["test"]))))
        state.training_jobs[job_id]["logs"].append(f"📊 Train: {len(train_dataset)}, Eval: {len(eval_dataset)} (max_steps와 동일)")

        # 5. Data Collator
        response_template = "### Response:\n"
        collator = DataCollatorForCompletionOnlyLM(
            tokenizer=train_tokenizer,
            response_template=response_template,
            mlm=False
        )

        # 6. Training Arguments
        output_dir = f"/workspace/output/{params['model_name']}"
        os.makedirs(output_dir, exist_ok=True)

        # ✅ max_steps는 이미 위에서 정의됨 (데이터 분할에서 사용하기 위해)

        # ✅ max_steps만 사용 (num_train_epochs 없이)
        # Hugging Face: max_steps > 0이면 epochs 무시됨
        
        # 양자화 타입에 따라 fp16/bf16 설정
        use_fp16 = quant_type in ["4bit", "8bit"]  # 양자화 시 fp16
        use_bf16 = quant_type == "none"  # 양자화 없으면 bf16 (네이티브)
        
        training_args = TrainingArguments(
            output_dir=output_dir,
            report_to="none",
            per_device_train_batch_size=2,
            per_device_eval_batch_size = 2,
            gradient_accumulation_steps=8,
            warmup_steps=params.get("warmup_steps", 30),
            max_steps=max_steps,  # ✅ 유일한 종료 조건
            eval_steps=params.get("eval_steps", 10),
            save_steps=params.get("save_steps", 50),
            evaluation_strategy=params.get("evaluation_strategy", "steps"),
            save_strategy=params.get("save_strategy", "steps"),
            logging_steps=1,
            learning_rate=params.get("learning_rate", 1e-4),
            optim="adamw_8bit" if quant_type != "none" else "adamw_torch",
            weight_decay=params.get("weight_decay", 0.01),
            lr_scheduler_type="constant_with_warmup",
            seed=42,
            gradient_checkpointing=True,
            gradient_checkpointing_kwargs={'use_reentrant': True},
            fp16=use_fp16,
            bf16=use_bf16,
        )




        state.training_jobs[job_id]["logs"].append("🚀 학습 시작!")
        state.training_jobs[job_id]["status"] = "running"
        state.training_jobs[job_id]["total_steps"] = max_steps
        state.training_jobs[job_id]["start_time"] = time.time()  # ✅ 시작 시간 기록

        # 7. Custom Callback for Progress
        # ✅ max_steps와 start_time을 여기서 캡처 (클로저)
        configured_max_steps = max_steps
        training_start_time = time.time()
        last_logged_step = -1  # ✅ 중복 로그 방지용
        
        class ProgressCallback(TrainerCallback):
            def on_log(self, args, cb_state, control, logs=None, **kwargs):
                nonlocal last_logged_step
                if logs:
                    step = cb_state.global_step
                    loss = logs.get("loss", None)
                    eval_loss = logs.get("eval_loss", None)
                    
                    # ✅ 경과 시간 계산
                    elapsed = time.time() - training_start_time
                    
                    state.training_jobs[job_id]["current_step"] = step
                    state.training_jobs[job_id]["metrics"]["current_step"] = step
                    state.training_jobs[job_id]["metrics"]["total_steps"] = configured_max_steps
                    state.training_jobs[job_id]["metrics"]["elapsed_time"] = elapsed
                    
                    # ✅ loss가 있으면 업데이트
                    if loss is not None:
                        state.training_jobs[job_id]["metrics"]["loss"] = loss
                    
                    # ✅ eval_loss가 있으면 업데이트
                    if eval_loss is not None:
                        state.training_jobs[job_id]["metrics"]["eval_loss"] = eval_loss
                        state.training_jobs[job_id]["logs"].append(f"[Step {step}] 📊 Eval Loss: {eval_loss:.4f}")

                    progress = int((step / configured_max_steps) * 100) if configured_max_steps else 0
                    state.training_jobs[job_id]["progress"] = min(progress, 100)
                    
                    # ✅ 중복 로그 방지: 같은 step에서 loss가 있을 때만 로그
                    if loss is not None and step != last_logged_step:
                        state.training_jobs[job_id]["logs"].append(f"[Step {step}/{configured_max_steps}] Loss: {loss:.4f}")
                        last_logged_step = step

        # 8. Trainer 생성
        trainer = SFTTrainer(
            model=train_model,
            tokenizer=train_tokenizer,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,  # ✅ 수정: train_dataset → eval_dataset (max_steps개)
            peft_config=peft_config,
            dataset_text_field="text",
            max_seq_length=2048,
            dataset_num_proc=2,
            packing=False,
            args=training_args,
            data_collator=collator,
            callbacks=[ProgressCallback()]
        )

        # 9. 학습 실행
        trainer.train()

        # 10. 모델 저장 및 검증
        trainer.save_model(output_dir)
        
        # ✅ adapter_config.json 저장 확인
        adapter_config_path = os.path.join(output_dir, "adapter_config.json")
        if os.path.exists(adapter_config_path):
            state.training_jobs[job_id]["logs"].append(f"✅ 어댑터 저장 성공: {output_dir}")
            state.training_jobs[job_id]["logs"].append(f"📁 adapter_config.json 확인됨")
        else:
            state.training_jobs[job_id]["logs"].append(f"⚠️ 어댑터 저장 경로: {output_dir}")
            state.training_jobs[job_id]["logs"].append(f"❌ adapter_config.json 미발견!")
            # 폴더 내용 로깅
            if os.path.exists(output_dir):
                files = os.listdir(output_dir)
                state.training_jobs[job_id]["logs"].append(f"📋 폴더 내용: {files}")

        state.training_jobs[job_id]["status"] = "completed"
        state.training_jobs[job_id]["progress"] = 100
        state.training_jobs[job_id]["logs"].append("🎉 학습 완료!")

        # GPU 메모리 정리
        del trainer, train_model, train_tokenizer
        torch.cuda.empty_cache()
        
        # ✅ 추론 모델 재로드 (백그라운드)
        state.training_jobs[job_id]["logs"].append("🔄 추론 모델 재로드 중...")
        try:
            from .generate import reload_model
            reload_model()
            state.training_jobs[job_id]["logs"].append("✅ 추론 모델 재로드 완료")
        except Exception as reload_err:
            state.training_jobs[job_id]["logs"].append(f"⚠️ 추론 모델 재로드 실패: {reload_err}")
            logger.warning(f"Failed to reload inference model: {reload_err}")

    except torch.cuda.CudaError as cuda_err:
        # CUDA 에러 명확히 처리
        logger.error(f"CUDA Error: {cuda_err}")
        state.training_jobs[job_id]["status"] = "failed"
        state.training_jobs[job_id]["error"] = f"GPU 에러: {str(cuda_err)}"
        state.training_jobs[job_id]["logs"].append(f"❌ GPU 에러: {str(cuda_err)}")
        state.training_jobs[job_id]["logs"].append("💡 GPU 메모리 부족 또는 점유 상태일 수 있습니다.")
        try:
            torch.cuda.empty_cache()
        except:
            pass

    except Exception as e:
        # 일반 에러 처리
        error_msg = str(e)
        if "CUDA" in error_msg or "cuda" in error_msg or "device" in error_msg.lower():
            error_msg = f"GPU 에러: {error_msg}"
            state.training_jobs[job_id]["logs"].append("💡 GPU 메모리 부족 또는 점유 상태일 수 있습니다.")
        
        logger.error(f"Training failed: {e}")
        state.training_jobs[job_id]["status"] = "failed"
        state.training_jobs[job_id]["error"] = error_msg
        state.training_jobs[job_id]["logs"].append(f"❌ 오류: {error_msg}")
        
        # GPU 메모리 정리 시도
        try:
            torch.cuda.empty_cache()
        except:
            pass



async def start_training(request: TrainRequest) -> dict:
    """파인튜닝 학습 시작"""
    # 이미 학습 중인지 확인
    for jid, job in state.training_jobs.items():
        if job.get("status") in ["loading", "running"]:
            raise HTTPException(status_code=409, detail="이미 학습이 진행 중입니다.")

    # Job ID 생성
    job_id = f"job-{request.model_name}-{int(time.time())}"

    # Job 초기화
    state.training_jobs[job_id] = {
        "job_id": job_id,
        "model_name": request.model_name,
        "status": "pending",
        "progress": 0,
        "current_step": 0,
        "total_steps": request.max_steps,
        "metrics": {},
        "logs": ["📋 학습 작업 생성됨"],
        "created_at": time.time(),
        "params": request.dict()
    }

    # 백그라운드 스레드로 학습 시작
    thread = threading.Thread(
        target=run_training_task,
        args=(job_id, request.dict())
    )
    thread.start()

    return {
        "ok": True,
        "job_id": job_id,
        "message": f"학습 시작: {request.model_name}",
        "data": {"job_id": job_id}
    }


async def get_training_status(job_id: str) -> dict:
    """학습 상태 조회"""
    if job_id not in state.training_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = state.training_jobs[job_id]
    
    # ✅ metrics 복사본 생성 (원본 수정 방지)
    metrics = dict(job.get("metrics", {}))
    if "total_steps" not in metrics:
        metrics["total_steps"] = job.get("total_steps", 100)

    return {
        "ok": True,
        "job_id": job_id,
        "status": job.get("status", "unknown"),
        "status_text": job.get("status", "unknown"),
        "progress": job.get("progress", 0),
        "metrics": metrics,
        "logs": job.get("logs", [])[-20:],
        "error": job.get("error"),
        "total_steps": job.get("total_steps", 100)  # ✅ 직접 반환도 추가
    }


async def list_trained_models() -> dict:
    """학습된 모델 목록"""
    models = ["base"]

    # /workspace/output 스캔
    output_dir = "/workspace/output"
    if os.path.exists(output_dir):
        for name in os.listdir(output_dir):
            if os.path.isdir(os.path.join(output_dir, name)):
                models.append(name)

    # 기존 fine_tune 폴더도 스캔
    local_dir = os.path.join(os.getcwd(), "belong", "ml", "fine_tune")
    if os.path.exists(local_dir):
        for name in os.listdir(local_dir):
            if os.path.isdir(os.path.join(local_dir, name)) and name not in models:
                models.append(name)

    return {"ok": True, "models": models}


async def delete_trained_model(model_name: str) -> dict:
    """
    파인튜닝된 모델 삭제 + 스토리지 정리
    
    Args:
        model_name: 삭제할 모델 이름
        
    Returns:
        {"ok": True, "message": "삭제 완료", "freed_mb": 용량}
    """
    import shutil
    
    # 보호된 모델 (삭제 불가)
    protected = ["base", "lora_best_r32"]
    if model_name in protected:
        return {"ok": False, "error": f"'{model_name}'은(는) 삭제할 수 없습니다."}
    
    deleted = False
    freed_bytes = 0
    
    def get_folder_size(path):
        """폴더 크기 계산 (바이트)"""
        total = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        total += os.path.getsize(fp)
        except:
            pass
        return total
    
    # 1. /workspace/output에서 찾아서 삭제
    output_path = f"/workspace/output/{model_name}"
    if os.path.exists(output_path):
        try:
            freed_bytes += get_folder_size(output_path)
            shutil.rmtree(output_path)
            logger.info(f"🗑️ Deleted model: {output_path}")
            deleted = True
        except Exception as e:
            return {"ok": False, "error": f"삭제 실패: {e}"}
    
    # 2. fine_tune 폴더에서도 확인
    local_path = os.path.join(os.getcwd(), "belong", "ml", "fine_tune", model_name)
    if os.path.exists(local_path):
        try:
            freed_bytes += get_folder_size(local_path)
            shutil.rmtree(local_path)
            logger.info(f"🗑️ Deleted model: {local_path}")
            deleted = True
        except Exception as e:
            return {"ok": False, "error": f"삭제 실패: {e}"}
    
    freed_mb = round(freed_bytes / (1024 * 1024), 2)
    
    if deleted:
        logger.info(f"✅ Model '{model_name}' deleted, freed {freed_mb}MB")
        return {"ok": True, "message": f"'{model_name}' 삭제 완료 ({freed_mb}MB 확보)", "freed_mb": freed_mb}
    else:
        return {"ok": False, "error": f"'{model_name}'을(를) 찾을 수 없습니다."}


async def cleanup_storage() -> dict:
    """
    스토리지 정리 - 고아 폴더 및 오래된 체크포인트 삭제
    
    Returns:
        {"ok": True, "cleaned": [...], "freed_mb": 용량}
    """
    import shutil
    
    cleaned = []
    freed_bytes = 0
    protected = ["base", "lora_best_r32"]
    
    def get_folder_size(path):
        total = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        total += os.path.getsize(fp)
        except:
            pass
        return total
    
    output_dir = "/workspace/output"
    
    if not os.path.exists(output_dir):
        return {"ok": True, "message": "정리할 폴더가 없습니다.", "cleaned": [], "freed_mb": 0}
    
    for folder_name in os.listdir(output_dir):
        folder_path = os.path.join(output_dir, folder_name)
        
        if not os.path.isdir(folder_path):
            continue
        
        # 보호된 폴더 건너뛰기
        if folder_name in protected:
            continue
        
        # 1. 오래된 checkpoint 정리 (최신 1개만 유지)
        checkpoints = [d for d in os.listdir(folder_path) 
                      if os.path.isdir(os.path.join(folder_path, d)) and d.startswith("checkpoint-")]
        
        if len(checkpoints) > 1:
            # 스텝 번호로 정렬
            try:
                checkpoints.sort(key=lambda x: int(x.split('-')[-1]) if x.split('-')[-1].isdigit() else 0)
                # 마지막 것 제외하고 삭제
                for old_cp in checkpoints[:-1]:
                    old_path = os.path.join(folder_path, old_cp)
                    size = get_folder_size(old_path)
                    shutil.rmtree(old_path)
                    freed_bytes += size
                    cleaned.append(f"{folder_name}/{old_cp}")
                    logger.info(f"🗑️ Deleted old checkpoint: {old_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup checkpoints: {e}")
        
        # 2. adapter_config.json이 없는 폴더 = 불완전한 학습 → 삭제
        has_adapter = os.path.exists(os.path.join(folder_path, "adapter_config.json"))
        has_checkpoint_adapter = any(
            os.path.exists(os.path.join(folder_path, cp, "adapter_config.json"))
            for cp in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, cp))
        ) if os.path.exists(folder_path) else False
        
        if not has_adapter and not has_checkpoint_adapter:
            # 불완전한 학습 데이터 삭제
            try:
                size = get_folder_size(folder_path)
                shutil.rmtree(folder_path)
                freed_bytes += size
                cleaned.append(f"{folder_name} (불완전)")
                logger.info(f"🗑️ Deleted incomplete model: {folder_path}")
            except Exception as e:
                logger.warning(f"Failed to delete incomplete model: {e}")
    
    freed_mb = round(freed_bytes / (1024 * 1024), 2)
    
    return {
        "ok": True, 
        "message": f"스토리지 정리 완료! {len(cleaned)}개 항목, {freed_mb}MB 확보",
        "cleaned": cleaned,
        "freed_mb": freed_mb
    }


async def get_storage_info() -> dict:
    """스토리지 사용량 정보"""
    import shutil
    
    output_dir = "/workspace/output"
    
    if not os.path.exists(output_dir):
        return {"ok": True, "total_mb": 0, "models": []}
    
    def get_folder_size(path):
        total = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        total += os.path.getsize(fp)
        except:
            pass
        return total
    
    models = []
    total_bytes = 0
    
    for folder_name in os.listdir(output_dir):
        folder_path = os.path.join(output_dir, folder_name)
        if os.path.isdir(folder_path):
            size = get_folder_size(folder_path)
            total_bytes += size
            models.append({
                "name": folder_name,
                "size_mb": round(size / (1024 * 1024), 2)
            })
    
    return {
        "ok": True,
        "total_mb": round(total_bytes / (1024 * 1024), 2),
        "models": sorted(models, key=lambda x: x["size_mb"], reverse=True)
    }

