# 🚀 Fuzzing Framework for Custom Vulnerability Scenarios

本项目是一个基于 Docker 与 Python 的自动化 Fuzz 框架，支持针对多种服务场景（如 ElasticSearch 等）进行漏洞探测与利用流程的生成。用户可通过自定义 API 文档、配置文件与工具，扩展自身的测试环境。

---

## 📦 环境要求

- **Python 版本**：`3.13`
- **操作系统**：Linux / macOS / Windows (需支持 Docker)

---

## 🛠 安装依赖

请确保已创建虚拟环境（推荐）并安装依赖库：

```bash
pip install -r requirements.txt
```

---

## ▶️ 快速开始

使用已有的 ElasticSearch 场景运行 Fuzz：

```bash
python3 main.py \
  --config-path ./example/elastic_search/config.toml \
  --docker-compose-path ./example/elastic_search/docker-compose.yml
```

Fuzz 结果将保存至：

```
./success
```

---

## 🧪 创建自定义测试场景（test）

如果你需要 Fuzz 自定义服务场景（如 `test`），请参考 `./example` 下已有场景的结构，并至少包含以下文件：

| 必须文件 | 路径示例 |
|----------|----------|
| 1️⃣ API 文档 | `./example/test/api_docs/api_doc.py` |
| 2️⃣ 配置文件 | `./example/test/config.toml` |
| 3️⃣ Docker Compose | `./example/test/docker-compose.yml` |
| 4️⃣ 自定义工具 | `./example/test/tool.py` |
| 5️⃣ 预定义文件目录 | `./example/test/predefined/` |

---

## 🏗 生成预定义文件（Predefined）

自定义场景的 `predefined` 目录内容需通过收集器脚本生成。请仿照以下方式创建：

1️⃣ 编写符合你目标服务的采集脚本（参考以下示例）  
```
./example/test/docker/es_gatherable.py
./example/test/docker/app/util.py
./example/test/docker/app/app.py
```

2️⃣ 运行脚本生成预定义文件：

```bash
python3 ./example/test/docker/es_gatherable.py
```

生成的内容将保存在：

```
./example/test/predefined/
```

---

## 📁 目录结构示例

```plaintext
example/
├── test/
│   ├── api_docs/
│   │   └── api_doc.py
│   ├── config.toml
│   ├── docker-compose.yml
│   ├── tool.py
│   └── predefined/
|       └── final_attack.bin
|       └── attacked_state.bin
|       └── depended_state.bin
|       └── api_dependency_model.bin
|       └── seeds.bin
```

---

## 📝 使用建议

- 建议先运行官方场景，熟悉输入输出结构
- 自定义场景时确保 Docker 服务可正常启动
- 所有请求及响应日志将被自动记录用于分析

---

## 🤝 贡献与反馈

欢迎提交 Issue 或 Pull Request，分享更多服务场景与改进建议！

---

## 📜 许可证

本项目根据所含依赖和组件，默认使用 MIT 或 Apache-2.0 许可证（请根据实际项目调整）。
