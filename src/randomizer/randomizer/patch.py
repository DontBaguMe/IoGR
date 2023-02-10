import tempfile


class Patch:
    step = 0

    def __init__(self, rom_data, logger):
        self.patch_data = []
        self.logger = logger
        self.temp = tempfile.TemporaryFile()
        self.temp.write(rom_data)

    def __del__(self):
        self.temp.close()

    def seek(self, position: int) -> None:
        self.temp.seek(position)

    def write(self, data: bytes) -> None:
        arr = [x for x in data]
        address = int(self.temp.tell())

        self.patch_data.append({'index': self.step, 'address': address, 'data': arr})
        self.temp.write(data)
        self.step += 1

    def read(self, n: int = None):
        return self.temp.read(n)

    def readinto(self, container: bytearray) -> None:
        return self.temp.readinto(container)

    def find(self, sub, start=None, end=None):
        d = self.read()
        return d.find(sub, start, end)
