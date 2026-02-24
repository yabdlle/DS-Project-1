import sys
sys.path.insert(0, "mcp_server/")
import mcp_server
import random
import json

jsonl_path = "ingestion/RAG/output/textbook_distributed_systems_v3.03_vectorized.jsonl"

def test_get_text_from_keys():
    print("TESTING: get_text_from_keys()")
    texts = {}
    with open(jsonl_path, 'r') as f:
        for l in f:
            record = json.loads(l)
            texts[record['chunk_id']] = record['text']

    def check_recall():
        print("    TESTING: check_recall()")
        for i in range(5):
            random.seed(i)
            keys = list(texts.keys())
            random.shuffle(keys)
            keys = keys[:len(keys) // 2] # take random subset of half the keys
            values = {texts[k] for k in keys}
            assert sorted(mcp_server.get_text_from_keys(keys)) == sorted(values), "FAILED: Texts retrieved do not match chunk ids"
        print("    PASSED: check_recall()")

    def check_ordering():
        print("    TESTING: check_ordering()")
        for i in range(5):
            random.seed(i)
            keys = list(texts.keys())
            random.shuffle(keys)
            values = [texts[k] for k in keys]
            assert values == mcp_server.get_text_from_keys(keys), "Keys and values did not agree"
        print("    PASSED: check_ordering()")

    def check_not_found():
        print("    TESTING: check_not_found()")
        fake_keys = ["This is definitely not a key", "Not a key either", "I love distributed systems!"]
        assert all(res == '' for res in mcp_server.get_text_from_keys(fake_keys))
        print("    PASSED: check_not_found()")
    
    check_recall()
    check_ordering()
    check_not_found()
    print("PASSED: get_text_from_keys()")

if __name__ == '__main__':
    test_get_text_from_keys()
    print("\nALL TESTS PASSED")
