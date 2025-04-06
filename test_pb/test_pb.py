import pytest
import sqlite3
from test_pb import assets

from db import TokensConnection


@pytest.fixture
def test_db():
    """Fixture that creates an in-memory database with test structure"""
    # Use :memory: for faster tests that don't need cleanup
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row  # Match your production setup
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute(assets.tokens_table)
    conn.commit()
    
    yield conn
    
    # Cleanup
    conn.close()

@pytest.fixture
def tokens_connection(test_db):
    """Fixture that provides a TokensConnection instance with test DB"""
    # Create a subclass that uses our test connection
    class TestTokensConnection(TokensConnection):
        def __init__(self):
            # Override the parent's connection with our test connection
            self.con = test_db
            self.cursor = self.con.cursor()
    
    return TestTokensConnection()




def test_test(tokens_table):
    print("Help!!1")

