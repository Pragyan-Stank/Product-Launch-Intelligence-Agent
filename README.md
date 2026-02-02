# 🚀 Product Launch Intelligence Agent

An **AI-powered multi-agent application** that delivers concise, evidence-backed product launch insights for **Product Managers, GTM teams, and Growth leaders**.

This app orchestrates multiple specialized agents to analyze:
- 🔍 Competitor launch strategies
- 💬 Market & customer sentiment
- 📈 Launch performance metrics

Powered by **Agno Agents**, **Groq LLMs**, and **Firecrawl** for real-time web intelligence.

---

## ✨ Features

### 🤖 Coordinated Multi-Agent System
- **Launch Analyst** – Competitive positioning, strengths & weaknesses
- **Sentiment Analyst** – Positive & negative market perception
- **Metrics Analyst** – Adoption, traction, and KPI signals

### 📊 Structured, Executive-Ready Outputs
- Markdown reports
- Tables, bullet summaries, and strategic takeaways
- Clear source attribution

---

## 🧱 Architecture Overview

```
User Input (Company Name)
        │
        ▼
┌──────────────────────────────┐
│   Product Intelligence Team  │
│  (Coordinator / Orchestrator)│
└───────────┬──────────────────┘
            │
   ┌────────┼─────────┐
   ▼        ▼         ▼
Launch   Sentiment   Metrics
Analyst  Analyst     Analyst
```

Each agent:
- Uses **Groq-hosted LLMs**
- Performs **controlled web search** via Firecrawl
- Returns concise, evidence-based bullets

---

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **Agent Framework**: Agno
- **LLM Provider**: Groq (`openai/gpt-oss-120b`)
- **Web Search**: Firecrawl
- **Config Management**: python-dotenv

---

## 📦 Installation

### 1️⃣ Clone the repository
```bash
git clone https://github.com/your-username/product-launch-intelligence-agent.git
cd product-launch-intelligence-agent
```

### 2️⃣ Create virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### 3️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

---

## 🔑 Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
FIRECRAWL_API_KEY=your_firecrawl_api_key
```

You can also enter keys directly in the Streamlit sidebar.

---

## ▶️ Run the Application

```bash
streamlit run app.py
```

Then open:
```
http://localhost:8501
```

---

## 🧭 How to Use

1. Enter **Groq** and **Firecrawl** API keys in the sidebar
2. Input a **company name**
3. Choose an analysis tab:
   - 🔍 Competitor Analysis
   - 💬 Market Sentiment
   - 📈 Launch Metrics
4. Click **Analyze**
5. Review structured, decision-ready insights

---

## 🧠 Ideal For

- Product Managers
- GTM & Product Marketing teams
- Founders & Strategy teams
- Competitive intelligence workflows



- **Streamlit** – Rapid UI development
