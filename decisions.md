# Key Decisions

## 1. In-memory SQLite for query execution
Each test case provides a schema and rows. The server builds a fresh SQLite in-memory database per request, inserts the provided rows, and executes queries against it. This gives real SQL semantics (joins, filters, aggregations) without any external database dependency.

## 2. Regex-based mutating statement detection
Before executing any SQL, the server checks whether the statement starts with a mutating keyword (INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, etc.) using a compiled regex. This is applied before SQLite ever sees the query so even clever obfuscation attempts are caught at the validation layer.

## 3. Automatic LIMIT injection
If a SELECT query has no LIMIT clause the server appends LIMIT 100. If the caller supplies a limit argument that value is used instead. This prevents runaway queries from returning unbounded result sets.

## 4. Clean tool separation
Each MCP tool (list_tables, describe_table, search_schema, run_readonly_query) is implemented as a separate function. SQL validation, schema access, and query execution are distinct code paths with no shared mutable state.

## 5. Safe error responses instead of exceptions
Unknown tables, invalid SQL, and unknown tool names all return structured error objects rather than raising exceptions. This ensures results.json always has one well-formed entry per input regardless of what the caller sends.
