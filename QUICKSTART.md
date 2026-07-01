# Quick Start Commands

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your AWS credentials.
# Your instructor may provide credentials if you do not have AWS access.

# Run exercises in order
python exercise-1-data-science/starter_code.py
python exercise-2-data-engineering/embeddings_pipeline.py
python exercise-3-app-development/server.py

# Or run individually from each exercise directory
cd exercise-1-data-science && python starter_code.py
cd exercise-2-data-engineering && python embeddings_pipeline.py
cd exercise-3-app-development && python server.py
```
