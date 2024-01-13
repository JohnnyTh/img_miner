import argparse
import pathlib

from img_miner.miner import ImgMiner


def parse_images_limit(value: str) -> int:
    try:
        float_value = float(value)
        if float_value.is_integer():
            return int(float_value)
        else:
            raise ValueError("Invalid value for images_limit: not a valid integer")

    except ValueError as err:
        raise argparse.ArgumentTypeError(
            f"Invalid value for images_limit: {value}. "
            f"Must be an integer or a floating-point number in scientific notation."
        ) from err


def main() -> None:
    parser = argparse.ArgumentParser(description="Image Miner Script")
    parser.add_argument(
        "--save_dir", type=str, default="mined_data", help="Directory to save images"
    )
    parser.add_argument(
        "--addr", type=str, default="https://prnt.sc/", help="Base address for web scraping"
    )
    parser.add_argument(
        "--images_limit",
        type=parse_images_limit,
        default=100000,
        help="Limit on the number of images to download.",
    )

    args = parser.parse_args()

    save_dir = pathlib.Path(args.save_dir)
    addr: str = args.addr
    images_limit: int = args.images_limit

    miner = ImgMiner(web_addr_base=addr, save_dir=save_dir, n_threads=4, images_limit=images_limit)
    miner.mine()


if __name__ == "__main__":
    main()
