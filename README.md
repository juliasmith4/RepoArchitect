# RepoArchitect

RepoArchitect is a full-stack software architecture analysis tool for Python repositories. It uses Python's AST module to statically analyze source code, build dependency relationships, calculate architecture metrics, and generate AI-assisted summaries of a repository's structure.

The project is still in development.

## Features

* Parses Python files using the built-in `ast` module
* Extracts functions, classes, imports, decorators, function calls, assignments, and return information
* Builds dependency graphs between modules
* Classifies dependencies as internal, external, or unresolved
* Calculates module-level architecture metrics
* Uses Gemini to generate architecture summaries and code-quality insights
* Includes automated tests for parsing, graph construction, dependency analysis, and AI integration

## Tech Stack

### Backend

* Python
* FastAPI
* PostgreSQL
* SQLAlchemy
* Alembic
* Pytest

### Frontend

* React
* TypeScript
* Vite
* TanStack Router

### AI

* Gemini API

### Development / Deployment

* Docker / Podman
* Google Cloud Run
* Google Cloud SQL

## How It Works

The analysis pipeline currently works roughly like this:

1. A Python repository is provided for analysis.
2. Python source files are parsed using the AST module.
3. RepoArchitect extracts code structure and relationships from each file.
4. Module dependencies are added to a dependency graph.
5. The graph is analyzed to calculate architecture and dependency metrics.
6. Parsed repository information is prepared for Gemini.
7. Gemini generates higher-level architecture summaries and recommendations.
8. Results are returned through the FastAPI backend for use by the frontend.

## Testing

The backend currently includes a Pytest suite with more than 130 tests covering areas such as:

* AST parsing
* Function and class extraction
* Import handling
* Dependency graph construction
* Dependency classification
* Architecture metrics
* AI analysis integration

Run the backend tests with:

```bash
cd backend
python -m pytest
```

## Project Structure

```text
RepoArchitect/
├── backend/
│   ├── app/
│   └── tests/
├── frontend/
│   └── src/
├── docs/
├── compose.yml
└── README.md
```

## Current Status

RepoArchitect is actively being developed.

The core parsing, dependency graph, graph analysis, and AI analysis components are implemented and tested. Work is continuing on the full repository-analysis workflow, frontend integration, persistence, and deployment.

## Running Locally

Setup instructions are still being finalized as the application structure changes.

For backend development:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m pytest
```

The full application is intended to run using the included container configuration once the frontend and backend integration is complete.

## Planned Work

Some of the next areas of development include:

* Complete repository input and analysis workflow
* Persist analysis results in PostgreSQL
* Expand the React frontend
* Improve visualization of dependency relationships
* Add additional architecture metrics and issue detection
* Deploy the completed application to Google Cloud

## Why I Built It

RepoArchitect started as a project to explore how static analysis, software architecture, and AI could be combined to make unfamiliar codebases easier to understand.

Instead of sending raw source code directly to an AI model, the goal is to first extract structured information from the repository and use that structure to produce more useful architecture-level analysis.
