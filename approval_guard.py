"""Read-only Ethereum ERC-20 approval preview. No RPC, wallet, signing or broadcasting."""
import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ADDRESS = re.compile(r'0x[0-9a-fA-F]{40}')
CALLDATA = re.compile(r'0x095ea7b3[0-9a-fA-F]{128}')

def preview(data):
    if not isinstance(data, dict):
        return {'status': 'unsupported', 'reason': 'expected_object'}
    chain, target, calldata = (data.get(k) for k in ('chain_id', 'to', 'data'))
    if type(chain) is not int or not 1 <= chain <= 2**53-1:
        return {'status': 'unsupported', 'reason': 'invalid_chain_id'}
    if not isinstance(target, str) or not ADDRESS.fullmatch(target) or int(target, 16) == 0:
        return {'status': 'unsupported', 'reason': 'invalid_target'}
    if data.get('value') not in ('0', '0x0'):
        return {'status': 'unsupported', 'reason': 'require_explicit_zero_native_value'}
    if not isinstance(calldata, str) or not CALLDATA.fullmatch(calldata):
        return {'status': 'unsupported', 'reason': 'not_canonical_erc20_approve'}
    address_word = calldata[10:74]
    if address_word[:24] != '0' * 24:
        return {'status': 'unsupported', 'reason': 'invalid_spender_encoding'}
    spender = '0x' + address_word[-40:].lower()
    amount = int(calldata[74:], 16)
    if int(spender, 16) == 0:
        label = 'zero_spender'
    elif amount == 0:
        label = 'zero_allowance_request'
    elif amount == 2**256 - 1:
        label = 'unlimited_allowance_request'
    else:
        label = 'bounded_allowance_request'
    return {'status': 'decoded_only', 'finding': label, 'chain_id_claimed': chain,
            'target': target.lower(), 'spender': spender, 'amount_base_units': str(amount),
            'warning': 'Contract, chain state and behavior were not verified. This is not a recommendation to sign.'}

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def send_json(self, status, response):
        raw = json.dumps(response).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        self.send_json(200, {'status': 'ok'}) if self.path == '/health' else self.send_json(404, {'error': 'not_found'})

    def do_POST(self):
        if self.path != '/agent':
            return self.send_json(404, {'error': 'not_found'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 4096:
                return self.send_json(400, {'error': 'invalid_content_length'})
            self.connection.settimeout(3)
            result = preview(json.loads(self.rfile.read(size)))
        except (ValueError, OSError, RecursionError):
            return self.send_json(400, {'error': 'invalid_request'})
        self.send_json(200 if result['status'] == 'decoded_only' else 422, result)

if __name__ == '__main__':
    ThreadingHTTPServer(('127.0.0.1', 8793), Handler).serve_forever()
