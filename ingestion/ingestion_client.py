import os
import argparse
import json
import numpy as np
from pathlib import Path
import grpc

import kvstore_pb2
import kvstore_pb2_grpc

# Derived from the environment variables (see devcontainer.json)
GRPC_SERVER_HOST = os.getenv("KVSTORE_HOST", "localhost")
GRPC_SERVER_PORT = int(os.getenv("KVSTORE_PORT", "50051"))

# Hardcoded path for simplicity
RAG_SOURCE_FOLDER = Path("/workspaces/project_1/ingestion/RAG/output")

def main():

    # Iterate over the RAG source folder to find any jsonl files
    print(f"Searching [{RAG_SOURCE_FOLDER}] for jsonl source files:")
    source_files = []
    for item in RAG_SOURCE_FOLDER.iterdir():
        if(item.is_file() and item.suffix == ".jsonl"):
            source_files.append(item)
            print(f"    Found: {item.name}")
    
    if len(source_files) == 0:
        print(f"    No source files found! Exiting")
        return
    
    # Derive the gRPC target URL from the environment variables
    grpc_target = f"{GRPC_SERVER_HOST}:{GRPC_SERVER_PORT}"

    # Attempt to connect to the gRPC Server to feed the RAG embeddings into it
    with grpc.insecure_channel(grpc_target) as channel:

        # Create a stub on the connected channel
        stub = kvstore_pb2_grpc.KeyValueStoreStub(channel)

        total = 0
        overwritten = 0

        # For each RAG source jsonl file:
        #   Iterate over all of the lines and "Put" the key-value into the server
        for f_path in source_files:
            with open(f_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    record = json.loads(line)

                    key = str(record["chunk_id"])
                    textbook_chunk = str(record["text"])
                    embedding_bytes = np.asarray(record["embedding"], dtype=np.float32).tobytes()

                    resp = stub.Put(
                        kvstore_pb2.PutRequest(
                            key = key,
                            textbook_chunk = textbook_chunk,
                            embedding = embedding_bytes,
                        )
                    )

                    total += 1
                    if resp.overwritten:
                        overwritten += 1
                
        print(f"Total Number of Put's:      [{total}]")
        print(f"Number of keys overwritten: [{overwritten}]")


if __name__ == "__main__":
    main()
