from unittest import TestCase
from iogr_rom import generate_filename, VERSION


class FilenameGenerationTests(TestCase):
    def test_GenerateDefaultFilename(self):
        EXPECTED = "IoGR_v" + VERSION + "_Normal_DG4_C_12345.sfc"

        filename = generate_filename(12345, 'Normal', 'Dark Gaia', 'Completable', '4', '', 'South Cape', 'None', False)
        self.assertEqual(filename, EXPECTED)
