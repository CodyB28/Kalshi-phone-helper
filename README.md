# Kalshi Phone Helper

A tiny Flask service that handles Kalshi request signing on a cloud host so your iPhone does not need to run `cryptography` locally.

## Files
- `app.py` - web service with balance, open markets, and test order routes
- `requirements.txt` - Python dependencies
- `render.yaml` - Render blueprint for deployment

## Deploy on Render
1. Create a new GitHub repository.
2. Upload `app.py`, `requirements.txt`, and `render.yaml`.
3. In Render, create a new **Web Service** from that repo.
4. Use the free Hobby workspace and web service flow.
5. Add environment variables:
   - `KALSHI_API_KEY_ID`
   - `KALSHI_PRIVATE_KEY_PEM`
   - optional `KALSHI_BASE_URL`
6. For the private key, paste the full PEM including:
   - `-----BEGIN RSA PRIVATE KEY-----`
   - all middle lines
   - `-----END RSA PRIVATE KEY-----`
7. Deploy the service.

## Test routes
- `/health`
- `/balance`
- `/markets/open?limit=5`
- `/order/test`

## Important notes
- Keep `KALSHI_API_KEY_ID` and `KALSHI_PRIVATE_KEY_PEM` as Render environment variables, not in code.
- The `/order/test` route is only a scaffold. Do not send real orders until `/balance` works first.
- For demo trading, switch `KALSHI_BASE_URL` to the demo API host.
