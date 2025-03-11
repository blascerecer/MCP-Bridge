# MCP-Bridge

MCP-Bridge is a tool designed to bridge communication between MCP components. This README provides instructions for installation and usage.

## Installation

To add MCP-Bridge to your project, follow these steps:

1. Add the repository as a Git submodule:
   ```bash
   git submodule add https://github.com/blascerecer/MCP-Bridge mcp-bridge/
   ```

2. Commit the changes to your repository:
   ```bash
   git add .gitmodules mcp-bridge/
   git commit -m "Add MCP-Bridge as a submodule"
   ```

3. Install dependencies using uv:
   ```bash
   uv sync
   ```

## Usage

To run MCP-Bridge, use the following command:

```bash
uv run mcp_bridge/main.py
```

## Requirements

- Git
- uv package manager
- Python 3.x (tested with Python 3.11.10)

## License

Please see the original repository for license information.

## Contributing

For contributions or issues, please visit the original repository at:
https://github.com/blascerecer/MCP-Bridge