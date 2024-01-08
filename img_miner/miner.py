import json
import pathlib
import typing
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from data_structures import ArtefactInfo
from loguru import logger
from name_generators import ImgIdGenerator, ImgIdGeneratorRandom


def download_file(url: str, local_p: pathlib.Path) -> bool:
    response = requests.get(url)

    success = False
    if response.status_code == 200:
        logger.debug(f"Save file to {local_p}")
        with open(local_p, "wb") as file:
            file.write(response.content)
        success = True
    else:
        logger.warning(f"Failed to download url={url}. Status code: {response.status_code}")

    return success


def read_json(path: pathlib.Path) -> typing.Dict[typing.Any, typing.Any]:
    with open(path, "r") as file:
        data = json.load(file)
    return data


def write_json(path: pathlib.Path, json_: typing.Dict[typing.Any, typing.Any]) -> None:
    with open(path, "w") as file:
        json.dump(json_, file)


class ImgMiner:
    def __init__(
        self, web_addr_base: str, save_dir: pathlib.Path, img_id_generator: ImgIdGenerator
    ) -> None:
        self.web_addr_base = web_addr_base
        self.save_dir = save_dir
        self.img_dir = save_dir / "images"

        if not self.img_dir.exists():
            self.img_dir.mkdir(parents=True)

        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            )
        }

        self.mined_cache = self._parse_mined_images()
        self.gen = img_id_generator

    def _parse_mined_images(self) -> typing.List[str]:
        mined_ids_ = list(self.img_dir.glob("*.png"))
        mined_ids = [id_.name.split("_")[0] for id_ in mined_ids_]
        return mined_ids

    @staticmethod
    def _save_image_metadata(info: ArtefactInfo, save_dir: pathlib.Path) -> None:
        metadata_name = f"{str(info.index_download).zfill(4)}_metadata.json"
        metadata_p = save_dir / metadata_name

        write_json(metadata_p, info.model_dump(mode="json"))

    def _mine(self, index_download: int) -> bool:
        success = False
        img_p_local = None
        url_img_hosting = None

        id_img = next(self.gen)

        if id_img in self.mined_cache:
            logger.debug(f"id_img={id_img} already mined")
            success = True
        else:
            url_img = urljoin(self.web_addr_base, id_img)

            response = requests.get(url_img, allow_redirects=True, headers=self.headers)

            if response.status_code == 200:
                # Parse the HTML content using BeautifulSoup
                soup = BeautifulSoup(response.content, "html.parser")
                element = soup.findAll("img", {"class": "no-click screenshot-image"})[0]
                url_img_hosting = element.attrs["src"]

                img_extension = pathlib.Path(url_img_hosting).suffix
                img_p_local = self.img_dir / f"{str(index_download).zfill(4)}{img_extension}"

                try:
                    success = download_file(url_img_hosting, img_p_local)
                except Exception as err:
                    logger.error(f"{err}")

            img_info = ArtefactInfo(
                local_p=img_p_local,
                url_primary=url_img,
                url_hosting=url_img_hosting,
                index_download=index_download,
                success_download=success,
            )
            self._save_image_metadata(img_info, self.img_dir)

        return success

    def mine(self) -> None:
        running = True

        n_mined = 0
        n_processed = 0
        while running:
            logger.info(f"Extracting image: {n_processed}. Extracted with success: {n_mined}")
            success = self._mine(n_processed)

            if success:
                n_mined += 1

            n_processed += 1


def main() -> None:
    save_dir = pathlib.Path("data3")
    addr = "https://prnt.sc/"

    miner = ImgMiner(web_addr_base=addr, save_dir=save_dir, img_id_generator=ImgIdGeneratorRandom())
    miner.mine()


if __name__ == "__main__":
    main()
