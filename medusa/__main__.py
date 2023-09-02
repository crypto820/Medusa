import argparse
import logging


def setup_logger():
    logging.basicConfig()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", type=str, required=True)
    parser.add_argument("-o", "--output", type=str, required=True)
    parser.add_argument("--frontend", type=str, required=False, default="clash")
    parser.add_argument("--backend", type=str, required=False, default="glider")
    args = parser.parse_args()
    return


if __name__ == "__main__":
    exit(main())
