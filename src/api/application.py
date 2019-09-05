from flask import Flask, escape, request, Response, make_response, jsonify, json, g
from flask_expects_json import expects_json

from randomizer.iogr_rom import Randomizer, generate_filename
from randomizer.errors import FileNotFoundError
from randomizer.models.randomizer_data import RandomizerData

from .exceptions.exceptions import InvalidRequestParameters
from .requests.generate_seed_request import GenerateSeedRequest
from .config import ROM_PATH

app = Flask(__name__)


@app.errorhandler(400)
def bad_request(errors):
    return make_response(jsonify({'errors': errors.description}), 400)


@app.route("/v1/seed/generate", methods=["POST"])
@expects_json(GenerateSeedRequest.schema)
def generateSeed() -> Response:
    try:

        rom_path = "C:\\Users\\Bryon\\Documents\\Illusion of Gaia.sfc"

        request_data = GenerateSeedRequest(request.get_json())
        settings = RandomizerData(request_data.seed, request_data.difficulty, request_data.goal,
                                  request_data.logic, request_data.statues, request_data.enemizer, request_data.start_location,
                                  request_data.firebird, request_data.ohko)

        rom_filename = generate_filename(settings, "sfc")
        spoiler_filename = generate_filename(settings, "json")

        randomizer = Randomizer(rom_filename, rom_path, settings)

        patch = randomizer.generate_rom()
        # spoiler = randomizer.generate_spoiler()

        return make_response(patch, 200)
    except InvalidRequestParameters as e:
        return make_response(e.message, e.status_code)
    except FileNotFoundError:
        return make_response(404)


if __name__ == '__main__':
    app.run(debug=True)
