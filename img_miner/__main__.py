import argparse
import pathlib

from img_miner.miner import ImgMiner


def main() -> None:
    parser = argparse.ArgumentParser(description="Image Miner Script")
    parser.add_argument(
        "--save_dir", type=str, default="mined_data", help="Directory to save images"
    )
    parser.add_argument(
        "--addr", type=str, default="https://prnt.sc/", help="Base address for web scraping"
    )

    args = parser.parse_args()

    save_dir = pathlib.Path(args.save_dir)
    addr: str = args.addr

    miner = ImgMiner(web_addr_base=addr, save_dir=save_dir, n_threads=4)
    miner.mine()


if __name__ == "__main__":
    main()
