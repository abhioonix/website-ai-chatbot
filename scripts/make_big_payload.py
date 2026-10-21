"""Local verification helpers — generates a payload larger than MAX_BODY_BYTES."""
import json

payload = {"message": "x" * 9000, "history": []}
with open("/tmp/big.json", "w", encoding="utf-8") as fh:
    json.dump(payload, fh)
print("wrote /tmp/big.json")
