import unittest
import string
import secrets

def generate_password_logic(length, use_upper, use_lower, use_digits, use_symbols, exclusions, enforce_all):
    upper_pool = [c for c in string.ascii_uppercase if c not in exclusions]
    lower_pool = [c for c in string.ascii_lowercase if c not in exclusions]
    digit_pool = [c for c in string.digits if c not in exclusions]
    symbols_list = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    symbol_pool = [c for c in symbols_list if c not in exclusions]

    active_pools = []
    if use_upper and upper_pool:
        active_pools.append(upper_pool)
    if use_lower and lower_pool:
        active_pools.append(lower_pool)
    if use_digits and digit_pool:
        active_pools.append(digit_pool)
    if use_symbols and symbol_pool:
        active_pools.append(symbol_pool)

    if not active_pools:
        return ""

    combined_pool = [char for pool in active_pools for char in pool]
    if not combined_pool:
        return ""

    password_chars = []
    if enforce_all and length >= len(active_pools):
        for pool in active_pools:
            password_chars.append(secrets.choice(pool))
        remaining = length - len(active_pools)
        for _ in range(remaining):
            password_chars.append(secrets.choice(combined_pool))
        secrets.SystemRandom().shuffle(password_chars)
    else:
        for _ in range(length):
            password_chars.append(secrets.choice(combined_pool))

    return "".join(password_chars)

class TestPasswordGenerator(unittest.TestCase):
    def test_length(self):
        for length in [8, 16, 32]:
            pwd = generate_password_logic(length, True, True, True, True, "", True)
            self.assertEqual(len(pwd), length)

    def test_exclusion(self):
        exclusions = "ABCabc123"
        for _ in range(50):
            pwd = generate_password_logic(16, True, True, True, True, exclusions, True)
            for char in exclusions:
                self.assertNotIn(char, pwd)

    def test_enforce_all(self):
        # When length is 4 and we request all 4 types, the password must contain exactly 1 of each
        for _ in range(50):
            pwd = generate_password_logic(4, True, True, True, True, "", True)
            has_upper = any(c in string.ascii_uppercase for c in pwd)
            has_lower = any(c in string.ascii_lowercase for c in pwd)
            has_digit = any(c in string.digits for c in pwd)
            has_symbol = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in pwd)
            self.assertTrue(has_upper)
            self.assertTrue(has_lower)
            self.assertTrue(has_digit)
            self.assertTrue(has_symbol)

if __name__ == "__main__":
    unittest.main()
