# 🚀 Attack Chain Reconstruction Engine for Custom Scenarios

This project is an automated state-search and attack-chain reconstruction engine based on Docker and Python, designed to build vulnerability discovery and exploitation flows across various service scenarios such as ElasticSearch. Users can extend their own testing environments through custom API documentation, configuration files, and tooling.

---

## 📦 Environment Requirements

- **Python Version**: `3.13`
- **Operating System**: Linux / macOS / Windows (Docker support required)

---

## 🛠 Install Dependencies

Make sure to create a virtual environment (recommended) and install the required libraries:

```bash
pip install -r requirements.txt
```

---

## ▶️ Quick Start

Run the state-search process using the built-in ElasticSearch scenario:

```bash
python3 main.py   --config-path ./example/elastic_search/config.toml   --docker-compose-path ./example/elastic_search/docker-compose.yml
```

Results will be saved to:

```
./success
```

---

## 🧪 Creating a Custom Test Scenario (`test`)

If you need to run a custom service scenario (e.g., `test`), follow the structure used in the `./example` directory. Your custom scenario must include the following files:

| Required File     | Path Example |
|-------------------|--------------|
| 1️⃣ API Documentation | `./example/test/api_docs/api_doc.py` |
| 2️⃣ Configuration File | `./example/test/config.toml` |
| 3️⃣ Docker Compose File | `./example/test/docker-compose.yml` |
| 4️⃣ Custom Tools | `./example/test/tool.py` |
| 5️⃣ Predefined Data Directory | `./example/test/predefined/` |

---

## 🏗 Generating Predefined Files

The contents of the `predefined` directory must be generated using a data collector script. To do this:

1️⃣ Write your own gatherer script based on the following example:  
```
./example/test/docker/es_gatherable.py
./example/test/docker/app/util.py
./example/test/docker/app/app.py
```

2️⃣ Run the script to generate predefined data:

```bash
python3 ./example/test/docker/es_gatherable.py
```

Generated files will be stored in:

```
./example/test/predefined/
```

---

## 📁 Example Directory Structure

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

## 📝 Usage Tips

- Run the official scenarios first to understand output formats.  
- Ensure Docker services start properly during custom scenario execution.
- All request and response logs are automatically recorded for analysis.

---

## 🤝 Contributing & Feedback

Issues and Pull Requests are welcome! Share your custom scenarios or improvements with the community.

---

## 📜 License

This project uses either the MIT or Apache-2.0 license by default (modify according to your needs).
