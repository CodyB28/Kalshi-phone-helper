import os
import time
import base64
from urllib.parse import urlparse

import requests
from flask import Flask, jsonify, request
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

app = Flask(__name__)

BASE_URL = os.getenv('KALSHI_BASE_URL', 'https://api.elections.kalshi.com/trade-api/v2')
API_KEY_ID = os.getenv('KALSHI_API_KEY_ID', '')
PRIVATE_KEY_PEM = os.getenv('KALSHI_PRIVATE_KEY_PEM', '')
API_TIMEOUT = float(os.getenv('API_TIMEOUT', '20'))


def load_private_key():
    if not PRIVATE_KEY_PEM.strip():
        raise RuntimeError('Missing KALSHI_PRIVATE_KEY_PEM environment variable')
    return serialization.load_pem_private_key(
        PRIVATE_KEY_PEM.encode('utf-8'),
        password=None,
    )


def create_signature(private_key, timestamp, method, path):
    path_without_query = path.split('?')[0]
    message = f"{timestamp}{method}{path_without_query}".encode('utf-8')
    signature = private_key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.DIGEST_LENGTH,
        ),
        hashes.SHA256(),
    )
    return base64.b64encode(signature).decode('utf-8')


def kalshi_request(method, path, payload=None):
    if not API_KEY_ID.strip():
        raise RuntimeError('Missing KALSHI_API_KEY_ID environment variable')

    private_key = load_private_key()
    timestamp = str(int(time.time() * 1000))
    sign_path = urlparse(BASE_URL + path).path
    signature = create_signature(private_key, timestamp, method.upper(), sign_path)

    headers = {
        'KALSHI-ACCESS-KEY': API_KEY_ID,
        'KALSHI-ACCESS-SIGNATURE': signature,
        'KALSHI-ACCESS-TIMESTAMP': timestamp,
    }
    if payload is not None:
        headers['Content-Type'] = 'application/json'

    response = requests.request(
        method=method.upper(),
        url=BASE_URL + path,
        headers=headers,
        json=payload,
        timeout=API_TIMEOUT,
    )
    return response


@app.get('/')
def home():
    return jsonify({
        'name': 'Kalshi Phone Helper',
        'status': 'ok',
        'routes': ['/health', '/balance', '/markets/open?limit=5'],
    })


@app.get('/health')
def health():
    return jsonify({'ok': True})


@app.get('/balance')
def balance():
    try:
        response = kalshi_request('GET', '/portfolio/balance')
        return jsonify({
            'status_code': response.status_code,
            'data': response.json() if response.content else {},
            'raw_text': response.text if response.status_code >= 400 else '',
        }), response.status_code
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@app.get('/markets/open')
def open_markets():
    limit = request.args.get('limit', '5')
    try:
        response = requests.get(
            f'{BASE_URL}/markets?status=open&limit={limit}',
            timeout=API_TIMEOUT,
        )
        return jsonify({
            'status_code': response.status_code,
            'data': response.json() if response.content else {},
            'raw_text': response.text if response.status_code >= 400 else '',
        }), response.status_code
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@app.post('/order/test')
def order_test():
    payload = request.get_json(silent=True) or {
        'ticker': 'DEMO',
        'action': 'buy',
        'side': 'yes',
        'count': 1,
        'type': 'limit',
        'yes_price': 1,
        'client_order_id': 'replace-me',
    }
    try:
        response = kalshi_request('POST', '/portfolio/orders', payload=payload)
        return jsonify({
            'status_code': response.status_code,
            'data': response.json() if response.content else {},
            'raw_text': response.text if response.status_code >= 400 else '',
        }), response.status_code
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', '10000'))
    app.run(host='0.0.0.0', port=port)
