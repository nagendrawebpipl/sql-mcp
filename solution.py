#!/usr/bin/env python3
import json
import os
import re
import sqlite3
import sys
from pathlib import Path

TEST_INPUTS_PATH = Path(os.environ.get("TEST_INPUTS_PATH", "test_inputs.json"))
RESULTS_PATH     = Path(os.environ.get("RESULTS_PATH",     "results.json"))
DEFAULT_LIMIT    = 100

MUTATING_KEYWORDS = re.compile(
    r"^\s*(insert|update|delete|drop|alter|create|truncate|replace|merge"
    r"|grant|revoke|call|exec|execute|pragma|attach|detach)\b",
    re.IGNORECASE,
)

def is_readonly(sql):
    return not bool(MUTATING_KEYWORDS.match(sql.strip()))

def build_db(schema):
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    tables = schema.get("tables", [])
    rows   = schema.get("rows", {})
    for table in tables:
        name    = table["name"]
        columns = table["columns"]
        col_defs = ", ".join(f'"{c}" TEXT' for c in columns)
        cur.execute(f'CREATE TABLE IF NOT EXISTS "{name}" ({col_defs})')
        for row in rows.get(name, []):
            placeholders = ", ".join("?" for _ in columns)
            values = [str(row.get(c, "")) for c in columns]
            cur.execute(f'INSERT INTO "{name}" VALUES ({placeholders})', values)
    conn.commit()
    return conn

def tool_list_tables(conn, schema, args):
    tables = [t["name"] for t in schema.get("tables", [])]
    return {"tables": tables}

def tool_describe_table(conn, schema, args):
    table_name = args.get("table", "")
    tables     = {t["name"]: t for t in schema.get("tables", [])}
    if table_name not in tables:
        return {"error": f"Table '{table_name}' not found"}
    return {"table": table_name, "columns": tables[table_name]["columns"]}

def tool_search_schema(conn, schema, args):
    query   = args.get("query", "").lower()
    matches = []
    for table in schema.get("tables", []):
        for col in table["columns"]:
            if query in col.lower() or query in table["name"].lower():
                matches.append({"table": table["name"], "column": col})
    return {"matches": matches}

def tool_run_readonly_query(conn, schema, args):
    sql   = args.get("sql", "").strip()
    limit = int(args.get("limit", DEFAULT_LIMIT))
    if not sql:
        return {"error": "No SQL provided"}
    if not is_readonly(sql):
        return {"error": "Mutating SQL statements are not allowed. Only SELECT queries are permitted."}
    if "LIMIT" not in sql.upper():
        sql = f"{sql} LIMIT {limit}"
    try:
        cur = conn.cursor()
        cur.execute(sql)
        column_names = [d[0] for d in cur.description] if cur.description else []
        raw_rows     = cur.fetchall()
        rows         = [dict(zip(column_names, row)) for row in raw_rows]
        return {"columns": column_names, "rows": rows, "count": len(rows)}
    except sqlite3.Error as exc:
        return {"error": f"SQL error: {exc}"}

TOOLS = {
    "list_tables":        tool_list_tables,
    "describe_table":     tool_describe_table,
    "search_schema":      tool_search_schema,
    "run_readonly_query": tool_run_readonly_query,
}

def process_item(item):
    inp        = item.get("input", item)
    schema     = inp.get("schema", {})
    tool_calls = inp.get("tool_calls", [])
    conn       = build_db(schema)
    results    = []
    for call in tool_calls:
        tool_name = call.get("tool", "")
        args      = call.get("args", {})
        if tool_name not in TOOLS:
            results.append({"tool": tool_name, "result": {"error": f"Unknown tool '{tool_name}'"}})
        else:
            try:
                result = TOOLS[tool_name](conn, schema, args)
                results.append({"tool": tool_name, "result": result})
            except Exception as exc:
                results.append({"tool": tool_name, "result": {"error": str(exc)}})
    conn.close()
    if len(results) == 1:
        return {"id": item["id"], "output": results[0]["result"]}
    return {"id": item["id"], "output": {"tool_results": results}}

def main():
    if not TEST_INPUTS_PATH.exists():
        print(f"ERROR: {TEST_INPUTS_PATH} not found", file=sys.stderr)
        sys.exit(1)
    test_inputs = json.loads(TEST_INPUTS_PATH.read_text())
    results     = []
    total       = len(test_inputs)
    for idx, item in enumerate(test_inputs, 1):
        print(f"[{idx}/{total}] Processing {item['id']} ...")
        try:
            result = process_item(item)
            results.append(result)
            print(f"  Done: {str(result['output'])[:80]}")
        except Exception as exc:
            print(f"  Error: {exc}", file=sys.stderr)
            results.append({"id": item["id"], "output": {"error": str(exc)}})
    RESULTS_PATH.write_text(json.dumps(results, indent=2))
    print(f"\nDone - {len(results)} results written to {RESULTS_PATH}")

if __name__ == "__main__":
    main()

