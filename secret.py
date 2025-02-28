import secrets
import string

# Generate a random secret key with 32 characters


def generate_secret_key(length=32):
    characters = string.ascii_letters + string.digits + string.punctuation
    secret_key = ''.join(secrets.choice(characters) for _ in range(length))
    return secret_key


# Print the generated secret key
print(generate_secret_key())
