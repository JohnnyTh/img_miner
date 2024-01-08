import itertools
import random
import string
import typing
from abc import ABC, abstractmethod

from loguru import logger

__all__ = ["ImgIdGenerator", "ImgIdGeneratorRandom", "ImgIdGeneratorSequential"]


class ImgIdGenerator(ABC):
    def __init__(
        self, first_char: str = "a", generate_from_idx: int = 0, n_chars_total: int = 6
    ) -> None:
        self.first_char = first_char
        self.generate_from_idx = generate_from_idx
        self.n_chars_total = n_chars_total

        self.n_characters_base = self.n_chars_total - 1
        self.characters_pool = string.ascii_lowercase + string.digits
        logger.info(
            f"Generator initialized to produce "
            f"{self.n_characters_base ** len(self.characters_pool):e} combinations"
        )
        if self.generate_from_idx > 0:
            logger.debug(f"First {self.generate_from_idx} combinations will be skipped")

    @abstractmethod
    def __iter__(self) -> "ImgIdGenerator":
        pass

    @abstractmethod
    def __next__(self) -> str:
        pass

    def generate_n_ids(self, n: int) -> typing.List[str]:
        image_ids = []
        for _ in range(n):
            image_ids.append(next(self))

        return image_ids


class ImgIdGeneratorRandom(ImgIdGenerator):
    def __init__(
        self,
        first_char: str = "a",
        generate_from_idx: int = 0,
        n_chars_total: int = 6,
        seed: int = 42,
    ):
        super().__init__(first_char, generate_from_idx, n_chars_total)
        logger.debug(f"Set random seed to: {seed}")
        random.seed(seed)
        for _ in range(self.generate_from_idx):
            _ = self._generate()

    def _generate(self) -> str:
        img_id = self.first_char + "".join(
            random.choices(self.characters_pool, k=self.n_characters_base)
        )
        return img_id

    def __iter__(self) -> "ImgIdGeneratorRandom":
        return self

    def __next__(self) -> str:
        return self._generate()


class ImgIdGeneratorSequential(ImgIdGenerator):
    def __init__(self, first_char: str = "a", generate_from_idx: int = 0, n_chars_total: int = 6):
        super().__init__(first_char, generate_from_idx, n_chars_total)

        self._image_ids_generator = self._prep_generator()

    def _prep_generator(self) -> itertools.product:
        image_ids_generator = itertools.product(self.characters_pool, repeat=self.n_characters_base)

        if self.generate_from_idx > 0:
            logger.debug(f"Skipping first {self.generate_from_idx} combinations")

        for _ in range(self.generate_from_idx):
            next(image_ids_generator, None)

        return image_ids_generator

    def __iter__(self) -> "ImgIdGeneratorSequential":
        return self

    def __next__(self) -> str:
        try:
            image_id = self.first_char + "".join(next(self._image_ids_generator))
            return image_id

        except StopIteration as err:
            raise StopIteration from err
