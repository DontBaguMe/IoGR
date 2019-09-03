import json, random
import numbers

from randomizer.models.enums.difficulty import Difficulty
from randomizer.models.enums.goal import Goal
from randomizer.models.enums.logic import Logic
from randomizer.models.enums.enemizer import Enemizer
from randomizer.models.enums.start_location import StartLocation
from randomizer.models.enums.entrance_shuffle import EntranceShuffle

from api.exceptions.exceptions import InvalidRequestParameters

class generateSeedRequest(object):
    schema = {
        'type': 'object',
        'properties': {
            'seed': {'type': 'number'},
            'difficulty': {'type': 'number'},
            'logic': {'type': 'string'},
            'goal': {'type': 'number'},
            'statues': {'type': 'string'},
            'enemizer': {'type':'string'},
            'startLocation': {'type':'string'},
            'allowGlitches': {'type':'boolean'},
            'ohko': {'type':'boolean'},
            'redJewelMadness': {'type':'boolean'},
            'firebird': {'type':'boolean'},
            'bossShuffle': {'type':'boolean'},
            'dungeonShuffle': {'type':'boolean'},
            'overworldShuffle': {'type':'boolean'},
        },
        'required': []
    }

    def __init__(self, payload):
        self._validateSeed(payload)
        self._validateDifficulty(payload)
        self._validateGoal(payload)
        self._validateLogic(payload)
        self._validateEnemizer(payload)
        self._validateStartLocation(payload)
        self._validateEntranceShuffle(payload)
        self._validateSwitches(payload)

#region Validation Methods
    def _validateSeed(self, payload):
        seed = payload.get("seed")

        if isinstance(seed, numbers.Number) and seed > 0:
            self.seed = seed
        else:
            self.seed = random.randrange(0, 9999999)

    def _validateDifficulty(self, payload):
        difficulty = payload.get("difficulty")
        
        try:
            self.difficulty = Difficulty(difficulty)
        except:
            self.difficulty = Difficulty.NORMAL

    def _validateGoal(self, payload):
        goal = payload.get("goal")
        try:
            self.goal = Goal(goal)
        except:
            self.goal = Goal.DARK_GAIA

        if self.goal == Goal.DARK_GAIA:
            self._validateStatues(payload)

    def _validateStatues(self, payload):
        statues = payload.get("statues")

        if statues is not None:
            if statues == "random":
                self.statues = random.randrange(0, 6)
            else:
                count = int(statues)
                if count >= 0 and count <= 6:
                    self.statues = count
                else:
                    self.statues = 4
        else:
            self.statues = 4

    def _validateLogic(self, payload):
        logic = payload.get("logic")

        try:
            self.logic = Logic(logic)
        except:
            self.logic = Logic.COMPLETABLE

    def _validateEnemizer(self, payload):
        enemizer = payload.get("enemizer")

        try:
            self.enemizer = Enemizer(enemizer)
        except:
            self.enemizer = Enemizer.NONE

    def _validateStartLocation(self, payload):
        start_location = payload.get("startLocation")

        try:
            self.start_location = StartLocation(start_location)
        except:
            self.start_location = StartLocation.SOUTH_CAPE

    def _validateEntranceShuffle(self, payload):
        entrance_shuffle = payload.get("entranceShuffle")

        try:
            self.entrance_shuffle = EntranceShuffle(entrance_shuffle)
        except:
            self.entrance_shuffle = EntranceShuffle.NONE

    def _validateSwitches(self, payload):
        def getSwitch(switch):
            if switch is None:
                return False
            return switch

        self.allow_glitches = getSwitch(payload.get("allowGlitches"))
        self.ohko = getSwitch(payload.get("ohko"))
        self.red_jewel_madness = getSwitch(payload.get("redJewelMadness"))
        self.firebird = getSwitch(payload.get("firebird"))
        self.boss_shuffle = getSwitch(payload.get("bossShuffle"))     
        self.dungeon_shuffle = getSwitch(payload.get("dungeonShuffle"))
        self.overworld_shuffle = getSwitch(payload.get("overworldShuffle"))

        if self.red_jewel_madness and self.ohko:
            raise InvalidRequestParameters("Can't have OHKO and Red Jewel Madness both flagged")

#endregion

    def to_json(self):
        return json.dumps(self.__dict__)
