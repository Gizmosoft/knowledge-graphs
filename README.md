# Knowledge Graphs

CLI tool that builds and explores a knowledge graph in **Neo4j AuraDB**. So far it focuses on mock employee/company/project data and interactive Cypher-backed lookups. Text-to-graph extraction is not wired up yet (`data/paragraphs.txt` exists as sample input for later work).

## What it does so far

1. **Mock graph generation** (`--generate`) — Creates a seeded dataset with Faker and loads it into Neo4j:
   - **200** people (`P0`…), **15** companies (`C0`…), **40** projects (`PR0`…)
   - Relationships: `WORKS_AT`, `OWNS`, `KNOWS`, `WORKS_ON`, `MANAGES`
   - Clears existing `:MockEntity` nodes before reload

2. **Interactive explorer** — After startup, a menu lets you:
   - **Find nodes by name** — Case-insensitive substring search (default if you press Enter)
   - **Find neighbors of a node** — Given an ID like `P1`, lists connected nodes and relationship types
   - **Exit**

## Project layout

| Path | Role |
|------|------|
| `main.py` | CLI entrypoint (`--generate` + explorer loop) |
| `graph_explorer.py` | Neo4j queries for name search and neighbors |
| `data/dataset_generator.py` | Mock graph generation + import |
| `constants.py` | Loads Neo4j settings from `.env` |
| `.env.example` | Template for required env vars |

## Run locally

### 1. Prerequisites

- Python 3.11+
- A [Neo4j Aura](https://console.neo4j.io/) instance (running, not paused)

### 2. Clone and set up a virtualenv

```bash
cd text-to-knowledge-graphs
python -m venv kb-venv
source kb-venv/bin/activate   # Windows: kb-venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment

Copy `.env.example` to `.env` and fill in your Aura credentials:

```bash
cp .env.example .env
```

| Variable | Description |
|----------|-------------|
| `NEO4J_INSTANCE_ID` | Database name used by the driver |
| `NEO4J_URI` | Connection URI, e.g. `neo4j+s://xxxx.databases.neo4j.io` |
| `NEO4J_USERNAME` | Aura username (often `neo4j`) |
| `NEO4J_PASSWORD` | Aura password |

Do not commit `.env` — it is gitignored.

### 4. Generate data and explore

```bash
# Load (or reload) the mock dataset, then open the explorer
python main.py --generate

# Explore an existing graph only
python main.py
```

In the explorer menu, choose `1` to search by name, `2` to inspect neighbors by node ID (`P0`, `C0`, `PR0`, …), or `3` to quit.
