# user-studio-access

A small, dependency-light Python client for Treasure Data's
[Controlling AI Studio Access](https://docs.treasure.ai/products/control-panel/security/users/controlling-ai-studio-access)
API.

Grant, check, or remove a user's access to Treasure AI Studio via the
per-user `treasure_ai_studio` profile option.

## Running it in Postman

The `postman/` folder has a ready-made collection covering all three
operations, for v3 and v4 both.

1. Open Postman → **Import** → select `postman/postman_collection.json`.
2. Import `postman/postman_environment.json` the same way, then select
   **"TD AI Studio Access - Local"** from the environment dropdown
   (top-right).
3. Edit the environment's variables (click the eye icon, or the environment
   name):
   - `api_key` → your Master API key, `ACCOUNT_ID/KEY` format
   - `base_url` → defaults to `https://api.treasuredata.com` (US); change for other regions
   - `user_id` → the target user's numeric ID
4. Open **v4 → Check access (GET)** and hit **Send**. You should get `200 OK`
   with a body like `{"treasure_ai_studio": "full_access"}` or `null` if
   unset.
5. **Grant access (PUT)** and **Remove access (DELETE)** work the same way —
   just select the request and Send. Grant/Remove require the account
   administrator role on the key used.

Auth is pre-wired at the collection level as `Authorization: TD1 {{api_key}}`
— you shouldn't need to touch the Auth tab on individual requests.

⚠️ These calls are **not dry-run** — PUT actually grants access and DELETE
actually revokes it (immediately, if the account is in restricted mode).
Double check `user_id` before sending.

## How it works

By default, every user in an account can use Treasure AI Studio. To
restrict access to specific users only:

1. Grant access to the intended users (`grant`, below).
2. Ask your Customer Success Manager to enable **restricted (opt-in) mode**
   for the account. Once enabled, only users with an explicit grant can
   sign in to Studio — everyone else is denied by default.

Changes take effect at sign-in:
- **Granting** access lets the user start a Studio session from their next sign-in onward.
- **Removing** access (in restricted mode) immediately revokes issued credentials and blocks new sign-ins, but does not terminate an already-active session — the user must sign out or wait for expiration.

## Requirements

- Python 3.9+
- A Treasure Data **Master API key** (`ACCOUNT_ID/KEY` format). `grant` and
  `remove` require the account administrator role; `check` can be run by an
  account admin, delegated admin, or the user themselves.

## Setup

```bash
git clone https://github.com/tushar-fde-ai/user-studio-access.git
cd user-studio-access

pip install -r requirements.txt

cp .env.example .env
# edit .env and set TD_API_KEY (and TD_API_ENDPOINT / TD_API_VERSION if needed)
```

## Usage

```bash
# Grant a user Studio access
python main.py grant --user-id 12345

# Check whether a user currently has access
python main.py check --user-id 12345

# Remove a user's access grant
python main.py remove --user-id 12345
```

## Using the client directly

```python
from studio_access import StudioAccessClient

client = StudioAccessClient(api_key="123456/abcdef...")

result = client.grant_access(user_id=12345)
print(result.has_access)   # True

result = client.check_access(user_id=12345)
print(result.value)        # "full_access" or None

client.remove_access(user_id=12345)
```

## Project structure

```
user-studio-access/
├── main.py                  # CLI entry point (grant / check / remove)
├── studio_access/
│   ├── __init__.py
│   └── client.py             # StudioAccessClient, StudioAccessResult, StudioAccessError
├── postman/
│   ├── postman_collection.json     # import into Postman
│   └── postman_environment.json    # import + fill in api_key/user_id
├── requirements.txt
├── .env.example
└── README.md
```

## API reference

| Operation | v4 endpoint | v3 endpoint |
|---|---|---|
| Grant  | `PUT /v4/users/:user_id/profile_options/treasure_ai_studio` | `PUT /v3/access_control/users/:user_id/profile_options/treasure_ai_studio` |
| Check  | `GET /v4/users/:user_id/profile_options/treasure_ai_studio` | `GET /v3/access_control/users/:user_id/profile_options/treasure_ai_studio` |
| Remove | `DELETE /v4/users/:user_id/profile_options/treasure_ai_studio` | `DELETE /v3/access_control/users/:user_id/profile_options/treasure_ai_studio` |

The only accepted value for the `treasure_ai_studio` option is
`full_access`. All per-user access changes are recorded in the Premium
Audit Log.

## Notes

- Never commit your real `.env` file — it's git-ignored by default.
- v3 and v4 behave identically; v3 includes an `/access_control` path
  segment that v4 omits.
