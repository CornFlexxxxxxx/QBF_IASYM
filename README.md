# 🧠 QBF Logic System

A powerful **Quantified Boolean Formula (QBF)** reasoning system that combines the robust **TweetyProject** library with **Large Language Model (LLM)** integration for natural language processing.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![TweetyProject](https://img.shields.io/badge/TweetyProject-1.28-orange.svg)

## ✨ Features

- 🤖 **Natural Language to QBF**: Convert plain English statements to formal QBF formulas
- 🧮 **Formal QBF Reasoning**: Powered by TweetyProject's proven algorithms
- 🎯 **Real-time Evaluation**: Fast satisfiability checking with detailed analysis
- 🌐 **Interactive Web UI**: Beautiful Streamlit interface for easy interaction
- 📊 **Batch Processing**: Analyze multiple formulas simultaneously
- 📚 **Example Library**: Learn from classic QBF examples
- 🔧 **API Integration**: Support for multiple LLM providers (OpenAI, Anthropic, etc.)

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Java 8+** (for TweetyProject)
- **LLM API Key** (OpenAI, Anthropic, or similar)

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd QBF_Project
   ```

2. **Set up Conda environment**
   ```bash
   conda env create -f environment.yml
   conda activate qbf-logic
   ```

3. **Configure your API key**
   ```bash
   cp .env.template .env
   # Edit .env and add your API key:
   # OPENAI_API_KEY=your_api_key_here
   ```

4. **Verify setup**
   ```bash
   python test_system.py
   ```

5. **Launch the Web UI**
   ```bash
   streamlit run qbf_ui.py
   ```

## 📖 Usage

### Web Interface

The easiest way to use the system is through the interactive web UI:

```bash
streamlit run qbf_ui.py
```

Then open your browser to `http://localhost:8501`

### Command Line

#### Natural Language Query
```python
from qbf_system import QBFLogicSystem
from config import Config

system = QBFLogicSystem(
    jar_path=str(Config.JAR_PATH),
    llm_api_key=Config.get_api_key()
)

# Convert natural language to QBF
result = system.evaluate_text("Every student either passes or fails")
print(f"Generated QBF: {result['qbf_formula']}")
print(f"Result: {result['result']}")
```

#### Direct QBF Evaluation
```python
# Evaluate QBF directly
result = system.evaluate_qbf(
    formula_str="x | ~x",           # Tautology
    variables=["x"],
    quantifiers=[("forall", "x")]
)
print(f"Result: {result['result']}")  # SATISFIABLE
```

## 🧮 QBF Syntax

### Logical Operators
- `&` - AND (conjunction)
- `|` - OR (disjunction)  
- `~` - NOT (negation)
- `()` - Grouping

### Quantifiers
- `exists` - Existential quantification (∃)
- `forall` - Universal quantification (∀)

### Examples

| Formula | Description | Expected Result |
|---------|-------------|-----------------|
| `∀x (x ∨ ¬x)` | Tautology | SATISFIABLE |
| `∀x (x ∧ ¬x)` | Contradiction | UNSATISFIABLE |
| `∃x ∀y (x ∨ y)` | Existential choice | SATISFIABLE |

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Natural       │    │    QBF       │    │  TweetyProject  │
│   Language      │───▶│   System     │───▶│   Reasoning     │
│   Input         │    │              │    │   Engine        │
└─────────────────┘    └──────────────┘    └─────────────────┘
        │                       │                     │
        ▼                       ▼                     ▼
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   LLM API       │    │   Python     │    │   Java Bridge   │
│   (OpenAI, etc) │    │   Controller │    │   (.qbf format) │
└─────────────────┘    └──────────────┘    └─────────────────┘
```

## 📁 Project Structure

```
QBF_Project/
├── 📄 qbf_system.py              # Core QBF reasoning system
├── 🎨 qbf_ui.py                  # Streamlit web interface
├── ⚙️ config.py                  # Configuration management
├── 🧪 test_system.py             # System tests
├── 📚 examples/                  # Example scripts
│   └── simple_examples.py
├── 🔧 tweety_bridge/             # Java bridge (auto-generated)
├── 📋 requirements.txt           # Python dependencies
├── 🐍 environment.yml            # Conda environment
├── ⚙️ .env                       # API keys (not in git)
├── 📖 README.md                  # This file
└── 🏺 org.tweetyproject.logics.qbf-1.28-with-dependencies.jar
```

## 🔧 Configuration

### Environment Variables (.env)
```bash
# LLM API Configuration
OPENAI_API_KEY=your_openai_api_key_here
# ANTHROPIC_API_KEY=your_anthropic_key_here

# TweetyProject Configuration  
TWEETY_JAR_PATH=org.tweetyproject.logics.qbf-1.28-with-dependencies.jar

# System Settings
SOLVER_TIMEOUT=30
LOG_LEVEL=INFO
```

### Supported LLM Providers
- **OpenAI** (GPT-3.5, GPT-4)
- **Anthropic** (Claude)
- **Google** (Gemini)
- Custom endpoints

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Basic system test
python test_system.py

# Run examples
python examples/simple_examples.py

# Test specific components
python debug_bridge.py
```

### Expected Test Results
```
✅ TweetyProject Compilation: PASS
✅ QBF Bridge: PASS  
✅ Complete System: PASS
✅ Natural Language: PASS
```

## 🎯 Use Cases

### Academic Research
- **Logic Education**: Teach QBF concepts interactively
- **Research Validation**: Verify QBF-based algorithms
- **Comparative Studies**: Benchmark different reasoning approaches

### AI & Reasoning
- **Planning Problems**: Model sequential decision making
- **Game Theory**: Analyze strategic interactions
- **Verification**: Formal system verification tasks

### Natural Language Processing
- **Logic Extraction**: Convert statements to formal logic
- **Argument Analysis**: Evaluate logical arguments
- **Knowledge Representation**: Model complex relationships

## 🚨 Troubleshooting

### Common Issues

#### Java Not Found
```bash
# Install Java (Ubuntu/Debian)
sudo apt-get install openjdk-11-jdk

# Install Java (macOS)
brew install openjdk@11
```

#### TweetyProject Compilation Errors
```bash
# Verify Java version
java -version

# Test JAR directly
java -cp org.tweetyproject.logics.qbf-1.28-with-dependencies.jar org.tweetyproject.logics.qbf.examples.QbfExample
```

#### API Key Issues
```bash
# Check .env file exists and is properly formatted
cat .env

# Verify API key is loaded
python -c "from config import Config; print('API Key:', bool(Config.get_api_key()))"
```

#### Bridge Compilation Failed
```bash
# Clean and rebuild bridge
rm -rf tweety_bridge/
python test_system.py
```

### Debug Mode

Enable verbose logging:
```bash
export LOG_LEVEL=DEBUG
python qbf_system.py
```

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**: Add features, fix bugs, improve docs
4. **Add tests**: Ensure your changes are tested
5. **Commit**: `git commit -m 'Add amazing feature'`
6. **Push**: `git push origin feature/amazing-feature`
7. **Submit a Pull Request**

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest black flake8

# Run linting
black .
flake8 .

# Run tests
pytest tests/
```

## 📚 References

- **TweetyProject**: [http://tweetyproject.org/](http://tweetyproject.org/)
- **QBF Theory**: [Wikipedia - Quantified Boolean Formula](https://en.wikipedia.org/wiki/True_quantified_Boolean_formula)
- **Streamlit**: [https://streamlit.io/](https://streamlit.io/)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **TweetyProject Team** for the excellent QBF reasoning library
- **Streamlit** for the amazing web app framework
- **OpenAI/Anthropic** for LLM API services
- **EPITA** for supporting this research project

## 📧 Contact

- **Author**: Gabriel Monteillard
- **Institution**: EPITA - ING2 SCIA IASY
- **Project**: QBF Logic System with LLM Integration

---

<div align="center">

**[⬆ Back to Top](#-qbf-logic-system)**

Made with ❤️ by Gabriel Monteillard | EPITA ING2 SCIA IASY

</div>