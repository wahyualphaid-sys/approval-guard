# Approval Guard — zkVerify Agent Games Wildcard

Approval Guard helps EVM wallet users review ERC-20 allowance requests before signing. It decodes canonical `approve(address,uint256)` calldata and distinguishes zero, bounded, and maximum allowances. It does not connect to wallets, sign, broadcast, call an RPC, or verify that the target is actually a token. A decoded request is not a recommendation to sign.

## Run the demo

`python3 approval_guard.py` (Python 3.10+, no dependencies) starts a local listener on `127.0.0.1:8793`. `GET /health` checks liveness. `POST /agent` takes `chain_id` (integer), `to` (20-byte hex address), `value` (`"0"` or `"0x0"`), and `data` (canonical hex calldata). `example.json` is a synthetic maximum allowance request on Base Sepolia. Send it with:

```sh
curl -sS -H 'Content-Type: application/json' --data-binary @example.json http://127.0.0.1:8793/agent
```

Expected `finding`: `unlimited_allowance_request`. `amount_base_units` is a decimal string so reviewers do not lose integer precision. Unsupported calldata returns HTTP 422; invalid JSON or length returns HTTP 400. The chain ID is caller-supplied, not verified.

## Wildcard submission

This archive is a local demo, not an entry or a registered agent. Host the demo behind a public HTTPS reverse proxy on an authorized host; forward only `/health` and `/agent`, and set request size limits, request timeouts, and rate limits there. Test both routes against the public URL before submitting it. Do not attach a wallet or expose the vault to this service. If the platform requires authenticated callbacks, implement and verify its documented HMAC protocol before using this endpoint for callbacks; the standalone demo does not implement it. No zkVerify proof is claimed.
