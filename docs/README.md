# Project 1: gRPC Key-Value Store for Context Serving

**Course:** CSCI 5105 - Introduction to Distributed Systems  
**Semester:** Spring 2026  
**Instructor:** Jon Weissman  
**Students:** Youssef Abdulle & William Walker

---

## 1. Running the Project

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Regenerate gRPC bindings** (only needed if you modify `kvstore.proto`)

   ```bash
   bash gRPC_KVS/scripts/gen_proto.sh
   ```

3. **Start the server**

   ```bash
   cd server
   python server.py
   ```

4. **Run the ingestion client** to populate the store with the textbook chunks

   ```bash
   cd ingestion
   python ingestion_client.py
   ```

5. **Start the MCP server**

   Open `.vscode/mcp.json` in VS Code and click **Start** above `csci5105-rag-poc`.

---

## 2. Running the Tests

Make sure the server is running first, then from the project root:

```bash
python tests/test_rpc.py
```

Each test function prints `PASSED: <RPC>` when it succeeds. No external test framework was used.

If all tests pass, the output will look like this:

    PASSED: Put
    PASSED: GetText
    PASSED: Delete
    PASSED: List
    PASSED: Health
    PASSED: StreamEmbeddings

    ALL TESTS PASSED

We test all five RPCs: `Put`, `GetText`, `Delete`, `List`, and `Health`. Each test cleans up its own keys before running so a leftover `kvstore.pkl` from a previous session won't cause false failures. We covered the non-obvious cases too, not just the happy path, things like overwriting an existing key, deleting a key that was never inserted, calling delete twice on the same key, putting a key back after deleting it, and making sure `key_count` in `Health` stays accurate across puts and deletes.


Each RPC is tested independently using a Python gRPC client stub connected to a running server instance. The tests verify both return values and the resulting internal state of the store. This ensures that RPC responses are correct and that state transitions (inserts, deletes, overwrites) behave as expected.

---

## 3. What We Did

We completed three parts of the project.

### `kvstore.proto`

The provided file had `Put` and `StreamEmbeddings` already defined. We added the four remaining RPCs and their message types:

| RPC | Request Fields | Response Fields |
| --- | --- | --- |
| `GetText` | `key` (string) | `found` (bool), `textbook_chunk` (string) |
| `Delete` | `key` (string) | `deleted` (bool) |
| `List` | *(none)* | `keys` (repeated string) |
| `Health` | *(none)* | `server_name`, `server_version`, `key_count` (uint64) |

### `server/server.py`

We implemented the four missing RPC handlers:

- **`GetText`** looks up the key in `textbook_chunks` under the lock and returns `found=False` with an empty string if it's not there.
- **`Delete`** removes the key from both dicts if it exists and returns whether anything was actually deleted.
- **`List`** snapshots the keys from `textbook_chunks` under the lock and returns them.
- **`Health`** returns a hardcoded server name and version along with the current `len(textbook_chunks)` as the key count.

### `mcp_server/mcp_server.py`

We implemented `get_text_from_keys`, which takes the list of keys identified by the MCP server's local embedding search and calls `GetText` on each one to fetch the corresponding text chunks to return as context.

---

## 4. Design Choices

**Single `RLock` over both dicts.** We used one lock to protect both `textbook_chunks` and `embeddings` rather than giving each its own lock. Some operations touch both dicts together (like `Put` and `Delete`), so two separate locks would risk acquiring them in different orders across handlers. We went with `RLock` over a plain `Lock` as a precaution since it lets the same thread re-acquire without deadlocking, which is useful if helper methods ever get called from within a locked section.

**Snapshot before streaming.** `StreamEmbeddings` snapshots the embeddings dict while holding the lock and then yields entries after releasing it. The alternative would be holding the lock for the entire stream, which could block writes for a long time if there are a lot of entries.
