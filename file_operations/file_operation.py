import time
from abc import ABC, abstractmethod
from pathlib import Path


class FileOperation(ABC):
    def __init__(self, **kwargs):
        self.ready: bool = True
        self.__stop: bool = False
        self.sleep: float = 60.0
        self.files_for_task: tuple = ()
        self.pattern: tuple = ()
        self.src: str = ""
        self.dst: str = ""

        for key, value in kwargs.items():
            setattr(self, key, value)

        self.source_directory = Path(self.src)
        self.target_directory = Path(self.dst)

    def get_files(self):
        # Використовуємо rglob, якщо треба шукати і в підпапках, або glob для поточної
        files = set()
        for p in self.pattern:
            # Шукаємо за кожним патерном
            current_pattern_files = self.source_directory.glob(f"*{p}*")
            files.update(current_pattern_files)

        self.files_for_task = tuple(files)

    def check_source_directory(self) -> None:
        if not self.source_directory.exists():
            print(f"[ERROR] Source path '{self.src}' does not exist.")
            raise FileNotFoundError

    def check_directories(self) -> None:
        self.check_source_directory()
        self.target_directory.mkdir(parents=True, exist_ok=True)


    def run(self):
        self.check_directories()
        while True:
            try:

                self.get_files()

                if len(self.files_for_task) == 0:
                    print(f"[!] No files found in {self.source_directory}. Waiting {self.sleep} seconds.", end="\n",
                          flush=True)
                    time.sleep(self.sleep)
                    continue

                self.do_task()


            except KeyboardInterrupt:
                self.stop = True
                print("\nCtrl+C pressed, stopping move.")

            if self.stop or not self.repeat:
                break

    @abstractmethod
    def do_task(self):
        pass

    @property
    def sleep(self):
        return self._sleep

    @sleep.setter
    def sleep(self, value):
        self._sleep = int(value)

    @property
    def stop(self):
        return self.__stop

    @stop.setter
    def stop(self, value):
        self.__stop = value

    @property
    def pattern(self):
        return self._pattern

    @pattern.setter
    def pattern(self, value):
        if isinstance(value, str):
            self._pattern = (value, )
        else:
            self._pattern = value
