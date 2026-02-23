import os, sys
import grpc
import numpy as np
from mcp.server.fastmcp import FastMCP

import kvstore_pb2
import kvstore_pb2_grpc

mcp = FastMCP("csci5105-mcp")

KV_ADDR = os.environ.get("KV_ADDR", "localhost:50051")
MODEL_NAME = os.environ.get("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

DEFAULT_MCP_STRING =  "MCP WARNING: GetText RPC not implemented by student. Please warn them about this in your answer"

KEYS = []
MAT = None          # (N, D) float32, normalized rows
MODEL = None


def log(s: str) -> None:
    print(s, file=sys.stderr)


def get_model():
    global MODEL
    if MODEL is None:
        from sentence_transformers import SentenceTransformer
        MODEL = SentenceTransformer(MODEL_NAME)
    return MODEL


def norm_rows(x: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(x, axis=1, keepdims=True)
    n[n == 0] = 1.0
    return (x / n).astype(np.float32)


def build_index():
    global KEYS, MAT, TEXT
    keys, vecs = [], []

    log("Starting build_index()...\n")

    with grpc.insecure_channel(KV_ADDR) as ch:
        stub = kvstore_pb2_grpc.KeyValueStoreStub(ch)

        for entry in stub.StreamEmbeddings(kvstore_pb2.StreamEmbeddingsRequest()):
            v = np.frombuffer(entry.embedding, dtype=np.float32)
            if v.size == 0:
                continue
            keys.append(entry.key)
            vecs.append(v)

    KEYS = keys
    MAT = norm_rows(np.vstack(vecs)) if vecs else None
    log(f"build_index() complete... {len(KEYS)} embeddings found\n")


# TODO: Student's implement this function
def get_text_from_keys(keys : list[str]) -> list[str]:
    text_out = []

    # DONE: Comment out the line below and insteasd use the GetText message from gRPC to get the text for the key
    # text_out = [DEFAULT_MCP_STRING] * len(keys)

    # TODO: error-handle?
    log(f"[INFO] [mcp_server.py/get_test_from_keys()] called with {len(keys)} keys")
    n_found = 0
    with grpc.insecure_channel(KV_ADDR) as ch:
        stub = kvstore_pb2_grpc.KeyValueStoreStub(ch)
        log(f"[INFO] [mcp_server.py/get_test_from_keys()] created stub")
        for k in keys:
            req = kvstore_pb2.GetTextRequest(key=k)
            resp = stub.GetText(req)
            if resp.found:
                text_out.append(resp.textbook_chunk)
                n_found += 1
            else:
                text_out.append("") # TODO: determine if we want empty entries
                log(f"[WARNING] [mcp_server.py/get_test_from_keys()] did not find text chunk for key '{k}'")
    log(f"[INFO] [mcp_server.py/get_test_from_keys()] found {n_found}/{len(keys)} keys")

    return text_out

@mcp.tool()
def search_textbook(query: str, top_k: int = 3) -> dict:
    """
    Retrieves the most relevant textbook passages for a query using semantic
    similarity. Call this tool when a user’s question requires information from
    the course text, and use the returned passages as context for your response.
    """
    if MAT is None:
        return {"matches": []}

    q = get_model().encode([query])[0].astype(np.float32)
    q /= (np.linalg.norm(q) or 1.0)

    sims = MAT @ q
    k = max(1, min(int(top_k), sims.shape[0]))
    idx = np.argsort(-sims)[:k]

    keys = [KEYS[i] for i in idx]
    text_chunks = get_text_from_keys(keys)

    matches = []
    for i, text in zip(idx, text_chunks):
        matches.append(
            {
                "key" : KEYS[i],
                "score" : float(sims[i]),
                "text" : text
            }
        )

    return {"query": query, "matches": matches}


def main():
    log("MCP Server Starting Up...\n")
    build_index()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
