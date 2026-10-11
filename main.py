# ==================================================
# SETUP
# ==================================================

# ? IMPORTS
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import pandas as pd
import typer
from dotenv import load_dotenv

from request_engine import RequestEngine
from urls import BASE_URL

# ? LOAD VIRTUAL ENVIRONMENT
load_dotenv('.venv/vars.env')

# ? INITS
app = typer.Typer(
    help="ECHO-ADMIN CLI — administrative command line interface for the ECHO application.",
    no_args_is_help=True,
    add_completion=False,
)

user_app = typer.Typer(help="Manage application users.", no_args_is_help=True)
promo_app = typer.Typer(help="Manage promo codes.", no_args_is_help=True)
credits_app = typer.Typer(help="Inspect and manipulate user credits.", no_args_is_help=True)
logs_app = typer.Typer(help="Download application log files.", no_args_is_help=True)

app.add_typer(user_app, name="user")
app.add_typer(promo_app, name="promo")
app.add_typer(credits_app, name="credits")
app.add_typer(logs_app, name="logs")

engine = RequestEngine()
VERSION = "echo-admin 0.1.0"


# ==================================================
# HELPERS
# ==================================================

def _emit(payload: Any) -> None:
    """Pretty-print a JSON-serializable payload to stdout."""
    if (isinstance(payload, (dict, list))):
        typer.echo(json.dumps(payload, indent=4, default=str))
    else:
        typer.echo(payload)


def _check(response, *, expect_json: bool = True) -> Optional[dict]:
    """
    Validate a response and return the decoded JSON body.

    On any non-2xx status the CLI prints a human-readable error and exits
    with code 1 so shell pipelines can detect failures.
    """
    payload: Optional[dict]
    try:
        payload = response.json() if expect_json else None
    except ValueError:
        payload = None

    if (response.status_code >= 400):
        message = (payload or {}).get('message') or response.text or 'Unknown error.'
        typer.secho(f"[{response.status_code}] {message}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    return payload


def _confirm(question: str, skip: bool) -> None:
    """Abort the command unless ``skip`` is True or the user confirms."""
    if (not skip):
        typer.confirm(question, abort=True)


# ==================================================
# ROOT CALLBACK
# ==================================================

@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show the current version and exit.",
    ),
) -> None:
    """ECHO-ADMIN command line interface."""
    if version:
        typer.echo(VERSION)
        raise typer.Exit()


# ==================================================
# USER COMMANDS
# ==================================================

@user_app.command("list")
def user_list(
    filename: Optional[str] = typer.Argument(
        None,
        help="Optional path to persist the users table as a CSV file. "
             "The filename must end with '.csv'.",
    ),
) -> None:
    """Fetch and display every registered user."""
    response = engine.get(f"{BASE_URL}/users")
    payload  = _check(response)

    users = (payload or {}).get('output_obj') or []
    if (not users):
        typer.secho("No users found.", fg=typer.colors.YELLOW)
        return

    df = pd.DataFrame(users)
    typer.echo(df.to_string(index=False))

    if (filename):
        if (not filename.endswith(".csv")):
            typer.secho(
                "Filename must end with '.csv'.",
                fg=typer.colors.RED,
                err=True,
            )
            raise typer.Exit(code=1)
        df.to_csv(filename, index=False)
        typer.secho(f"Users exported to '{filename}'.", fg=typer.colors.GREEN)


@user_app.command("get")
def user_get(
    user_id: str = typer.Argument(..., help="The unique ID of the user to fetch."),
) -> None:
    """Fetch the details of a single user."""
    response = engine.get(f"{BASE_URL}/users/{user_id}")
    payload  = _check(response)
    _emit((payload or {}).get('details') or payload)


