# generator.py — HEX CHEATS OFC  |  @HeX_CiPhEr
# All Garena OB55 protocol logic + multi-threaded generation engine.

import hmac
import hashlib
import requests
import string
import random
import json
import codecs
import time
import os
import base64
import re
import threading
import urllib3
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============ BRANDING ============
BRAND = {
    "name": "HEX CHEATS OFC",
    "handle": "@HeX_CiPhEr",
    "channel": "https://t.me/+sL3xBoiSrVZmYWI9",
    "hidden_tag": "HeX_CiPhEr",
}

# ============ CONFIG ============
REGION_LANG = {
    "ME": "ar", "IND": "hi", "ID": "id", "VN": "vi", "TH": "th",
    "BD": "bn", "PK": "ur", "TW": "zh", "CIS": "ru", "SAC": "es", "BR": "pt",
}

API_SECRET_KEY = "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"
_API_KEY_BYTES = API_SECRET_KEY.encode()
DEVICE_ID = "02-344afb0e-593c-40b7-92f2-171972f74807"

_AES_KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
_AES_IV = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

DATADOME_COOKIES_REG = [
    "datadome=oYpIhVco_RFvLHe_T9KFd5wuY0gcQuNfrlt4rHJY5QOkwv4TGt8gPMK32MbHuBdzJyfXnXlfzNZT_2tHr2kys8AMYT2~T71QP1S78_7Pdx4JLOXdSrflPT6cOX2vsyJh",
    "datadome=Jm3nWQKqc8QvL9C7xgP2RfT5hYbN6dEwA4sZ1xM0pUkV3tBi9oHlGgDfSjNc2rX5eAq8wY7uI1kP4mZ9vB6tR0nO3sL5hC2dF8gE7aQ1wS4vN0jM6xT9bK3rY5uH2pD8cL1fV7eA4gZ0nX6wI3sQ9tB5mR2kO8yJ7hD4fP1cU6vN3xL9aG",
    "datadome=Xk7pQzW2nR9mD4vB6tH1yC3fL8sE5aG0oJ2uI9wK4rN7qP3mT6vX8zB1cD5hF0gL2nS4uW7yM9oK3pQ6rT8vB1xZ4cN7mH2jF5dG0aS9e",
]
DATADOME_COOKIES_TOK = [
    "datadome=y23Z3X17pgkMHEt5zY8dqxC6BIf7WJMgC0RXNbqifHT7t9zajKe_hegFb1Ie9_7JixXpz7FRGVodOn~mWPk_NrqIIhUOXDYqKOahzoRQcyEy77GWEMcdA9_MqPJeM5qv",
    "datadome=Pq8wN3mL7kJ2vR5tY1xH9cF4bD6gS0aE7uZ3nI9oK2mP5qT8vX1wB4cR7hL0jG6dS9fA2uW5yM8nQ3pO6rT1vK4xZ7cB0dF5hJ9lN2sG",
    "datadome=Hn4rT7xP1sK9mB2vQ6wC3yF8dL5gJ0aE9uI4oN7pR1tM6vX3zB8cD2hF5kL0nS9wA4yU7iO1qP6rT3vM8xZ2cB5dG",
]
UA_POOL_REG = [
    "GarenaMSDK/4.0.44(25028RN03A ;Android 15;ar;EG;app 1.132.1 2019121229;)",
    "GarenaMSDK/4.0.44(SM-A325M;Android 13;en;HK;app 1.132.1 2019121229;)",
    "GarenaMSDK/4.0.43(Redmi Note 8;Android 11;en;IN;app 1.130.1 2019121229;)",
    "GarenaMSDK/4.0.44(Pixel 6;Android 14;en;US;app 1.132.1 2019121229;)",
]
UA_MAJOR = "UnityPlayer/2018.4.12f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)"

_MAJOR_HEADERS = {
    "User-Agent": UA_MAJOR,
    "Accept-Encoding": "deflate, gzip",
    "X-GA-SV": "1789535859",
    "Authorization": "Bearer",
    "X-GA": "v1 1",
    "ReleaseVersion": "OB55",
    "Content-Type": "application/x-www-form-urlencoded",
    "X-Unity-Version": "2018.4.12f1",
    "Host": "loginbp.ppmainecoonghj.com",
}

# ============ THREAD-LOCAL SESSION ============
_thread_local = threading.local()


def _session():
    if not hasattr(_thread_local, "s"):
        s = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=20, pool_maxsize=40, max_retries=0, pool_block=False
        )
        s.mount("https://", adapter)
        s.mount("http://", adapter)
        _thread_local.s = s
    return _thread_local.s


