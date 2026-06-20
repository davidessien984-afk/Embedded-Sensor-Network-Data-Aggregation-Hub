"""Render class_diagram.puml to class_diagram.png via the PlantUML server.

Uses PlantUML's deflate + custom-base64 URL encoding so we don't need a local
Java/PlantUML install. Requires an internet connection.
"""
import os
import zlib
import urllib.request

ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"


def _enc3(b1, b2, b3):
    c1 = b1 >> 2
    c2 = ((b1 & 0x3) << 4) | (b2 >> 4)
    c3 = ((b2 & 0xF) << 2) | (b3 >> 6)
    c4 = b3 & 0x3F
    return ALPHABET[c1 & 0x3F] + ALPHABET[c2 & 0x3F] + ALPHABET[c3 & 0x3F] + ALPHABET[c4 & 0x3F]


def encode(data: bytes) -> str:
    out = []
    for i in range(0, len(data), 3):
        b1 = data[i]
        b2 = data[i + 1] if i + 1 < len(data) else 0
        b3 = data[i + 2] if i + 2 < len(data) else 0
        out.append(_enc3(b1, b2, b3))
    return "".join(out)


here = os.path.dirname(os.path.abspath(__file__))
puml = open(os.path.join(here, "class_diagram.puml"), encoding="utf-8").read()
compressed = zlib.compress(puml.encode("utf-8"), 9)[2:-4]  # strip zlib header + checksum
url = "http://www.plantuml.com/plantuml/png/" + encode(compressed)
print("URL length:", len(url))

req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
data = urllib.request.urlopen(req, timeout=60).read()
out_path = os.path.join(here, "class_diagram.png")
with open(out_path, "wb") as fh:
    fh.write(data)
print("wrote", out_path, len(data), "bytes; valid PNG:", data[:8] == b"\x89PNG\r\n\x1a\n")
