# ProteinCraft
**Engineer better proteins with AI reasoning.**

ProteinCraft is a production-grade full-stack platform that combines large language models for biology (ESM2) with multi-modal reasoning models (Gemini 2.5 Flash) to design, optimize, and rank protein sequences.

![Architecture overview placeholder]

## Features
- **ESM2 Mutagenesis**: Extracts hidden-state embeddings and performs masked-language model scoring to generate biophysically plausible variants.
- **Gemini Reasoning**: Uses Gemini 2.5 Flash strictly as a logical ranking and explanation layer to select the best candidates based on computed proxies (NOT as a scientific predictor).
- **Biophysical Properties**: On-the-fly calculation of instability, pI, molecular weight, and aromaticity using Biopython.
- **Structure Prediction**: Integrates with ESMFold via the ESM Metagenomic Atlas API (or HuggingFace Inference API) for rapid 3D structure generation.
- **Full-stack Architecture**: Next.js 14 frontend (Tailwind CSS, Glassmorphism, Mol* Viewer) powered by an asynchronous FastAPI backend (PostgreSQL).

## Quick Start (Docker)

Ensure you have Docker and Docker Compose installed.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/proteincraft/proteincraft.git
   cd proteincraft
   ```

2. **Configure environment:**
   Copy the example environment variables and insert your Gemini API key.
   ```bash
   cp .env.example .env
   # Edit .env and set GEMINI_API_KEY
   ```

3. **Launch the stack:**
   ```bash
   docker-compose up --build
   ```

4. **Access the application:**
   - Frontend UI: http://localhost:3000
   - Backend API Docs (Swagger): http://localhost:8000/docs

## API Endpoints

- `POST /design-sequence`: Core endpoint. Accepts `sequence` or `fasta_content`. Returns ranked candidate variants.
- `POST /predict-properties`: Computes biophysical properties and ESM2 log-likelihood for a given sequence.
- `POST /structure`: Submits a sequence to ESMFold and returns the PDB format string.
- `POST /batch-design`: Concurrent processing of multiple sequences.
- `GET /protein/{job_id}`: Retrieve past design jobs from the PostgreSQL database.

## Architecture

* **Backend**: FastAPI, SQLAlchemy (Async), PostgreSQL, PyTorch, Transformers, Biopython, Google GenAI SDK.
* **Frontend**: Next.js 14, React 18, Tailwind CSS, Radix UI, Mol* (structure viewer).

## Testing

The backend includes a comprehensive pytest suite (unit and integration tests).

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest
```
*(Note: Tests use mocked ESM/Gemini calls by default to run instantly without GPU or API keys).*