# ============ CRYPTO / PROTO ============
def generate_signature(payload: str) -> str:
    return hmac.new(_API_KEY_BYTES, payload.encode(), hashlib.sha256).hexdigest()


def _encode_varint(n):
    if n < 0:
        return b""
    out = []
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            b |= 0x80
        out.append(b)
        if not n:
            break
    return bytes(out)


def _proto_field(num, value):
    if isinstance(value, int):
        return _encode_varint((num << 3) | 0) + _encode_varint(value)
    if isinstance(value, (str, bytes)):
        v = value.encode() if isinstance(value, str) else value
        return _encode_varint((num << 3) | 2) + _encode_varint(len(v)) + v
    return b""


def build_proto(fields):
    return b"".join(_proto_field(k, v) for k, v in fields.items())


def _aes_encrypt(hex_data):
    cipher = AES.new(_AES_KEY, AES.MODE_CBC, _AES_IV)
    return cipher.encrypt(pad(bytes.fromhex(hex_data), AES.block_size))


def _encrypt_api(plain_hex):
    cipher = AES.new(_AES_KEY, AES.MODE_CBC, _AES_IV)
    return cipher.encrypt(pad(bytes.fromhex(plain_hex), AES.block_size)).hex()


# ============ HELPERS ============
def _exp_suffix():
    exp = {"0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
           "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹"}
    n = random.randint(1, 9999)
    return "".join(exp[d] for d in f"{n:04d}")


def _rand_name(prefix):
    return f"{prefix}{_exp_suffix()}"


def _rand_password(prefix):
    rand = "".join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(8))
    return f"{prefix}_{BRAND['hidden_tag']}_{rand}"


_LOGIN_BLOB_PREFIX = b'\x1a\x132025-08-30 05:19:21"\tfree fire(\x01:\x081.114.13B2Android OS 9 / API-28 (PI/rel.cjw.20220518.114133)J\x08HandheldR\nATM MobilsZ\x04WIFI`\xb6\nh\xee\x05r\x03300z\x1fARMv7 VFPv3 NEON VMH | 2400 | 2\x80\x01\xc9\x0f\x8a\x01\x0fAdreno (TM) 640\x92\x01\rOpenGL ES 3.2\x9a\x01+Google|dfa4ab4b-9dc4-454e-8065-e70c733fa53f\xa2\x01\x0e105.235.139.91\xaa\x01\x02'
_LOGIN_BLOB_SUFFIX = b'\xb2\x01 1d8ec0240ede109973f3321b9354b44d\xba\x01\x014\xc2\x01\x08Handheld\xca\x01\x10Asus ASUS_I005DA\xea\x01@afcfbf13334be42036e4f742c80b956344bed760ac91b3aff9b607a610ab4390\xf0\x01\x01\xca\x02\nATM Mobils\xd2\x02\x04WIFI\xca\x03 7428b253defc164018c604a1ebbfebdf\xe0\x03\xa8\x81\x02\xe8\x03\xf6\xe5\x01\xf0\x03\xaf\x13\xf8\x03\x84\x07\x80\x04\xe7\xf0\x01\x88\x04\xa8\x81\x02\x90\x04\xe7\xf0\x01\x98\x04\xa8\x81\x02\xc8\x04\x01\xd2\x04=/data/app/com.dts.freefireth-PdeDnOilCSFn37p1AH_FLg==/lib/arm\xe0\x04\x01\xea\x04_2087f61c19f57f2af4e7feff0b24d9d9|/data/app/com.dts.freefireth-PdeDnOilCSFn37p1AH_FLg==/base.apk\xf0\x04\x03\xf8\x04\x01\x8a\x05\x0232\x9a\x05\n2019118693\xb2\x05\tOpenGLES2\xb8\x05\xff\x7f\xc0\x05\x04\xe0\x05\xf3C\xea\x05\x07android\xf2\x05pKqsHT5ZLWrYljNb5Vqh//yFRlaPHSO9NWSQsVvOmdhEEn7W+VHNUK+Q+fduA3ptNrGB0Ll0LRz3WW0jOwesLj6aiU7sZ40p8BfUE/FI/jzSTwRe2\xf8\x05\xfb\xe4\x06\x88\x06\x01\x90\x06\x01\x9a\x06\x014\xa2\x06\x014\xb2\x06"GQ@O\x00\x0e^\x00D\x06UA\x0ePM\r\x13hZ\x07T\x06\x0cm\\V\x0ejYV;\x0bU5'


