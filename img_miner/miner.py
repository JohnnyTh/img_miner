import pathlib
import signal
import sys
import types
import typing
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from joblib import Parallel, delayed
from loguru import logger

from img_miner.filesystem import read_json, write_json
from img_miner.http_connection import HTTPConnection
from img_miner.name_generators import ImgIdGeneratorRandom
from img_miner.schemas import ArtefactInfo, ProgressTracker

__all__ = ["ImgMiner"]


class ImgMiner:
    def __init__(
        self,
        web_addr_base: str,
        save_dir: pathlib.Path,
        n_threads: int = 2,
        save_progress_every_iters: int = 1000,
        image_batch_size: int = 1000,
        images_limit: int = int(10e6),
    ) -> None:
        self.web_addr_base = web_addr_base
        self.n_threads = n_threads
        self.save_progress_every_iters = save_progress_every_iters
        self.image_batch_size = image_batch_size
        self.images_limit = images_limit

        self.img_dir = save_dir / "images"
        self.progress_tracker_p = save_dir / "progress_tracker.json"

        self.progress = self._restore_progress()
        self.generator = ImgIdGeneratorRandom(generate_from_idx=self.progress.n_processed + 1)

        self.progress.random_seed = getattr(self.generator, "seed", None)
        self.progress.generator_type = self.generator.__class__.__name__

        if not self.img_dir.exists():
            self.img_dir.mkdir(parents=True)

        self.connection = HTTPConnection(
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
                )
            },
            retries_total=25,
            backoff_factor_seconds=10,
        )

        signal.signal(signal.SIGTERM, self._handle_stop_signal)
        signal.signal(signal.SIGINT, self._handle_stop_signal)

    def _save_progress(self) -> None:
        logger.info(f"Saving mining progress to {self.progress_tracker_p}")
        write_json(self.progress.model_dump(mode="json"), self.progress_tracker_p)

    def _restore_progress(self) -> ProgressTracker:
        if self.progress_tracker_p.exists():
            logger.info(f"Restoring mining progress from: {self.progress_tracker_p}")
            progress = ProgressTracker(**read_json(self.progress_tracker_p))
            logger.info(f"Restored: {progress}")
        else:
            logger.info("Initializing new mining progress tracker")
            progress = ProgressTracker()
        return progress

    @staticmethod
    def _save_image_metadata(info: ArtefactInfo, save_dir: pathlib.Path) -> None:
        metadata_name = f"{str(info.index_download).zfill(4)}_metadata.json"
        metadata_p = save_dir / metadata_name

        write_json(info.model_dump(mode="json"), metadata_p)

    @staticmethod
    def _download_file(url: str, local_p: pathlib.Path) -> bool:
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

    def _mine(self, image_index: int, id_img: str, save_dir: pathlib.Path) -> bool:
        success = False
        img_p_local = None
        url_img_hosting = None

        url_img = urljoin(self.web_addr_base, id_img)

        response = self.connection.make_request(url_img)

        if response is not None and response.status_code == 200:
            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(response.content, "html.parser")
            element = soup.findAll("img", {"class": "no-click screenshot-image"})[0]
            url_img_hosting = element.attrs["src"]

            img_extension = pathlib.Path(url_img_hosting).suffix
            img_p_local = save_dir / f"{str(image_index).zfill(4)}{img_extension}"

            try:
                success = self._download_file(url_img_hosting, img_p_local)
            except Exception as err:
                logger.error(f"{err}")

        img_info = ArtefactInfo(
            local_p=img_p_local,
            url_primary=url_img,
            url_hosting=url_img_hosting,
            index_download=image_index,
            success_download=success,
        )
        self._save_image_metadata(img_info, save_dir)

        return success

    def _handle_stop_signal(
        self, signum: int, frame: typing.Optional[types.FrameType] = None
    ) -> None:
        logger.info(f"Received signal {signum}. Stopping miner")
        self._save_progress()
        sys.exit(0)

    def mine(self) -> None:
        running = True

        with Parallel(n_jobs=self.n_threads, backend="threading") as parallel:
            while running:
                img_ids_batch = self.generator.generate_n_ids(self.image_batch_size)
                save_dir = self.img_dir / f"batch_{str(self.progress.batch_id).zfill(10)}"
                if not save_dir.exists():
                    save_dir.mkdir()

                logger.info(
                    f"Extracting batch to dir: {save_dir}. "
                    f"Stats: total_images_processed={self.progress.n_processed}. "
                    f" total_image_success={self.progress.n_successful}"
                )
                delayed_jobs = []
                for image_index_batch, image_id in enumerate(img_ids_batch):
                    delayed_jobs.append(delayed(self._mine)(image_index_batch, image_id, save_dir))

                success_batch = list(parallel(delayed_jobs))

                self.progress.n_successful += success_batch.count(True)

                self.progress.n_processed += len(img_ids_batch)
                self.progress.batch_id += 1

                if self.progress.n_processed % self.save_progress_every_iters == 0:
                    self._save_progress()

                if self.progress.n_processed >= self.images_limit:
                    logger.info(f"Reached image limit: {self.images_limit}, exiting")
                    self._save_progress()
                    running = False
