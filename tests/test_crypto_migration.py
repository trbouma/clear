"""Fixed pre-migration outputs protect CMU identity and blind signatures."""
from clear.crypto import Keyset, hash_to_curve


def test_stroma_curve_preserves_existing_keyset_and_signature():
    keyset = Keyset("11" * 32, max_order=3)
    assert keyset.id == (
        "013b5fb6d7ff46ec711c6cb107187abfd846f78c11a7e58af4db5315ecdc0a4bc2"
    )
    assert keyset.unit == "cmu-0004ed28d004cf77"
    point = hash_to_curve("stroma-migration-vector").format().hex()
    assert point == "02dad075851833dda3d8cfcb146f748ed5cf22f9461c1584f8233c5091ccef15e2"
    signature = keyset.sign_blinded(8, point)
    assert signature == (
        "0319a0cd49e1503b2b010089a3832140e3d7ee760c3a632791cd83b7c5055349d8"
    )
    assert keyset.verify_proof(8, "stroma-migration-vector", signature) == point
