import subprocess
import time
import sys

def run_quantization():
    models = [
        {"name": "llama3-8b-base-q4", "file": "Modelfile_base"},
        {"name": "llama3-8b-constant-100-q4", "file": "Modelfile_constant_100"},
        {"name": "llama3-8b-cosine-100-q4", "file": "Modelfile_cosine_100"},
        {"name": "llama3-8b-cosine-1000-q4", "file": "Modelfile_cosine_1000"},
    ]

    print("=" * 60)
    print("🚀 Ollama Model Quantization Script (Q4_K_M)")
    print("=" * 60)
    print(f"Total models to process: {len(models)}")
    print("This process may take some time depending on your disk speed.")
    print("-" * 60)

    for i, model in enumerate(models, 1):
        name = model["name"]
        modelfile = model["file"]
        
        print(f"\n[{i}/{len(models)}] Processing: {name} ...")
        start_time = time.time()
        
        # Command: ollama create <name> -f <modelfile> -q Q4_K_M
        cmd = ["ollama", "create", name, "-f", modelfile, "-q", "Q4_K_M"]
        
        try:
            # Run command and stream output
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace' # Handle potential encoding errors safely
            )
            
            # Print output in real-time
            for line in process.stdout:
                line = line.strip()
                if line:
                    print(f"  > {line}")
            
            process.wait()
            
            if process.returncode == 0:
                elapsed = time.time() - start_time
                print(f"✅ Success! ({elapsed:.2f}s)")
            else:
                print(f"❌ Failed with exit code {process.returncode}")
                
        except Exception as e:
            print(f"❌ Error occurred: {str(e)}")
        
        print("-" * 60)

    print("\n🎉 All tasks completed.")
    print("Run 'ollama list' to verify the new models.")

if __name__ == "__main__":
    run_quantization()
