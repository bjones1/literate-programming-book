<h1 id="cc-t95-jpUTgJ">Signing in with Microsoft Teams accounts</h1>

Teams doesn't have its own sign-in system. It uses **Microsoft Entra ID**
accounts (formerly Azure AD), the same ones behind Outlook and the rest of
Microsoft 365. Any app that offers "Sign in with Microsoft" (OpenID Connect) can
therefore log users in with their Teams credentials. You don't need a Teams app
or manifest.

This guide registers an app in Entra, then runs a Python script that signs a
user in and prints their name and email.

1\. Register the app
--------------------

1. Go to [https://entra.microsoft.com](https://entra.microsoft.com) → **App
   registrations** → **New registration**.
2. <strong>Name:</strong> anything you like, e.g. `Teams login test`.
3. <strong>Supported account types:</strong>: choose *Accounts in this
   organizational directory only*.
4. <strong>Redirect URI:</strong> set the platform to <strong>Public
   client/native (mobile \& desktop)</strong> and the value to
   `http://localhost`.
5. Click **Register**, then copy the **Application (client) ID** from the
   Overview page.

If your organization doesn't let regular users register apps, ask IT to do
step 1.

2\. The script
--------------

Save the script below as `teams_login.py`. It uses
[uv](https://docs.astral.sh/uv/) inline metadata, so uv installs the
dependencies automatically.

```python
# /// script
# requires-python = ">=3.10"
# dependencies = ["msal>=1.28", "requests"]
# ///
"""Sign in with a Microsoft (Teams) account and print the user's identity."""

import argparse
import json
import sys

import msal
import requests

p = argparse.ArgumentParser()
p.add_argument("client_id")
p.add_argument("--tenant", default="organizations",
               help="tenant ID/domain, 'organizations' (work/school), or 'common' (+personal)")
p.add_argument("--graph", action="store_true",
               help="also request User.Read and call Graph /me")
args = p.parse_args()

app = msal.PublicClientApplication(
    args.client_id, authority=f"https://login.microsoftonline.com/{args.tenant}"
)
# MSAL always adds openid and profile; email has to be requested explicitly.
scopes = ["email"] + (["User.Read"] if args.graph else [])

# Opens a browser and waits for the redirect to http://localhost.
result = app.acquire_token_interactive(scopes=scopes, prompt="select_account")

if "error" in result:
    print(f"FAILED: {result['error']}\n{result.get('error_description')}")
    sys.exit(1)

claims = result["id_token_claims"]
print("Name: ", claims.get("name"))
# email is missing if the account has no mailbox; preferred_username
# (usually the UPN, e.g. jdoe@school.edu) is the fallback.
print("Email:", claims.get("email") or claims.get("preferred_username"))
print("ID:   ", f"{claims['tid']}/{claims['oid']}")

if args.graph:
    r = requests.get("https://graph.microsoft.com/v1.0/me",
                     headers={"Authorization": f"Bearer {result['access_token']}"})
    print(json.dumps(r.json(), indent=2))
```

3\. Run it
----------

```
uv run teams_login.py <client-id>
```

A browser window opens. Sign in with your Teams account, accept the consent
prompt, and the script prints:

```
Name:  Jane Doe
Email: jdoe@school.edu
ID:    <tenant-id>/<object-id>
```

Which value identifies the user
-------------------------------

* <strong>`name` and `email`/`preferred_username`</strong> are for display. They
  can change (after a name change or a domain migration, for example), so don't
  use them as keys.
* <strong>`tid` + `oid`</strong> (tenant ID + object ID) is permanent and
  unique. Use it as the primary key in your database.

Troubleshooting
---------------

* <strong>"Need admin approval"</strong> (errors `AADSTS65001` or
  `AADSTS90094`): your organization blocks user consent. Ask IT to grant
  tenant-wide admin consent for the app. Try once without `--graph`, too: some
  tenants allow the basic sign-in scopes but block `User.Read`.
* <strong>`AADSTS50011` (redirect URI mismatch):</strong> check that
  `http://localhost` is registered under *Mobile and desktop applications*, not
  *Web*.

Moving to a web app
-------------------

A real web app uses the same identity. The differences:

* Register a **Web** redirect URI, such as `https://yourapp/auth/callback`.
* Add a client secret or certificate.
* Use `msal.ConfidentialClientApplication` (or any OIDC library) with the
  authorization-code flow.

The ID token contains the same claims (`name`, `email`, `oid`, `tid`), so
everything above still applies.
