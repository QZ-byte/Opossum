import random, string

def generate_password(length=16, digits=True, upper=True, symbols=True):
    chars = list(string.ascii_lowercase)
    if digits:
        chars += list(string.digits)
    if upper:
        chars += list(string.ascii_uppercase)
    if symbols:
        chars += list("!@#$%^&*()-_=+[]{};:,.<>?")
    return "".join(random.choice(chars) for _ in range(length))
