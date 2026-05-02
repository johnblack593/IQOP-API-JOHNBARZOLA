# iqoptionapi/security.py
import os
import random

class CredentialConsumedError(Exception):
    pass

class CredentialStore:
    def __init__(self, email: str, password: str):
        self.email = email
        self._password = password
        self._consumed = False

    @property
    def password(self):
        # Prevent direct property access to avoid accidental leakage in logs/repr
        raise AttributeError("Password cannot be accessed via property. Use .consume() instead.")

    def consume(self) -> str:
        """
        Returns the password.
        NOTE: Password is kept in memory to support Auto-Reconnect (S1-03).
        """
        return self._password

    def __repr__(self):
        return f"CredentialStore(email='{self.email}', password='[PROTECTED]')"

    def __str__(self):
        return self.__repr__()

    @classmethod
    def from_env(cls, email_env: str = "IQ_EMAIL", password_env: str = "IQ_PASSWORD") -> "CredentialStore":
        email = os.environ.get(email_env)
        password = os.environ.get(password_env)
        if not email or not password:
            raise EnvironmentError(f"Missing environment variables. Ensure {email_env} and {password_env} are set.")
        return cls(email, password)

def generate_user_agent() -> str:
    # Chrome stable range active in 2026 (v124–v132)
    version = random.choice([124, 125, 126, 127, 128, 129, 130, 131, 132])
    return f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version}.0.0.0 Safari/537.36"