# ============ RARITY / COUPLES ============
RARE_PATTERNS = {
    "REPEAT4": [r"(\d)\1{3,}", 3],
    "REPEAT3X2": [r"(\d)\1\1(\d)\2\2", 2],
    "SEQ5": [r"(12345|23456|34567|45678|56789)", 4],
    "SEQ4": [r"(0123|1234|2345|3456|4567|5678|6789)", 3],
    "PALIN": [r"^(\d)(\d)\2\1$", 3],
    "QUAD": [r"(1111|2222|3333|4444|5555|6666|7777|8888|9999|0000)", 4],
    "LOW_ID": [r"^\d{1,6}$", 3],
}

_COUPLES_STORE = {}
_COUPLES_LOCK = threading.Lock()


def check_rarity(acc, threshold):
    aid = str(acc.get("account_id", ""))
    if not aid or aid == "N/A":
        return False, None, 0
    score = 0
    hits = []
    for name, (pat, pts) in RARE_PATTERNS.items():
        if re.search(pat, aid):
            score += pts
            hits.append(name)
    digits = [int(d) for d in aid if d.isdigit()]
    if len(digits) >= 4 and len(set(digits)) == 1:
        score += 5
        hits.append("UNIFORM")
    if score >= threshold:
        return True, ",".join(hits), score
    return False, None, score


def check_couple(acc):
    aid = str(acc.get("account_id", ""))
    if not aid or aid == "N/A":
        return False, None
    with _COUPLES_LOCK:
        for stored_id, stored in list(_COUPLES_STORE.items()):
            if abs(int(aid) - int(stored_id)) == 1:
                partner = _COUPLES_STORE.pop(stored_id)
                return True, partner
            if aid == stored_id[::-1]:
                partner = _COUPLES_STORE.pop(stored_id)
                return True, partner
        _COUPLES_STORE[aid] = acc
    return False, None


# ============ CORE FLOW ============
def _create_account(region, name_prefix, pwd_prefix):
    """Full flow: register → token grant → major register → major login."""
    session = _session()
    password = _rand_password(pwd_prefix)

    # 1) register
    reg_payload = json.dumps({
        "app_id": 100067, "client_type": 2,
        "password": password, "source": 2,
    }, separators=(",", ":"))
    headers = {
        "User-Agent": random.choice(UA_POOL_REG),
        "Connection": "Keep-Alive",
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "Authorization": f"Signature {generate_signature(reg_payload)}",
        "Content-Type": "application/json; charset=utf-8",
        "Cookie": random.choice(DATADOME_COOKIES_REG),
        "Host": "100067.connect.garena.com",
    }
    try:
        r = session.post(
            "https://100067.connect.garena.com/api/v2/oauth/guest:register",
            headers=headers, data=reg_payload, timeout=8, verify=False,
        )
        if r.status_code != 200:
            return None
        rj = r.json()
        if rj.get("code") != 0 or "uid" not in rj.get("data", {}):
            return None
        uid = rj["data"]["uid"]
    except Exception:
        return None

    # 2) token grant
    tok_payload = json.dumps({
        "client_id": 100067,
        "client_secret": API_SECRET_KEY,
        "client_type": 2,
        "device_id": DEVICE_ID,
        "password": password,
        "response_type": "token",
        "uid": uid,
    }, separators=(",", ":"))
    headers["Cookie"] = random.choice(DATADOME_COOKIES_TOK)
    try:
        r = session.post(
            "https://100067.connect.garena.com/api/v2/oauth/guest/token:grant",
            headers=headers, data=tok_payload, timeout=8, verify=False,
        )
        if r.status_code != 200:
            return None
        rj = r.json()
        if rj.get("code") != 0:
            return None
        open_id = rj["data"]["open_id"]
        access_token = rj["data"]["access_token"]
    except Exception:
        return None

    # 3) major register
    keystream = [0x30] * 32
    field = codecs.decode(
        "".join(chr(ord(open_id[i]) ^ keystream[i % len(keystream)]) for i in range(len(open_id)))
        .encode("unicode_escape").decode("utf-8"),
        "unicode_escape",
    ).encode("latin1")

    name = _rand_name(name_prefix)
    lang = REGION_LANG.get(region.upper(), "en")
    proto = build_proto({
        1: name, 2: access_token, 3: open_id,
        5: 102000007, 6: 4, 7: 1, 13: 1, 14: field,
        15: lang, 16: 1, 17: 1,
    })
    try:
        session.post(
            "https://loginbp.ppmainecoonghj.com/MajorRegister",
            headers=_MAJOR_HEADERS, data=_aes_encrypt(proto.hex()),
            verify=False, timeout=8,
        )
    except Exception:
        pass

    # 4) major login
    payload = _LOGIN_BLOB_PREFIX + lang.encode("ascii") + _LOGIN_BLOB_SUFFIX
    payload = payload.replace(b"afcfbf13334be42036e4f742c80b956344bed760ac91b3aff9b607a610ab4390", access_token.encode())
    payload = payload.replace(b"1d8ec0240ede109973f3321b9354b44d", open_id.encode())
    try:
        r = session.post(
            "https://loginbp.ppmainecoonghj.com/MajorLogin",
            headers=_MAJOR_HEADERS, data=bytes.fromhex(_encrypt_api(payload.hex())),
            verify=False, timeout=8,
        )
        if r.status_code != 200:
            return None
        jwt_start = r.text.find("eyJ")
        if jwt_start == -1:
            return None
        jwt_token = r.text[jwt_start:]
        second_dot = jwt_token.find(".", jwt_token.find(".") + 1)
        if second_dot == -1:
            return None
        jwt_token = jwt_token[:second_dot + 44]
        payload_b64 = jwt_token.split(".")[1]
        pad_len = 4 - len(payload_b64) % 4
        if pad_len != 4:
            payload_b64 += "=" * pad_len
        decoded = json.loads(base64.urlsafe_b64decode(payload_b64))
        account_id = decoded.get("account_id") or decoded.get("external_id")
        if not account_id:
            return None
        return {
            "uid": str(uid),
            "password": password,
            "name": name,
            "account_id": str(account_id),
            "region": region,
            "jwt_token": jwt_token,
            "date_created": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        }
    except Exception:
        return None


