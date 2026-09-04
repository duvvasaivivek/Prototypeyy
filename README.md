# Zero-Trust Privacy Gateway for Browser Agents 🛡️

**SIH Problem Statement:** On-device Visual Perception for Light-weight Browser Agents (SIH26171)  
**Team Name:** ShatAvaran  
**Theme:** Smart Automation

## 📖 Overview
Autonomous browser agents can automate complex web tasks, but they expose highly sensitive Personal Identifiable Information (PII) like Aadhaar, PAN, and credentials to cloud AI models. 

This project implements a **Zero-Trust Privacy Gateway** that creates a local security boundary between the browser and the cloud AI. It combines DOM extraction, multi-layer PII detection using Microsoft Presidio, semantic tokenization, and on-device policy enforcement. The cloud AI receives only a sanitized tokenized context, ensuring absolute privacy while still allowing the AI to reason and automate complex web tasks.

## 🏗️ Architecture
The system consists of two main components:
1. **Chrome Extension (`/extension`)**: A lightweight React-based Chrome extension that seamlessly captures the DOM, extracts visual data, and natively executes Javascript mouse events to bypass anti-bot systems like React Synthetic Events.
2. **Local Python Gateway (`/local-agent`)**: A fast asynchronous FastAPI backend that acts as the Privacy Firewall. It uses Microsoft Presidio for NLP-based NER (Named Entity Recognition), EasyOCR for visual perception fallbacks, and a Needle2-simulated Outbound Inspector.

## ✨ Key Features
- **Zero-Trust Boundaries:** Cloud AI only sees semantic tokens (`<EMAIL_TOKEN>`), never the actual raw text.
- **On-Device NLP:** Microsoft Presidio runs locally to perform Named Entity Recognition.
- **Anti-Bot Evasion:** Native mouse event simulation circumvents React/Vue synthetic event tracking.
- **Dynamic OCR Fallback:** AI can interact with purely visual canvas elements by using fallback text matching.

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+
- Chrome Browser

### 1. Start the Local Privacy Gateway (Backend)
Navigate to the `local-agent` directory, create a virtual environment, install dependencies, and run the FastAPI server:

```powershell
cd local-agent
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```
*Note: Make sure to create a `.env` file from the `.env.example` and add your `GEMINI_API_KEY`!*

### 2. Load the Chrome Extension (Frontend)
1. Navigate to the `extension` directory and build the project:
```powershell
cd extension
npm install
npm run build
```
2. Open Google Chrome and go to `chrome://extensions/`
3. Toggle **Developer mode** on in the top right corner.
4. Click **Load unpacked** and select the `extension/dist` folder.

## 📊 Live Privacy Dashboard
While the local agent is running, you can monitor real-time tokenization and privacy metrics by navigating to:
`http://127.0.0.1:8000`

## 🛠️ Tech Stack
- **Frontend:** React, TypeScript, Vite, Tailwind CSS, Chrome Extension API (Manifest V3)
- **Backend:** Python, FastAPI, Uvicorn, Asyncio
- **Privacy Engine:** Microsoft Presidio Analyzer (NLP NER), Regex Policies
- **Perception & Execution:** EasyOCR, Native JS MouseEvents
- **AI Reasoning:** Google Gemini 1.5/2.5 Flash

## ⚠️ Disclaimer
This is a prototype built for the Smart India Hackathon (SIH26171). It is not intended for production use without further security auditing and integration with production LLM environments.

---
*Built with ❤️ for SIH26171 by Team ShatAvaran*
