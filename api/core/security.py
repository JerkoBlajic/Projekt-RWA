# =============================================================
# security.py - Password hashing and verification
# =============================================================
# We use bcrypt directly (not the passlib wrapper, which has
# compatibility issues with bcrypt >= 4.1). bcrypt embeds the
# salt in the hash, so we do not store it separately.
# =============================================================

import bcrypt


def hash_password(plain: str) -> str:
    """Hash a plain-text password. Returns a DB-ready string."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Check a plain-text password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except ValueError:
        return False