@user_app.command("patch")
def user_patch(
    user_id: str = typer.Argument(..., help="The unique ID of the user to update."),
    name: Optional[str]          = typer.Option(None, "--name",          help="Full name of the user."),
    email: Optional[str]         = typer.Option(None, "--email",         help="Email address of the user."),
    site_url: Optional[str]      = typer.Option(None, "--site-url",      help="Website associated with the user."),
    total_credits: Optional[int] = typer.Option(None, "--total-credits", help="Total credits assigned to the user."),
    left_credits: Optional[int]  = typer.Option(None, "--left-credits",  help="Credits the user has remaining."),
    last_plan: Optional[str]     = typer.Option(None, "--last-plan",     help="The user's previous subscription plan."),
    current_plan: Optional[str]  = typer.Option(None, "--current-plan",  help="The user's current subscription plan."),
    renewal_date: Optional[str]  = typer.Option(None, "--renewal-date",  help="Plan renewal date (YYYY-MM-DD)."),
) -> None:
    """Update one or more fields on an existing user."""
    body = {
        key: value
        for key, value in {
            "name": name,
            "email": email,
            "site_url": site_url,
            "total_credits": total_credits,
            "left_credits": left_credits,
            "last_plan": last_plan,
            "current_plan": current_plan,
            "renewal_date": renewal_date,
        }.items()
        if value is not None
    }

    if (not body):
        typer.secho(
            "Nothing to update: provide at least one option.",
            fg=typer.colors.YELLOW,
            err=True,
        )
        raise typer.Exit(code=1)

    response = engine.patch(f"{BASE_URL}/users/{user_id}", json=body)
    payload  = _check(response)
    typer.secho(
        (payload or {}).get('message') or "User updated successfully!",
        fg=typer.colors.GREEN,
    )


@user_app.command("delete")
def user_delete(
    user_id: str = typer.Argument(..., help="The unique ID of the user to delete."),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip the interactive confirmation prompt.",
    ),
) -> None:
    """Permanently delete a user and all of their associated records."""
    _confirm(
        f"Delete user '{user_id}' and EVERY related record (captions, headlines, "
        f"products, orders, payments, ...)? This cannot be undone.",
        skip=yes,
    )

    response = engine.delete(f"{BASE_URL}/users/{user_id}")
    payload  = _check(response)
    typer.secho(
        (payload or {}).get('message') or "User deleted.",
        fg=typer.colors.GREEN,
    )


# ==================================================
# PROMO COMMANDS
# ==================================================

@promo_app.command("list")
def promo_list() -> None:
    """List every promo code with aggregate statistics."""
    response = engine.get(f"{BASE_URL}/promo")
    payload  = _check(response)
    _emit(payload)


@promo_app.command("get")
def promo_get(
    promo_id: str = typer.Argument(..., help="The unique ID of the promo code to fetch."),
) -> None:
    """Fetch a single promo code's details."""
    response = engine.get(f"{BASE_URL}/promo/{promo_id}")
    payload  = _check(response)
    _emit((payload or {}).get('details') or payload)


@promo_app.command("create")
def promo_create(
    code: str            = typer.Option(..., "--code",    "-c", help="Unique promo code string."),
    plans: str           = typer.Option(..., "--plans",   "-p", help="Comma-separated list of plans the promo applies to."),
    limit: int           = typer.Option(..., "--limit",   "-l", help="Maximum number of users that may redeem the promo."),
    expiry: str          = typer.Option(..., "--expiry",  "-e", help="Expiration date (YYYY-MM-DD)."),
    sponsor: Optional[str]  = typer.Option(None, "--sponsor",  "-s", help="Sponsor of the promo code."),
    credits: Optional[int]  = typer.Option(None, "--credits",        help="Credits granted to redeemers."),
    discount: Optional[float] = typer.Option(None, "--discount",     help="Discount percentage (e.g. 0.15 = 15%)."),
) -> None:
    """Create a new promo code."""
    body = {
        "code": code,
        "sponsor": sponsor,
        "credits": credits,
        "discount": discount,
        "plans": plans,
        "limit": limit,
        "expiry": expiry,
    }

    response = engine.post(f"{BASE_URL}/promo/new", json=body)
    payload  = _check(response)
    typer.secho(
        (payload or {}).get('message') or "Promo code created.",
        fg=typer.colors.GREEN,
    )
    _emit((payload or {}).get('details'))


