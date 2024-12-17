import json
import re
import uuid
import base64
import time
import execjs
import requests
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
from cryptography.hazmat.backends import default_backend


def base64url_encode(data: bytes) -> str:
    """
    Encodes bytes into a base64url string without padding.
    """
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')


def generate_ecdsa_key_pair(htu: str, htm: str) -> str:
    """
    Generates an ECDSA P-256 key pair, constructs a DPoP JWT, signs it, and returns the token.

    Parameters:
    - htu (str): HTTP URI the token is intended for.
    - htm (str): HTTP method (e.g., "GET", "POST").

    Returns:
    - str: The signed DPoP JWT.
    """
    # 1. Generate ECDSA key pair using the P-256 curve
    private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
    public_key = private_key.public_key()

    # 2. Export the public key in JWK format
    public_numbers = public_key.public_numbers()
    jwk = {
        'kty': 'EC',
        'crv': 'P-256',
        'x': base64url_encode(public_numbers.x.to_bytes(32, 'big')),
        'y': base64url_encode(public_numbers.y.to_bytes(32, 'big')),
        # 'ext' and 'key_ops' are intentionally omitted to match the JavaScript code
    }

    # 3. Create the header part of the JWT
    header = {
        "typ": "dpop+jwt",
        "alg": "ES256",
        "jwk": jwk
    }
    header_json = json.dumps(header, separators=(',', ':'))

    # 4. Create the payload part of the JWT
    payload = {
        "iat": int(time.time()),
        "jti": str(uuid.uuid4()),
        "htu": htu,
        "htm": htm,
        "uuid": "07eede5c-3f3d-48fc-85b2-c11fdfe4101c"  # Hardcoded UUID as in the JS code
    }
    payload_json = json.dumps(payload, separators=(',', ':'))

    # 5. Base64url encode the header and payload
    encoded_header = base64url_encode(header_json.encode('utf-8'))
    encoded_payload = base64url_encode(payload_json.encode('utf-8'))

    # 6. Concatenate header and payload with a dot
    signing_input = f"{encoded_header}.{encoded_payload}"

    # 7. Sign the concatenated string using ECDSA with SHA-256
    signature_der = private_key.sign(
        signing_input.encode('utf-8'),
        ec.ECDSA(hashes.SHA256())
    )

    # 8. Convert DER signature to raw (R || S) format
    r, s = decode_dss_signature(signature_der)
    r_bytes = r.to_bytes(32, byteorder='big')
    s_bytes = s.to_bytes(32, byteorder='big')
    signature_raw = r_bytes + s_bytes

    # 9. Base64url encode the signature
    encoded_signature = base64url_encode(signature_raw)

    # 10. Construct the final JWT
    dpop_jwt = f"{signing_input}.{encoded_signature}"

    return dpop_jwt


def xiangqing(url):

    try:
        ids = re.findall('/item/(.*)', url)[0]
        url = 'https://api.mercari.jp/items/get?id=' + ids + '&include_item_attributes=true&include_product_page_component=true&include_non_ui_item_attributes=true&include_donation=true&include_offer_like_coupon_display=true&include_offer_coupon_display=true&include_item_attributes_sections=true&include_auction=false&country_code=HK'
        header = {
            'dpop': generate_ecdsa_key_pair(url, "GET"),
            'origin': 'https://jp.mercari.com',
            'priority': 'u=1, i',
            'referer': 'https://jp.mercari.com/',

            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'x-platform': 'web'
        }
        req = requests.get(url, headers=header)
        dic = {}
        html = req.json()
        dic['price'] = html['data']['price']

        dic['name'] = html['data']['name']
        dic['photos'] = html['data']['photos']
        return json.dumps(dic)
    except Exception as e:
        ids = re.findall('/shops/product/(.*)', url)[0]

        url = 'https://api.mercari.jp/v1/marketplaces/shops/products/'+ids+'?view=FULL&imageType=JPEG'
        header = {
            'dpop': generate_ecdsa_key_pair(url, "GET"),
            'origin': 'https://jp.mercari.com',
            'priority': 'u=1, i',
            'referer': 'https://jp.mercari.com/',

            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'x-platform': 'web'
        }
        req = requests.get(url, headers=header)

        dic = {}
        html = req.json()
        dic['price'] = html['price']

        dic['name'] = html['displayName']
        dic['photos'] = html['productDetail']['photos']
        return json.dumps(dic)

print(xiangqing('https://jp.mercari.com/shops/product/RLdhEkp9exLuUC4uEXtPyb'))