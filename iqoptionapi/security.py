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
        if self._consumed:
            raise CredentialConsumedError("Password has already been consumed. Re-instantiate CredentialStore to authenticate again.")
        raise AttributeError("Password cannot be accessed via property. Use .consume() instead.")

    def consume(self) -> str:
        if self._consumed:
            raise CredentialConsumedError("Password has already been consumed. Re-instantiate CredentialStore to authenticate again.")
        val = self._password
        self._password = ""
        self._consumed = True
        return val

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
    version = random.choice([120, 121, 122, 123, 124])
    return f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version}.0.0.0 Safari/537.36"
