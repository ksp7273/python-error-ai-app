import gradio as gr
from llama_cpp import Llama
from huggingface_hub import hf_hub_download
import os

# Model config
MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct-GGUF"
MODEL_FILE = "qwen2.5-0.5b-instruct-q4_k_m.gguf"  # Quantized variant for speed/low res
CACHE_DIR = os.path.expanduser("~/.cache/huggingface/hub")

# Download model if not present (one-time, ~300MB)
def download_model():
    model_dir = os.path.join(CACHE_DIR, MODEL_NAME.split("/")[1])
    model_path = os.path.join(model_dir, MODEL_FILE)
    if not os.path.exists(model_path):
        print(f"Downloading model to {model_path}...")
        try:
            hf_hub_download(
                repo_id=MODEL_NAME,
                filename=MODEL_FILE,
                cache_dir=CACHE_DIR,
                local_dir_use_symlinks=False
            )
            print("Download successful")
        except Exception as e:
            print(f"Download failed: {e}")
            sys.exit(1)
    else:
        print(f"Model found at {model_path}")
    return model_path

download_model()  # Run on import

# Load model (CPU-optimized)
llm = Llama(
    model_path="/home/codespace/.cache/huggingface/hub/models--Qwen--Qwen2.5-0.5B-Instruct-GGUF/snapshots/9217f5db79a29953eb74d5343926648285ec7e67/qwen2.5-0.5b-instruct-q4_k_m.gguf",
    n_ctx=2048,  # Context for error desc
    n_threads=4,  # Use all 4 cores
    n_gpu_layers=0,  # CPU only
    verbose=False
)

def debug_python_error(description):
    if not description.strip():
        return "Please provide a Python error description.", ""
    
    # Prompt template for accurate, structured response
    prompt = f"""<|im_start|>system
You are a Python debugging expert. Given only the error description, explain why it occurs and provide clear, step-by-step solutions. Keep it concise.
<|im_end|>
<|im_start|>user
Error Description: {description}
<|im_end|>
<|im_start|>assistant
### Why This Problem Occurs:
[Brief explanation]

### Steps to Solve:
1. [Step 1]
2. [Step 2]
..."""
    
    # Generate response (fast on CPU)
    output = llm(
        prompt,
        max_tokens=300,
        temperature=0.1,  # Low for accuracy
        top_p=0.9,
        stop=["<|im_end|>", "### Why This Problem Occurs:"],  # Structured stop
        echo=False
    )
    
    response = output['choices'][0]['text'].strip()
    return response, ""  # Gradio format: output, status

# Gradio UI (simple, enforces description-only input)
with gr.Blocks(title="Python Error Debugger") as demo:
    gr.Markdown("# Python Error Debugger\nUpload only the error description (text). AI will explain & fix.")
    desc_input = gr.Textbox(
        label="Error Description",
        placeholder="e.g., 'TypeError: unsupported operand type(s) for +: \'int\' and \'str\' when adding 5 + \"hello\"'",
        lines=3
    )
    explain_output = gr.Markdown(label="AI Response")
    
    submit_btn = gr.Button("Debug Error")
    submit_btn.click(
        fn=debug_python_error,
        inputs=desc_input,
        outputs=explain_output
    )
    gr.Examples(
        examples=[
            "IndexError: list index out of range",
            "ImportError: No module named 'numpy'",
            "KeyError: 'user_id' in dict access"
        ],
        inputs=desc_input
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)  # Local in Codespaces