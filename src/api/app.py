# pylint: disable=import-error
from flask import Flask, escape, request, make_response, jsonify, json, g
from flask_expects_json import expects_json

from randomizer.iogr_rom import Randomizer
from randomizer.errors import FileNotFoundError
from randomizer.models.randomizer_data import RandomizerData

from api.exceptions.exceptions import InvalidRequestParameters
from api.requests.generateSeedRequest import generateSeedRequest

app = Flask(__name__)


@app.errorhandler(400)
def bad_request(errors):
    return make_response(jsonify({'errors': errors.description}), 400)


@app.route("/v1/seed/generate", methods=["POST"])
@expects_json(generateSeedRequest.schema)
def generateSeed():
    try:
        request_data = generateSeedRequest(request.get_json())
        data = RandomizerData(request_data.seed, request_data.difficulty, request_data.goal,
                              request_data.logic, request_data.statues, request_data.enemizer, request_data.start_location,
                              request_data.firebird)

        randomizer = Randomizer(data)
        filename = randomizer.generate_filename()

        return make_response(filename, 200)
    except InvalidRequestParameters as e:
        return make_response(e.message, e.status_code)
    except FileNotFoundError:
        return make_response(404)


if __name__ == '__main__':
    app.run(debug=True)