@promo_app.command("patch")
def promo_patch(
    promo_id: str = typer.Argument(..., help="The unique ID of the promo code to update."),
    credits: Optional[int]         = typer.Option(None, "--credits",         help="New credits value."),
    available_plans: Optional[str] = typer.Option(None, "--available-plans", help="Comma-separated list of applicable plans."),
    limit: Optional[int]           = typer.Option(None, "--limit",           help="New redemption limit."),
    expiry: Optional[str]          = typer.Option(None, "--expiry",          help="New expiration date (YYYY-MM-DD)."),
) -> None:
    """Update one or more fields on an existing promo code."""
    plans = available_plans.split(",") if available_plans else None

    body = {
        key: value
        for key, value in {
            "credits": credits,
            "available_plans": plans,
            "limit": limit,
            "expiry": expiry,
        }.items()
        if value is not None
    }

    if (not body):
        typer.secho(
            "Nothing to update: provide at least one option.",
            fg=typer.colors.YELLOW,
            err=True,
        )
        raise typer.Exit(code=1)

    response = engine.patch(f"{BASE_URL}/promo/{promo_id}", json=body)
    payload  = _check(response)
    typer.secho(
        (payload or {}).get('message') or "Promo code updated.",
        fg=typer.colors.GREEN,
    )


@promo_app.command("delete")
def promo_delete(
    promo_id: str = typer.Argument(..., help="The unique ID of the promo code to delete."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip the interactive confirmation prompt."),
) -> None:
    """Delete a promo code."""
    _confirm(f"Delete promo code '{promo_id}'?", skip=yes)

    response = engine.delete(f"{BASE_URL}/promo/{promo_id}")
    payload  = _check(response)
    typer.secho(
        (payload or {}).get('message') or "Promo code deleted.",
        fg=typer.colors.GREEN,
    )


# ==================================================
# CREDITS COMMANDS
# ==================================================

@credits_app.command("manipulate")
def credits_manipulate(
    user_id: str = typer.Option(..., "--user-id", "-u", help="The unique ID of the user whose credits will change."),
    amount: int  = typer.Option(
        ...,
        "--amount",
        "-a",
        help="Credits to add (positive integer) or remove (negative integer).",
    ),
) -> None:
    """
    Increase or decrease a user's total and remaining credits.

    The same ``amount`` is applied to both ``total_credits`` and
    ``left_credits`` — matching the semantics of the admin API.
    """
    if (amount == 0):
        typer.secho("Amount must be non-zero.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    body = {"userid": user_id, "credits": amount}
    response = engine.patch(f"{BASE_URL}/credits/manipulate", json=body)
    payload  = _check(response)

    typer.secho(
        (payload or {}).get('message') or "Credits updated.",
        fg=typer.colors.GREEN,
    )
    _emit((payload or {}).get('details'))


# ==================================================
# LOG COMMANDS
# ==================================================

@logs_app.command("download")
def logs_download(
    log_type: str = typer.Argument(
        ...,
        help="The log file to fetch (e.g. 'app', 'error', 'access').",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Destination path. Defaults to './<log_type>.log'.",
    ),
) -> None:
    """Download a log file from the server."""
    destination = output or Path(f"{log_type}.log")

    response = engine.download(
        f"{BASE_URL}/logs/download",
        destination=destination,
        log_type=log_type,
    )

    if (response.status_code != 200):
        try:
            message = response.json().get('message')
        except ValueError:
            message = response.text or "Download failed."
        typer.secho(f"[{response.status_code}] {message}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    typer.secho(
        f"Log '{log_type}' saved to '{destination}'.",
        fg=typer.colors.GREEN,
    )


# ==================================================
# RUN
# ==================================================

if (__name__ == "__main__"):
    app()