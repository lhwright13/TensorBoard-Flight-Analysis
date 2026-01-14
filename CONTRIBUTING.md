# Contributing to TensorBoard Flight Plugin

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Development Setup

### Prerequisites

- Python 3.8+
- Node.js 18+
- npm

### Installation

```bash
# Clone the repository
git clone https://github.com/lhwright13/tensorboard-flight-plugin.git
cd tensorboard-flight-plugin

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python package in development mode
pip install -e ".[dev]"

# Install frontend dependencies
cd src/frontend
npm install
```

### Building the Frontend

```bash
cd src/frontend
npm run build      # Production build
npm run dev        # Development mode with watch
```

### Running Tests

```bash
# Python tests
pytest tests/ -v

# Frontend type checking
cd src/frontend
npm run type-check
```

## Project Structure

```
tensorboard-flight-plugin/
├── src/
│   ├── tensorboard_flight/     # Python backend
│   │   ├── plugin.py           # TensorBoard plugin
│   │   ├── logger.py           # FlightLogger API
│   │   ├── data/               # Data schemas
│   │   ├── acmi/               # ACMI export support
│   │   └── static/             # Built frontend + models
│   └── frontend/               # React/Three.js frontend
│       └── src/
│           ├── components/     # React components
│           ├── store.ts        # Zustand state
│           └── types/          # TypeScript types
├── tests/                      # Python tests
├── examples/                   # Usage examples
└── docs/                       # Documentation
```

## Making Changes

### Code Style

**Python:**
- Follow PEP 8
- Use type hints
- Add docstrings to public functions

**TypeScript/React:**
- Use TypeScript strict mode
- Functional components with hooks
- JSDoc comments for complex functions

### Commit Messages

Use clear, descriptive commit messages:

```
feat: Add multi-aircraft rendering support
fix: Correct NED to Three.js coordinate transform
docs: Update API reference for FlightLogger
```

### Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Run tests (`pytest tests/` and `npm run type-check`)
5. Commit with a clear message
6. Push to your fork
7. Open a Pull Request

## Reporting Issues

When reporting bugs, please include:

- Python/Node.js version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages/logs

## Feature Requests

Open an issue with:

- Clear description of the feature
- Use case / motivation
- Proposed implementation (if any)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
