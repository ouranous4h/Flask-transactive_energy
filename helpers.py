import os
import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps

from math import cos, asin, sqrt

def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characfters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


# def lookup(symbol):
#     """Look up quote for symbol."""

#     # Contact API
#     try:
#         api_key = os.environ.get("API_KEY")
#         response = requests.get(f"https://cloud-sse.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}/quote?token={api_key}")
#         response.raise_for_status()
#     except requests.RequestException:
#         return None

#     # Parse response
#     try:
#         quote = response.json()
#         return {
#             "name": quote["companyName"],
#             "price": float(quote["latestPrice"]),
#             "symbol": quote["symbol"]
#         }
#     except (KeyError, TypeError, ValueError):
#         return None


### for calculating distance between two points on the globe
def distance(lat1, lon1, lat2, lon2):
    p = 0.017453292519943295
    a = 0.5 - cos((lat2-lat1)*p)/2 + cos(lat1*p)*cos(lat2*p) * (1-cos((lon2-lon1)*p)) / 2
    return 12742 * asin(sqrt(a))


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"

def watt(value):
    """Format value as USD."""
    return f"{value:d} Watt"
