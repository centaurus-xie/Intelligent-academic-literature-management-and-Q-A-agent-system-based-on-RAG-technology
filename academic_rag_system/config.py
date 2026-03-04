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
# 使用本地模型路径，避免重复下载
BGE_LOCAL_PATH = os.path.join(MODEL_DIR, "bge-large-zh-v1.5")

# 检查本地模型是否存在
if os.path.exists(BGE_LOCAL_PATH) and any(os.listdir(BGE_LOCAL_PATH)):
    EMBEDDING_MODEL_NAME = BGE_LOCAL_PATH
    print("✅ 使用本地BGE-large模型（完全离线）")
else:
    EMBEDDING_MODEL_NAME = "BAAI/bge-large-zh-v1.5"
    print("⚠️  本地模型不存在，将尝试在线下载")

# 强制离线模式，避免网络连接
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"

# 镜像源配置（备用）
HF_MIRROR_URL = "https://hf-mirror.com"
os.environ["HF_ENDPOINT"] = HF_MIRROR_URL
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"

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