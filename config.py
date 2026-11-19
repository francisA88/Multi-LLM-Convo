import pathlib
import os

class Config:
    host = "127.0.0.1"
    port = 1876
    c_name_a = "agent_a"
    c_name_b = "agent_b"
    topic_root = "convo"
    model_dir = pathlib.Path(f"{os.path.expanduser('~')}/programming/models") # change to your own directory containing your gguf model
    model_file = "Llama-3.2-1B-Instruct-Q4_K_M.gguf"