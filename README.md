# Read-only SQL MCP Server

A safe read-only SQL server that exposes four MCP tools for schema inspection and SELECT queries.

## Tools

- list_tables: List all tables in the database
- describe_table: Get columns for a specific table
- search_schema: Search for columns by name
- run_readonly_query: Run a SELECT query (mutating SQL is rejected)

## Safety

- Mutating statements (INSERT, UPDATE, DELETE, DROP, etc.) return an error and are never executed
- Results are limited to 100 rows by default (overridable with limit arg)
- Unknown tables return a safe error response

## Running locally

export TEST_INPUTS_PATH=test_inputs.json
export RESULTS_PATH=results.json
python solution.py

## Docker

docker build -t sql-mcp .
docker run --rm -v $(pwd)/test_inputs.json:/workspace/test_inputs.json -v $(pwd):/workspace sql-mcp

See decisions.md for architectural choices.
