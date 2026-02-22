import os
import threading
from concurrent import futures
import grpc
import signal
from pathlib import Path
import pickle
import sys

import kvstore_pb2
import kvstore_pb2_grpc

# Derived from the environment variables (see devcontainer.json)
GRPC_SERVER_PORT = int(os.getenv("KVSTORE_PORT", "50051"))

# Python Pickle disc file where we will dump and load our data when starting and ending
KV_STORE_DISK = Path(Path(__file__).parent, "kvstore.pkl")

class InMemoryKV(kvstore_pb2_grpc.KeyValueStoreServicer):

    def __init__(self):
        # Instantiate two dictionaries (hash tables) for the
        # the mapping of keys to textbook chunks and keys to embeddings

        self.textbook_chunks = {}   # key -> bytes (JSON)
        # key -> bytes (numpy array of numpy float-32's)
        self.embeddings = {}

        # Protects shared dicts
        self.lock = threading.RLock()

        # Attempt to load previous data from disk
        self.load_from_disk()

    def persist_to_disk(self):
        with self.lock:
            data = {
                "textbook_chunks": dict(self.textbook_chunks),
                "embeddings": dict(self.embeddings)
            }

        with open(KV_STORE_DISK, "wb") as f:
            pickle.dump(data, f)

        print(
            f"Dumped textbook_chunks & embeddings to disk via [{KV_STORE_DISK.name}]")

    def load_from_disk(self):
        if not KV_STORE_DISK.exists():
            return

        with open(KV_STORE_DISK, "rb") as f:
            data = pickle.load(f)

        with self.lock:
            self.textbook_chunks = data.get("textbook_chunks", {})
            self.embeddings = data.get("embeddings", {})

        print(
            f"Loaded textbook_chunks and embeddings from disk via [{KV_STORE_DISK.name}]")
        print(f"[{len(self.textbook_chunks)}] key/values loaded")

    def Put(self, request, context):
        with self.lock:
            # Set overwritten based on if the key exists in the dictionaries
            overwritten = (request.key in self.textbook_chunks) or (
                request.key in self.embeddings)

            # Update or add the textbook chunk and embedding into our dictionary
            self.textbook_chunks[request.key] = request.textbook_chunk
            self.embeddings[request.key] = request.embedding

        # Return the response
        return kvstore_pb2.PutResponse(overwritten=overwritten)

    def StreamEmbeddings(self, request, context):
        with self.lock:
            items = list(self.embeddings.items())
        for key, emb in items:
            yield kvstore_pb2.EmbeddingEntry(key=key, embedding=emb)

    def GetText(self, request, context):
        with self.lock:
            data = self.textbook_chunks.get(request.key)

        if data is None:
            return kvstore_pb2.GetTextResponse(found=False, textbook_chunk="")

        return kvstore_pb2.GetTextResponse(found=True, textbook_chunk=data)

    def Delete(self, request, context):
        with self.lock:
            data = request.key in self.textbook_chunks
            if data:
                del self.textbook_chunks[request.key]
                if request.key in self.embeddings:
                    del self.embeddings[request.key]
        return kvstore_pb2.DeleteResponse(deleted=data)

    def List(self, request, context):
        with self.lock:
            keys = list(self.textbook_chunks.keys())
        return kvstore_pb2.ListResponse(keys=keys)

    def Health(self, request, context):
        with self.lock:
            count = len(self.textbook_chunks)

        return kvstore_pb2.HealthResponse(
            server_name="InMemoryKVStore",
            server_version="v1",
            key_count=count
        )


def serve():
    # Single worker keeps semantics simple for now
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=8))
    kv = InMemoryKV()
    kvstore_pb2_grpc.add_KeyValueStoreServicer_to_server(kv, server)

    # Bind to all local interfaces (IPv4 + IPv6) with [::],
    # so clients can connect via localhost or other container addresses
    server.add_insecure_port(f"[::]:{GRPC_SERVER_PORT}")

    # Define a signal handler function to gracefully shut down the server
    def server_shutdown_sig_handler(signum, frame):
        print("shutting down server")
        kv.persist_to_disk()     # Dump the current KV-Store data to the disk
        server.stop(grace=1)     # allow in-flight RPCs to finish
        sys.exit(0)

    # Register the interrupt signal with our handler
    signal.signal(signal.SIGINT, server_shutdown_sig_handler)  # Ctrl+C

    # Start the server then wait for termination
    server.start()
    print(f"listening on :{GRPC_SERVER_PORT}")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()