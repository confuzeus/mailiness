import argparse

from . import commands

def main():
    parser = argparse.ArgumentParser(description="Manage your mail server.")
    parser.add_argument("--version", "-v", action="store_true", default=False)

    args = parser.parse_args()

    if args.version:
        commands.print_version()

if __name__ == "__main__":
    main()
