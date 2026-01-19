# Python Ingest

This is the Python ingest flow. It reads `./policies/**/policies.pdf`
with `./policies/**/metadata.json`, chunks the text, generates embeddings, and upserts to Pinecone.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Set the following environment variables (you can put them in a local `.env` file):

```bash
PINECONE_SERVICE_URL="https://your-index-xxxxxx.svc.your-region.pinecone.io"
PINECONE_API_KEY="your-pinecone-api-key"
OPENAI_API_KEY="your-openai-api-key"
```

## Run

```bash
python ingest.py
```

Notes:
- The script expects the `policies` directory to exist at `ai_backends/ingest/policies`.
- Chunk size and overlap are configurable in `ingest.py` if you need different settings.
