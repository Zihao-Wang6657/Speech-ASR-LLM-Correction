# Running the Official FunASR Gradio Demo / 运行 FunASR 官方 Gradio Demo

## 中文说明

### 目标

本步骤的目标是：在本地成功运行 FunASR 官方 OpenAI-compatible API server 与 Gradio 前端，并完成一次中文语音识别测试。

该步骤用于确认本地环境、模型加载、音频解码和 API 调用能够正常工作。

### 项目路径

项目根目录：

```text
D:\Github_repo\Speech-Project
```

FunASR 官方代码路径：

```text
D:\Github_repo\Speech-Project\FunASR
```

### 环境信息

- 操作系统：Windows
- Conda 环境：funasr
- ASR 模型：sensevoice
- 后端 API 地址：http://localhost:8000
- Gradio 前端地址：http://127.0.0.1:7860
- 音频解码依赖：ffmpeg

### 启动后端 API server

在第一个 PowerShell 窗口中运行：

```powershell
conda activate funasr
cd D:\Github_repo\Speech-Project\FunASR\examples\openai_api
python server.py --model sensevoice --device cpu --port 8000
```

### 启动 Gradio 前端

在第二个 PowerShell 窗口中运行：

```powershell
conda activate funasr
cd D:\Github_repo\Speech-Project\FunASR\examples\openai_api
python gradio_app.py --base-url http://localhost:8000
```

### 测试样例

测试音频：

```text
data/mandarin/raw_audio/test_001.m4a
```

Gradio 截图：

```text
assets/Gradio_demo/test_001.png
```

参考文本：

```text
今天我们测试一下中文语音识别系统
```

识别结果：

```text
今天我们测试一下中文语音识别系统
```

### 结果

FunASR 官方 Gradio demo 已成功在本地运行，并完成了一条中文语音样例的识别。该步骤验证了本地环境、模型加载、音频解码和 API 调用均能正常工作。

---

## English Version

### Goal

The goal of this step is to run the official FunASR OpenAI-compatible API server and Gradio frontend locally, and verify Mandarin ASR with one test audio sample.

This step confirms that the local environment, model loading, audio decoding, and API call all work properly.

### Project Path

Project root:

```text
D:\Github_repo\Speech-Project
```

FunASR source code:

```text
D:\Github_repo\Speech-Project\FunASR
```

### Environment

- OS: Windows
- Conda environment: funasr
- ASR model: sensevoice
- Backend API: http://localhost:8000
- Gradio frontend: http://127.0.0.1:7860
- Audio decoding dependency: ffmpeg

### Start the Backend API Server

Run the following commands in the first PowerShell window:

```powershell
conda activate funasr
cd D:\Github_repo\Speech-Project\FunASR\examples\openai_api
python server.py --model sensevoice --device cpu --port 8000
```

### Start the Gradio Frontend

Run the following commands in the second PowerShell window:

```powershell
conda activate funasr
cd D:\Github_repo\Speech-Project\FunASR\examples\openai_api
python gradio_app.py --base-url http://localhost:8000
```

### Test Sample

Test audio:

```text
data/mandarin/raw_audio/test_001.m4a
```

Gradio screenshot:

```text
assets/Gradio_demo/test_001.png
```

Reference text:

```text
今天我们测试一下中文语音识别系统
```

ASR output:

```text
今天我们测试一下中文语音识别系统
```

### Result

The official FunASR Gradio demo was successfully launched locally. One Mandarin speech sample was recognized correctly, which verifies that the local environment, model loading, audio decoding, and API call all work properly.
