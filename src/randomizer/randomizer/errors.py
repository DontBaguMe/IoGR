class FileNotFoundError(Exception):
    """Raised when the ROM does not exist"""
    pass


class OffsetError(Exception):
    """Raised when the ROM offset does not match"""
    pass
