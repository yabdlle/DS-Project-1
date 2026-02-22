import grpc
import kvstore_pb2
import kvstore_pb2_grpc


def get_stub():
    channel = grpc.insecure_channel("localhost:50051")
    return kvstore_pb2_grpc.KeyValueStoreStub(channel)


# ─────────────────────────────────────────────────────────────────────────────
# RPC: Put
# ─────────────────────────────────────────────────────────────────────────────
def test_Put(stub):
    stub.Delete(kvstore_pb2.DeleteRequest(key="put:new"))
    stub.Delete(kvstore_pb2.DeleteRequest(key="put:empty"))

    r = stub.Put(kvstore_pb2.PutRequest(key="put:new", textbook_chunk="hello", embedding=b"\x01"))
    assert r.overwritten is False, "new key should not be overwritten"

    r2 = stub.Put(kvstore_pb2.PutRequest(key="put:new", textbook_chunk="hello2", embedding=b"\x02"))
    assert r2.overwritten is True, "existing key should be overwritten"

    g = stub.GetText(kvstore_pb2.GetTextRequest(key="put:new"))
    assert g.textbook_chunk == "hello2", "value should be updated after overwrite"

    r3 = stub.Put(kvstore_pb2.PutRequest(key="put:empty", textbook_chunk="", embedding=b""))
    assert r3.overwritten is False
    g2 = stub.GetText(kvstore_pb2.GetTextRequest(key="put:empty"))
    assert g2.found is True and g2.textbook_chunk == ""

    print("PASSED: Put")


# ─────────────────────────────────────────────────────────────────────────────
# RPC: GetText
# ─────────────────────────────────────────────────────────────────────────────
def test_GetText(stub):
    stub.Delete(kvstore_pb2.DeleteRequest(key="get:exists"))
    stub.Delete(kvstore_pb2.DeleteRequest(key="get:missing"))

    stub.Put(kvstore_pb2.PutRequest(key="get:exists", textbook_chunk="my text", embedding=b"\xAA"))

    g = stub.GetText(kvstore_pb2.GetTextRequest(key="get:exists"))
    assert g.found is True, "existing key should be found"
    assert g.textbook_chunk == "my text", "should return correct chunk"

    g2 = stub.GetText(kvstore_pb2.GetTextRequest(key="get:missing"))
    assert g2.found is False, "missing key should not be found"
    assert g2.textbook_chunk == "", "missing key should return empty string"

    stub.Delete(kvstore_pb2.DeleteRequest(key="get:exists"))
    g3 = stub.GetText(kvstore_pb2.GetTextRequest(key="get:exists"))
    assert g3.found is False, "deleted key should not be found"

    print("PASSED: GetText")


# ─────────────────────────────────────────────────────────────────────────────
# RPC: Delete
# ─────────────────────────────────────────────────────────────────────────────
def test_Delete(stub):
    stub.Delete(kvstore_pb2.DeleteRequest(key="del:exists"))
    stub.Delete(kvstore_pb2.DeleteRequest(key="del:missing"))
    stub.Delete(kvstore_pb2.DeleteRequest(key="del:double"))
    stub.Delete(kvstore_pb2.DeleteRequest(key="del:reput"))

    stub.Put(kvstore_pb2.PutRequest(key="del:exists", textbook_chunk="bye", embedding=b"\x01"))
    stub.Put(kvstore_pb2.PutRequest(key="del:double", textbook_chunk="x",   embedding=b"\x01"))

    d = stub.Delete(kvstore_pb2.DeleteRequest(key="del:exists"))
    assert d.deleted is True, "existing key should be deleted"
    g = stub.GetText(kvstore_pb2.GetTextRequest(key="del:exists"))
    assert g.found is False, "key should be gone after delete"

    d2 = stub.Delete(kvstore_pb2.DeleteRequest(key="del:missing"))
    assert d2.deleted is False, "missing key should return deleted=False"

    stub.Delete(kvstore_pb2.DeleteRequest(key="del:double"))
    d3 = stub.Delete(kvstore_pb2.DeleteRequest(key="del:double"))
    assert d3.deleted is False, "second delete should return deleted=False"

    stub.Put(kvstore_pb2.PutRequest(key="del:reput", textbook_chunk="first", embedding=b"\x01"))
    stub.Delete(kvstore_pb2.DeleteRequest(key="del:reput"))
    r = stub.Put(kvstore_pb2.PutRequest(key="del:reput", textbook_chunk="second", embedding=b"\x02"))
    assert r.overwritten is False, "put after delete should be treated as new"
    g2 = stub.GetText(kvstore_pb2.GetTextRequest(key="del:reput"))
    assert g2.textbook_chunk == "second"

    print("PASSED: Delete")


# ─────────────────────────────────────────────────────────────────────────────
# RPC: List
# ─────────────────────────────────────────────────────────────────────────────
def test_List(stub):
    stub.Delete(kvstore_pb2.DeleteRequest(key="list:a"))
    stub.Delete(kvstore_pb2.DeleteRequest(key="list:b"))
    stub.Delete(kvstore_pb2.DeleteRequest(key="list:c"))

    for k in ["list:a", "list:b", "list:c"]:
        stub.Put(kvstore_pb2.PutRequest(key=k, textbook_chunk=k, embedding=b"\x01"))

    l = stub.List(kvstore_pb2.ListRequest())
    assert "list:a" in l.keys
    assert "list:b" in l.keys
    assert "list:c" in l.keys

    stub.Delete(kvstore_pb2.DeleteRequest(key="list:b"))
    l2 = stub.List(kvstore_pb2.ListRequest())
    assert "list:b" not in l2.keys, "deleted key should not appear in list"
    assert "list:a" in l2.keys and "list:c" in l2.keys, "non-deleted keys should remain"

    print("PASSED: List")


# ─────────────────────────────────────────────────────────────────────────────
# RPC: Health
# ─────────────────────────────────────────────────────────────────────────────
def test_Health(stub):
    stub.Delete(kvstore_pb2.DeleteRequest(key="health:probe"))

    h = stub.Health(kvstore_pb2.HealthRequest())
    assert len(h.server_name) > 0, "server_name should be non-empty"
    assert len(h.server_version) > 0, "server_version should be non-empty"
    assert h.key_count >= 0

    before = h.key_count

    stub.Put(kvstore_pb2.PutRequest(key="health:probe", textbook_chunk="x", embedding=b"\x01"))
    h2 = stub.Health(kvstore_pb2.HealthRequest())
    assert h2.key_count == before + 1, "key_count should increment after Put"

    stub.Put(kvstore_pb2.PutRequest(key="health:probe", textbook_chunk="y", embedding=b"\x02"))
    h3 = stub.Health(kvstore_pb2.HealthRequest())
    assert h3.key_count == before + 1, "key_count should not change on overwrite"

    stub.Delete(kvstore_pb2.DeleteRequest(key="health:probe"))
    h4 = stub.Health(kvstore_pb2.HealthRequest())
    assert h4.key_count == before, "key_count should decrement after Delete"

    print("PASSED: Health")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main():
    stub = get_stub()

    test_Put(stub)
    test_GetText(stub)
    test_Delete(stub)
    test_List(stub)
    test_Health(stub)

    print("\nALL TESTS PASSED")


if __name__ == "__main__":
    main()