# ============ JOB ENGINE ============
def _log(job, level, msg):
    with job["lock"]:
        job["logs"].append({"t": time.time(), "level": level, "msg": msg})
        if len(job["logs"]) > 500:
            job["logs"] = job["logs"][-500:]


def _worker(job):
    with job["lock"]:
        if job["stop"] or job["success"] >= job["count"]:
            return
    acc = _create_account(job["region"], job["prefix"], job["pwd_prefix"])
    if not acc:
        with job["lock"]:
            job["failed"] += 1
        return

    # rarity check
    is_rare, hit_reason, score = check_rarity(acc, job["rarity_threshold"])
    if is_rare:
        acc["rarity_score"] = score
        acc["rarity_reason"] = hit_reason

    is_couple, partner = check_couple(acc)

    with job["lock"]:
        if job["success"] >= job["count"]:
            return
        job["success"] += 1
        if is_rare:
            job["rare"] += 1
        if is_couple:
            job["couples"] += 1
            acc["couple_with"] = partner.get("account_id") if partner else None
        job["accounts"].append(acc)
        if len(job["accounts"]) > 10000:
            job["accounts"] = job["accounts"][-10000:]

    tag = ""
    if is_rare:
        tag += f" 💎[{hit_reason} {score}]"
    if is_couple:
        tag += " 💑"
    _log(job, "success", f"+ {acc['name']} | {acc['account_id']} | {acc['uid']}{tag}")


def generate_accounts(job):
    _log(job, "info", f"Job started | region={job['region']} | count={job['count']} | threads={job['threads']}")
    threads = job["threads"]
    with ThreadPoolExecutor(max_workers=threads) as ex:
        futures = set()
        while True:
            with job["lock"]:
                done = job["success"] + job["failed"]
                finished = job["success"] >= job["count"] or job["stop"]
            if finished and not futures:
                break
            # top up workers
            while not finished and len(futures) < threads:
                futures.add(ex.submit(_worker, job))
            # wait a bit and clean finished
            done_futs = {f for f in futures if f.done()}
            if done_futs:
                for f in done_futs:
                    futures.discard(f)
            time.sleep(0.02)

    with job["lock"]:
        job["finished"] = True
    _log(job, "info",
         f"Job finished | success={job['success']} failed={job['failed']} "
         f"rare={job['rare']} couples={job['couples']}")


# ============ STOP MANAGER ============
class StopFlagManager:
    def __init__(self):
        self.flags = {}

    def get(self, job_id):
        return self.flags.get(job_id, False)

    def set(self, job_id):
        self.flags[job_id] = True


stop_flag_manager = StopFlagManager()