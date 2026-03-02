import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
DB_DIR = os.path.join(DATA_DIR, "db")
MODEL_DIR = os.path.join(BASE_DIR, "models")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)

# Embedding 模型配置（16GB 内存可用 large）
EMBEDDING_MODEL_NAME = "BAAI/bge-large-zh-v1.5"
# HuggingFace 镜像源配置
HF_MIRROR_URL = "https://hf-mirror.com"  # 国内镜像源
os.environ["HF_ENDPOINT"] = HF_MIRROR_URL
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"  # 启用快速传输
os.environ["TRANSFORMERS_SAFE_WEIGHTS_ONLY"] = "1"  # 强制使用 safetensors 格式
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "0"  # 显示进度条
os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = "600"  # 10分钟超时

# Qdrant 配置
QDRANT_COLLECTION_NAME = "academic_papers"
QDRANT_VECTOR_SIZE = 1024  # BGE-large-zh 的输出维度
QDRANT_PERSIST_PATH = os.path.join(DB_DIR, "qdrant_db")  # 本地持久化路径

# 本地模型配置
LOCAL_LLM_PATH = os.path.join(MODEL_DIR, "Qwen3-4B-Q4_0.gguf")
LOCAL_LLM_N_CTX = 4096
LOCAL_LLM_N_THREADS = 6

# 文本分块配置
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50