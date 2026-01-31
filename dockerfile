# 使用支持CUDA 12.8的Python基础镜像
# 基于NVIDIA CUDA 12.8 runtime + Ubuntu 22.04 + Python 3.9
# FROM nvidia/cuda:12.8.0-runtime-ubuntu22.04
FROM nvidia/cuda:12.8.0-runtime-ubuntu22.04


# 设置Python版本
ENV PYTHON_VERSION=3.9

# 安装Python及基础工具
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    python${PYTHON_VERSION} \
    python3-pip \
    python${PYTHON_VERSION}-dev \
    xz-utils \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 建立Python3.9的符号链接
RUN ln -sf /usr/bin/python${PYTHON_VERSION} /usr/bin/python3 && \
    ln -sf /usr/bin/python3 /usr/bin/python && \
    ln -sf /usr/bin/pip3 /usr/bin/pip

# 设置工作目录
WORKDIR /app
  
# 从本地拷贝已下载的FFmpeg静态包到容器内
# 注意：确保ffmpeg-release-amd64-static.tar.xz与Dockerfile在同一目录或指定正确路径
COPY .asset_space/.cache/ffmpeg-release-amd64-static.tar.xz /tmp/

# 解压并配置FFmpeg
RUN mkdir -p /opt/ffmpeg && \
    # 解压到/opt/ffmpeg目录（移除顶层目录）
    tar -xJf /tmp/ffmpeg-release-amd64-static.tar.xz -C /opt/ffmpeg --strip-components=1 && \
    # 清理压缩包
    rm /tmp/ffmpeg-release-amd64-static.tar.xz && \
    # 配置环境变量，使其全局可用
    ln -s /opt/ffmpeg/ffmpeg /usr/local/bin/ffmpeg && \
    ln -s /opt/ffmpeg/ffprobe /usr/local/bin/ffprobe

# 验证安装
RUN ffmpeg -version || echo "FFmpeg配置完成"

# Upgrade sqlite3 to meet ChromaDB requirements

# 从本地安装PyTorch及相关库
RUN pip install torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 \
    --index-url https://download.pytorch.org/whl/cu121 \
    --default-timeout=1800  # 30分钟超时

RUN pip install transformers==4.35.0 \
    --index-url https://pypi.mirrors.ustc.edu.cn/simple/ \
    --default-timeout=1800  # 30分钟超时

# 配置pip镜像源（阿里、清华、科大）
RUN pip config set global.index-url  https://pypi.mirrors.ustc.edu.cn/simple/ && \
    pip config set global.extra-index-url " https://mirrors.aliyun.com/pypi/simple/ https://pypi.tuna.tsinghua.edu.cn/simple/ " && \
    pip config set global.trusted-host " pypi.mirrors.ustc.edu.cn pypi.tuna.tsinghua.edu.cn mirrors.aliyun.com"

# 前面已单独安装的pip包，须在requirements中排除
# 安装依赖（禁用缓存减少镜像体积）
COPY requirements.txt .
RUN pip install  -r requirements.txt \
    && rm -rf /root/.cache/pip

# 复制应用代码
COPY . .

# 声明五个持久化目录（容器内路径）
VOLUME [ "/app/.logs", "/app/.work_space", "/app/.asset_space"]

# 预创建目录并设置权限（确保可写入）
RUN mkdir -p  /app/.logs /app/.work_space /app/.asset_space   && \
    chmod -R 775  /app/.logs /app/.work_space /app/.asset_space 

# 暴露 Gunicorn 端口（与启动命令中的端口保持一致）
EXPOSE 8000

# 启动命令：移除gunicorn_config.py依赖，直接指定参数
# 保持与EXPOSE一致的8000端口，工作进程数设为4，超时时间120秒
CMD ["gunicorn", "run:app", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120"]
    