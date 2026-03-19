# Contributing to Army81

## How to Add a New Agent

```bash
python scripts/add_agent.py \
  --id A82 \
  --name "Agent Name" \
  --category cat2_science \
  --model gemini-flash \
  --tools web_search,file_ops
```

## How to Add a New Tool

1. Create `tools/your_tool.py`
2. Register in `tools/registry.py`
3. Add to agent JSON files that need it

## How to Run Tests

```bash
python -m pytest tests/ -v
```

## How to Report Issues

Open a GitHub Issue with:
- What you expected
- What happened
- Steps to reproduce
- Error logs (from `logs/` directory)

## Code Style
- Python 3.11+
- Arabic comments welcome
- Type hints encouraged
