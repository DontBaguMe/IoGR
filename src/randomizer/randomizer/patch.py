import tempfile


class Patch:
    def __init__(self, rom_data, logger):
        self.data = dict()
        self.logger = logger
        self.temp = tempfile.TemporaryFile()
        self.temp.write(rom_data)

    def __del__(self):
        self.temp.close()

    def seek(self, position: int) -> None:
        self.temp.seek(position)

    def write(self, data: bytes) -> None:
        arr = [x for x in data]
        #  self.logger.debug("address," + str(self.temp.tell()) + ",value," + str(len(arr)))
        #  print("address," + str(self.temp.tell()) + ",value," + str(len(arr)))

        self.data[self.temp.tell()] = arr
        self.temp.write(data)

    def read(self, n: int = None):
        return self.temp.read(n)

    def find(self, sub, start=None, end=None):
        d = self.read()
        return d.find(sub, start, end)
