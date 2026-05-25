import pytest
import sqlite3

from test_db import test_tx_db
from adding_accounts import get_balances_and_transactions, unpack_balances_and_transactions

from assets import trans_and_balances

def test_get_balances_and_transactions():
    r = unpack_balances_and_transactions(trans_and_balances)
    print(r)