import json
from dataclasses import dataclass

import pytest

from wintoucher.util.json import JSONSerializableManager, TwoWayDict


class TestTwoWayDict:
    def test_set_and_get(self):
        d = TwoWayDict()
        d["a"] = 1
        assert d["a"] == 1

    def test_get_key_reverse_lookup(self):
        d = TwoWayDict()
        d["a"] = 1
        assert d.get_key(1) == "a"

    def test_contains(self):
        d = TwoWayDict()
        d["a"] = 1
        assert "a" in d
        assert "b" not in d

    def test_len(self):
        d = TwoWayDict()
        assert len(d) == 0
        d["a"] = 1
        assert len(d) == 1
        d["b"] = 2
        assert len(d) == 2

    def test_delete(self):
        d = TwoWayDict()
        d["a"] = 1
        del d["a"]
        assert "a" not in d
        assert len(d) == 0
        with pytest.raises(KeyError):
            d.get_key(1)

    def test_iter(self):
        d = TwoWayDict()
        d["a"] = 1
        d["b"] = 2
        assert set(d) == {"a", "b"}

    def test_items_keys_values(self):
        d = TwoWayDict()
        d["x"] = 10
        d["y"] = 20
        assert dict(d.items()) == {"x": 10, "y": 20}
        assert set(d.keys()) == {"x", "y"}
        assert set(d.values()) == {10, 20}

    def test_overwrite_key(self):
        d = TwoWayDict()
        d["a"] = 1
        d["a"] = 2
        assert d["a"] == 2
        assert d.get_key(2) == "a"


@dataclass
class SimpleObj:
    name: str
    value: int

    @classmethod
    def __json__(cls):
        return ("name", "value")


@dataclass
class NestedObj:
    label: str
    child: SimpleObj

    @classmethod
    def __json__(cls):
        return ("label", "child")


class TestJSONSerializableManager:
    def test_register_and_roundtrip_simple(self):
        mgr = JSONSerializableManager()
        mgr.register(SimpleObj)
        encoder = mgr.build_encoder()
        decoder = mgr.build_decoder()

        obj = SimpleObj(name="test", value=42)
        encoded = json.dumps(obj, cls=encoder)
        decoded = json.loads(encoded, cls=decoder)

        assert isinstance(decoded, SimpleObj)
        assert decoded.name == "test"
        assert decoded.value == 42

    def test_register_nested_objects(self):
        mgr = JSONSerializableManager()
        mgr.register(SimpleObj)
        mgr.register(NestedObj)
        encoder = mgr.build_encoder()
        decoder = mgr.build_decoder()

        obj = NestedObj(label="parent", child=SimpleObj(name="child", value=99))
        encoded = json.dumps(obj, cls=encoder)
        decoded = json.loads(encoded, cls=decoder)

        assert isinstance(decoded, NestedObj)
        assert isinstance(decoded.child, SimpleObj)
        assert decoded.child.value == 99

    def test_duplicate_signature_raises(self):
        mgr = JSONSerializableManager()
        mgr.register(SimpleObj)
        with pytest.raises(ValueError, match="same attribute signature"):
            mgr.register_special(str, ("name", "value"))

    def test_custom_encoder_decoder(self):
        mgr = JSONSerializableManager()
        mgr.register_special(set, ("__set__",))
        mgr.add_encoder(set, lambda s: {"__set__": list(s)})
        mgr.add_decoder(set, lambda o: set(o["__set__"]))
        encoder = mgr.build_encoder()
        decoder = mgr.build_decoder()

        encoded = json.dumps({1, 2, 3}, cls=encoder)
        decoded = json.loads(encoded, cls=decoder)

        assert isinstance(decoded, set)
        assert decoded == {1, 2, 3}

    def test_duplicate_encoder_raises(self):
        mgr = JSONSerializableManager()
        mgr.register_special(set, ("__set__",))
        mgr.add_encoder(set, lambda s: {"__set__": list(s)})
        with pytest.raises(ValueError, match="Encoder for type"):
            mgr.add_encoder(set, lambda s: {"__set__": list(s)})

    def test_duplicate_decoder_raises(self):
        mgr = JSONSerializableManager()
        mgr.register_special(set, ("__set__",))
        mgr.add_decoder(set, lambda o: set(o["__set__"]))
        with pytest.raises(ValueError, match="Decoder for type"):
            mgr.add_decoder(set, lambda o: set(o["__set__"]))

    def test_list_of_objects(self):
        mgr = JSONSerializableManager()
        mgr.register(SimpleObj)
        encoder = mgr.build_encoder()
        decoder = mgr.build_decoder()

        objs = [SimpleObj("a", 1), SimpleObj("b", 2)]
        encoded = json.dumps(objs, cls=encoder)
        decoded = json.loads(encoded, cls=decoder)

        assert len(decoded) == 2
        assert all(isinstance(o, SimpleObj) for o in decoded)
        assert decoded[0].name == "a"
        assert decoded[1].value == 2

    def test_plain_dict_passes_through(self):
        mgr = JSONSerializableManager()
        encoder = mgr.build_encoder()
        decoder = mgr.build_decoder()

        data = {"foo": "bar", "num": 123}
        encoded = json.dumps(data, cls=encoder)
        decoded = json.loads(encoded, cls=decoder)

        assert decoded == data
