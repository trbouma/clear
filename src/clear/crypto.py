"""Cashu BDHKE primitives and deterministic Clear keysets."""

from __future__ import annotations

import hashlib
import hmac

from coincurve import PrivateKey, PublicKey

CURVE_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
DOMAIN_SEPARATOR = b"Secp256k1_HashToCurve_Cashu_"


def _scalar(secret: bytes) -> bytes:
    value = int.from_bytes(secret, "big") % CURVE_ORDER
    if value == 0:
        value = 1
    return value.to_bytes(32, "big")


def _derivation_secret(master_secret: str, root_authority_npub: str | None) -> str:
    if not root_authority_npub:
        return master_secret
    return f"{master_secret}|root-authority-npub:{root_authority_npub}"


def derive_private_key(
    master_secret: str,
    amount: int,
    root_authority_npub: str | None = None,
) -> bytes:
    digest = hmac.new(
        _derivation_secret(master_secret, root_authority_npub).encode(),
        f"clear-keyset-v2:{amount}".encode(),
        hashlib.sha256,
    ).digest()
    return _scalar(digest)


def hash_to_curve(message: str) -> PublicKey:
    message_hash = hashlib.sha256(DOMAIN_SEPARATOR + message.encode()).digest()
    for counter in range(2**32):
        candidate = hashlib.sha256(
            message_hash + counter.to_bytes(4, "little")
        ).digest()
        try:
            return PublicKey(b"\x02" + candidate)
        except ValueError:
            continue
    raise RuntimeError("could not map secret to secp256k1")


class Keyset:
    def __init__(
        self,
        master_secret: str,
        max_order: int = 20,
        root_authority_npub: str | None = None,
    ):
        self.root_authority_npub = root_authority_npub
        self.private_keys = {
            2**order: derive_private_key(
                master_secret,
                2**order,
                root_authority_npub,
            )
            for order in range(max_order + 1)
        }
        self.public_keys = {
            amount: PrivateKey(private).public_key.format(compressed=True).hex()
            for amount, private in self.private_keys.items()
        }
        public_key_bytes = b"".join(
            bytes.fromhex(self.public_keys[amount])
            for amount in sorted(self.public_keys)
        )
        self.fingerprint = "00" + hashlib.sha256(public_key_bytes).hexdigest()[:14]
        self.unit = f"cmu-{self.fingerprint}"
        preimage = ",".join(
            f"{amount}:{self.public_keys[amount]}"
            for amount in sorted(self.public_keys)
        )
        preimage += f"|unit:{self.unit}"
        self.id = "01" + hashlib.sha256(preimage.encode()).hexdigest()

    def sign_blinded(self, amount: int, blinded_secret: str) -> str:
        private = self.private_keys.get(amount)
        if private is None:
            raise ValueError(f"unsupported denomination: {amount}")
        try:
            point = PublicKey(bytes.fromhex(blinded_secret))
        except (ValueError, TypeError) as exc:
            raise ValueError("B_ must be a compressed secp256k1 public key") from exc
        return point.multiply(private).format(compressed=True).hex()

    def verify_proof(self, amount: int, secret: str, signature: str) -> str:
        private = self.private_keys.get(amount)
        if private is None:
            raise ValueError(f"unsupported denomination: {amount}")
        y = hash_to_curve(secret)
        expected = y.multiply(private).format(compressed=True)
        try:
            supplied = PublicKey(bytes.fromhex(signature)).format(compressed=True)
        except (ValueError, TypeError) as exc:
            raise ValueError("C must be a compressed secp256k1 public key") from exc
        if not hmac.compare_digest(expected, supplied):
            raise ValueError("invalid proof signature")
        return y.format(compressed=True).hex()
