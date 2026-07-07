# Modern Password Generator App

A cryptographically secure, visually polished password generator built using Python and standard `tkinter` / `ttk`.

## Features
- **Cryptographic Security**: Generates random numbers and selects characters using Python's `secrets` module (cryptographically secure), not the standard pseudo-random `random` module.
- **Visual Entropy Meter**: Dynamically calculates Shannon entropy (in bits) as you toggle parameters and length, giving real-time feedback on how secure your password is.
- **Interactive UI**: Slider for length (4 to 64), toggles for Uppercase/Lowercase letters, numbers, and symbols.
- **Complexity Enforcer**: Optionally ensures at least one character from each active category is present in the final password.
- **Exclusion Filters**: Filter out custom characters (e.g. to avoid similar looking characters like `O`/`0` or `I`/`l`/`1`).
- **History Panel**: Stores the last 10 generated passwords, masked by default for privacy, with toggleable eye button and copy action.

## How to Run
1. Make sure Python 3 is installed.
2. Navigate to the project directory in your terminal or Command Prompt.
3. Run the following command:
   ```bash
   python password_generator.py
   ```
