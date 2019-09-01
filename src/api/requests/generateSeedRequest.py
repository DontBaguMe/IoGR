import json, random
import numbers

from randomizer.models.enums.difficulty import Difficulty
from randomizer.models.enums.goal import Goal
from randomizer.models.enums.logic import Logic
from randomizer.models.enums.enemizer import Enemizer
from randomizer.models.enums.start_location import StartLocation
from randomizer.models.enums.entrance_shuffle import EntranceShuffle

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
        switch = {
            0: "0",
            1: "1",
            2: "2",
            3: "3",
            4: "4",
            5: "5",
            6: "6",
            7: "random",
        }

        if statues is not None:
            self.statues = switch.get(statues.lower(), "Random")
        else:
            self.statues = "4"

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
        self.allow_glitches = payload.get("allowGlitches")
        if self.allow_glitches is None: self.allow_glitches = False

        self.ohko = payload.get("ohko")
        if self.ohko is None: self.ohko = False

        self.red_jewel_madness = payload.get("redJewelMadness")
        if self.red_jewel_madness is None: self.red_jewel_madness = False

        self.firebird = payload.get("firebird")
        if self.firebird is None: self.firebird = False

        self.boss_shuffle = payload.get("bossShuffle")
        if self.boss_shuffle is None: self.boss_shuffle = False
            
        self.dungeon_shuffle = payload.get("dungeonShuffle")
        if self.dungeon_shuffle is None: self.dungeon_shuffle = False

        self.overworld_shuffle = payload.get("overworldShuffle")
        if self.overworld_shuffle is None: self.overworld_shuffle = False

    
#endregion

    def to_json(self):
        return json.dumps(self.__dict__)
