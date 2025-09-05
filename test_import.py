import email
import sys

print("\n--- Diagnostic Information ---")
print(f"Python Executable: {sys.executable}")
print("-" * 20)

try:
    print(f"Location of the imported 'email' module:")
    print(email.__file__)
except Exception as e:
    print(f"Could not determine the location of the 'email' module. Error: {e}")

print("-" * 20)