from datetime import datetime
import binascii
import random
import quintet_text

MAX_INVENTORY = 15
PROGRESS_ADJ = [1.5, 1.25, 1, 1]   # Required items are more likely to be placed in easier modes
MAX_CYCLES = 100
INACCESSIBLE = 100

class World:
    # Assigns item to location
    def fill_item(self,item,location=-1):
        if location == -1:
            return False
        elif self.item_locations[location][2]:
            return False

        self.item_pool[item][0] -= 1
        self.item_locations[location][2] = True
        self.item_locations[location][3] = item

        self.placement_log.append([item,location])

        return True

    # Removes an assigned item and returns it to item pool
    def unfill_item(self,location=-1):
        if location == -1:
            return 0
        elif not self.item_locations[location][2]:
            return 0

        item = self.item_locations[location][3]
        self.item_locations[location][2] = False
        self.item_pool[item][0] += 1

        for x in self.placement_log:
            if x[1] == location:
                self.placement_log.remove(x)

        return item

    # Find and clear non-progression item to make room for progression item
    def make_room(self,item_locations,inv=False,count=1):
        unfilled = []
        while count > 0:
            i = 0
            done = False
            while not done:
                loc = item_locations[i]
                region = self.item_locations[loc][0]
                type = self.item_locations[loc][1]

                if type == 1 and self.item_locations[loc][2]:
                    item = self.item_locations[loc][3]
                    if inv and not self.graph[region][0] and self.item_pool[item][4]:
                        done = True
                    elif not inv and self.graph[region][0] and self.item_pool[item][5] != 1:
                        done = True

                if done:
                    self.unfill_item(loc)
                    unfilled.append(loc)

                i += 1
                if i >= len(item_locations):
                    return []
            count -= 1

        return unfilled

    # Converts item pool into list of unique items, returns list
    def list_item_pool(self,type=0,items=[],progress_type=0):
        item_list = []
        for x in self.item_pool:
            if not items or x in items:
                if type == 0 or type == self.item_pool[x][1]:
                    if progress_type == 0 or progress_type == self.item_pool[x][5]:
                        i = 0
                        while i < self.item_pool[x][0]:
                            item_list.append(x)
                            i += 1
        return item_list

    # Returns a list of unfilled item locations
    def list_item_locations(self):
        locations = []
        for x in self.item_locations:
            locations.append(x)
        return locations

    # Returns list of graph edges
    def list_logic(self):
        edges = []
        for x in self.logic:
            edges.append(x)
        return edges

    # Checks if one list is contained inside another list
    def is_sublist(self,list,sublist):
        if sublist == []:
            return True
        elif sublist == list:
            return True
        elif len(sublist) > len(list):
            return False

        l = list[:]

        for x in sublist:
            if x in l:
                l.remove(x)
            else:
                return False

        return True

    # Returns lists of accessible item, ability, and statue locations
    def open_locations(self):
        # Accessible open location for items, abilities, and Mystic Statues
        locations = [[],[],[]]
        for x in self.item_locations:
            region = self.item_locations[x][0]
            type = self.item_locations[x][1]
            if self.graph[region][0] and not self.item_locations[x][2]:
                locations[type-1].append(x)
        return locations

    # Zeroes out accessible flags for all world regions
    def unsolve(self):
        for x in self.graph:
            self.graph[x][0]=False

    # Finds all accessible locations and returns all accessible items
    def traverse(self,start_items=[]):
        #print "Traverse:"
        self.unsolve()
        to_visit = [-1]
        items = start_items[:]
        while to_visit:
            origin = to_visit.pop(0)
            #print "Visiting ",origin

            if not self.graph[origin][0]:
                self.graph[origin][0] = True
                for x in self.graph[origin][1]:
                    if x not in to_visit:
                        to_visit.append(x)
                found_item = False
                for location in self.item_locations:
                    if self.item_locations[location][0] == origin and self.item_locations[location][2]:
                        items.append(self.item_locations[location][3])
                        found_item = True
                        #print "Found item in location: ", self.item_locations[location][3], location
                if found_item:
                    #print "We found an item"
                    for y in self.graph:
                        if self.graph[y][0] and y != origin:
                            to_visit.append(y)

            for edge in self.logic:
                if self.logic[edge][0] == origin:
                    dest = self.logic[edge][1]
                    if not self.graph[dest][0] and dest not in to_visit:
                        req_items = []
                        for req in self.logic[edge][2]:
                            i = 0
                            while i < req[1]:
                                req_items.append(req[0])
                                i += 1
                        if self.is_sublist(items,req_items):
                            to_visit.append(dest)

        return items

    # Returns full list of accessible locations
    def accessible_locations(self,item_locations):
        accessible = []
        for x in item_locations:
            region = self.item_locations[x][0]
            if self.graph[region][0]:
                accessible.append(x)
        return accessible

    # Returns full list of unaccessible locations
    def unaccessible_locations(self,item_locations):
        unaccessible = []
        for x in item_locations:
            region = self.item_locations[x][0]
            if not self.graph[region][0]:
                unaccessible.append(x)
        return unaccessible

    # Fill a list of items randomly in a list of locations
    def random_fill(self,items=[],item_locations=[],accessible=True):
        if not items:
            return True
        elif not item_locations:
            return False

        to_place = items[:]
        to_fill = item_locations[:]

        while to_place:
            item = to_place.pop(0)
            item_type = self.item_pool[item][1]

            placed = False
            i = 0
            for dest in to_fill:
                if not placed:
                    region = self.item_locations[dest][0]
                    location_type = self.item_locations[dest][1]
                    filled = self.item_locations[dest][2]
                    restrictions = self.item_locations[dest][4]
                    if not filled and item_type == location_type and item not in restrictions:
                        if not accessible or region != INACCESSIBLE:
                            if self.fill_item(item,dest):
                                to_fill.remove(dest)
                                placed = True

        return True

    # Place list of items into random accessible locations
    def forward_fill(self,items=[],item_locations=[]):
        if not items:
            return True
        elif not item_locations:
            return False

        to_place = items[:]
        to_fill = item_locations[:]

        item = to_place.pop(0)
        item_type = self.item_pool[item][1]

        for dest in to_fill:
            region = self.item_locations[dest][0]
            location_type = self.item_locations[dest][1]
            filled = self.item_locations[dest][2]
            restrictions = self.item_locations[dest][4]
            if self.graph[region][0] and not filled and self.item_pool[item][0] > 0:
                if item_type == location_type and item not in restrictions:
                    #print "Placing item: ", item, dest
                    if self.fill_item(item,dest):
                        to_fill_new = to_fill[:]
                        to_fill_new.remove(dest)
                        if self.forward_fill(to_place,to_fill_new):
                            #print "Filled ",dest," with ",item
                            #self.placement_log.append([item,dest])
                            return True
                        else:
                            item = self.unfill_item(dest)

        return False

    # Convert a prerequisite to a list of items needed to fulfill it
    def items_needed(self,prereq=[],items=[]):
        if not prereq:
            return []
        elif not items:
            return prereq

        prereq_new = prereq[:]
        items_new = items[:]

        for x in prereq:
            if x in items_new:
                prereq_new.remove(x)
                items_new.remove(x)

        return prereq_new

    # Returns list of item combinations that grant progression
    def progression_list(self,start_items=[]):
        open_locations = self.open_locations()
        open_items = len(open_locations[0])
        open_abilities = len(open_locations[1])

        item_pool = self.list_item_pool(1)
        ability_pool = self.list_item_pool(2)
        all_items = item_pool + ability_pool

        prereq_list = []

        for x in self.logic:
            origin = self.logic[x][0]
            dest = self.logic[x][1]
            if self.graph[origin][0] and not self.graph[dest][0]:
                prereq = []
                for req in self.logic[x][2]:
                    item = req[0]
                    i = 0
                    while i < req[1]:
                        prereq.append(item)
                        i += 1
                prereq = self.items_needed(prereq,start_items)

                item_prereqs = 0
                ability_prereqs = 0
                for y in prereq:
                    if self.item_pool[y][1] == 1:
                        item_prereqs += 1
                    elif self.item_pool[y][1] == 2:
                        ability_prereqs += 1

                if prereq and self.is_sublist(all_items,prereq) and prereq not in prereq_list:
                    if item_prereqs <= open_items and ability_prereqs <= open_abilities:
                        self.graph[dest][0] = True
                        start_items_temp = start_items[:] + prereq
                        #for req in prereq:
                        #    if self.item_pool[req][4]:
                        #        start_items_temp.append(req)
                        inv_temp = self.get_inventory(start_items_temp)
                        #neg_inv_temp = negative_inventory[:]

                        #for item in inv_temp:
                        #    if item in neg_inv_temp:
                        #        inv_temp.remove(item)
                        #        neg_inv_temp.remove(item)
                        if len(inv_temp) <= MAX_INVENTORY:
                            prereq_list.append(prereq)
                        else:
                            prereq_list.append(-1)
                        self.graph[dest][0] = False

        if not prereq_list:
            return -1
        else:
            while -1 in prereq_list:
                prereq_list.remove(-1)
            if not prereq_list:
                return -2
            else:
                return prereq_list

    # Converts a progression list into a normalized Monte Carlo distribution
    def monte_carlo(self,progression=[],start_items=[]):
        if not progression:
            return []

        open_locations = self.open_locations()
        open_items = len(open_locations[0])
        open_abilities = len(open_locations[1])

        items = self.list_item_pool(1)
        abilities = self.list_item_pool(2)
        all_items = items + abilities
        sum_items = len(items)
        sum_abilities = len(abilities)

        probability = []

        monte_carlo = []
        sum_prob = 0
        sum_edges = 0

        probabilities = []

        while progression:
            current_prereq = progression.pop(0)
            prereqs = current_prereq[:]
            probability = 1.0
            i = 0
            j = 0
            while prereqs:
                item = prereqs.pop(0)
                if item in all_items:
                    if self.item_pool[item][1] == 1:
                        probability *= float(self.item_pool[item][0]) / float((sum_items - i))
                        i += 1
                    elif self.item_pool[item][1] == 2:
                        probability *= float(self.item_pool[item][0]) / float((sum_abilities - j))
                        j += 1
                    if item in self.required_items:
                        probability *= PROGRESS_ADJ[self.mode]
            probabilities.append([probability,current_prereq])
            sum_prob += probability
            sum_edges += 1

        prob_adj = 100.0 / sum_prob
        rolling_sum = 0
        for x in probabilities:
            x[0] = x[0]*prob_adj + rolling_sum
            rolling_sum = x[0]

        #print probabilities
        return probabilities

    # Returns a list of map lists, by boss
    def get_maps(self):
        maps = [[],[],[],[],[],[],[]]
        for map in self.maps:
            boss = self.maps[map][1]
            maps[boss].append(map)

        maps.pop(0)
        return maps

    # Randomize map-clearing rewards
    def map_rewards(self):
        maps = self.get_maps()
        #print maps

        for area in maps:
            random.shuffle(area)

        boss_rewards = 4 - self.mode

        rewards = []              # Total rewards by mode (HP/STR/DEF)
        if self.mode == 0:             # Easy: 10/7/7
            rewards += [1] * 10
            rewards += [2] * 7
            rewards += [3] * 7
        elif self.mode == 1:           # Normal: 10/4/4
            rewards += [1] * 10
            rewards += [2] * 4
            rewards += [3] * 4
        elif self.mode == 2:           # Hard: 8/2/2
            rewards += [1] * 8
            rewards += [2] * 2
            rewards += [3] * 2
        elif self.mode == 3:           # Extreme: 6/0/0
            rewards += [1] * 6

        random.shuffle(rewards)

        # Add in rewards, where applicable, by difficulty
        for area in maps:
            i = 0
            while i < boss_rewards:
                map = area[i]
                reward = rewards.pop(0)
                if self.variant != "OHKO" or reward > 1:  # No HP rewards for OHKO
                    self.maps[map][2] = reward
                i += 1

    # Place Mystic Statues in World
    def fill_statues(self,locations=[148,149,150,151,152,153]):
        return self.random_fill([54,55,56,57,58,59],locations)

    def lock_dark_spaces(self,item_locations=[]):
        for set in self.dark_space_sets:
            ds = -1
            for location in item_locations:
                if location in set:
                    ds = location
            if ds == -1:
                return False
            else:
                self.item_locations[ds][2] = True
        return True

    # Initialize World parameters
    def initialize(self):
        # Manage required items
        if 1 in self.statues:
            self.required_items += [3,4,7,8]
        if 2 in self.statues:
            self.required_items += [14]
        if 3 in self.statues:
            self.required_items += [18,19]
        if 4 in self.statues:
            self.required_items += [50,51]
        if 5 in self.statues:
            self.required_items += [38,30,31,32,33,34,35]
        if 6 in self.statues:
            self.required_items += [39]

        if self.kara == 1:
            self.required_items += [2,9,23]
        elif self.kara == 2:
            self.required_items += [11,12,15]
        elif self.kara == 3:
            self.required_items += [49]
        elif self.kara == 4:
            self.required_items += [26,50]
        elif self.kara == 5:
            self.required_items += [28,50,53]

        # Update inventory space logic
        if 3 in self.statues:
            self.item_pool[19][4] = True
        if 5 in self.statues:
            self.item_pool[30][4] = True
            self.item_pool[31][4] = True
            self.item_pool[32][4] = True
            self.item_pool[33][4] = True
            self.item_pool[34][4] = True
            self.item_pool[35][4] = True
            self.item_pool[38][4] = True

        # Random start location
        if self.start_mode != "South Cape":
            self.start_loc = self.random_start()
            self.graph[-1][1] = [self.item_locations[self.start_loc][0]]

        # Chaos mode
        if self.logic_mode == "Chaos":
            # Add "Inaccessible" node to graph
            self.graph[INACCESSIBLE] = [False,[],"Inaccessible",[]]

            # Towns can have Freedan abilities
            for x in [10,14,22,39,57,66,77,88,103,114,129,145,146]:
                for y in [51,52,53]:
                    self.item_locations[x][4].remove(y)

            # Several locked Dark Spaces can have abilities
            ds_unlock = [74,94,124,142]

            if 1 not in self.statues:   # First DS in Inca
                ds_unlock.append(29)
            if 4 in self.statues:
                self.dark_space_sets.append([93,94])
            if self.kara != 1:          # DS in Underground Tunnel
                ds_unlock.append(19)
            if self.kara != 5:          # DS in Ankor Wat garden
                ds_unlock.append(122)

            for x in ds_unlock:
                self.item_locations[x][2] = False

        # Change graph logic depending on Kara's location
        if self.kara == 1:
            self.logic[150][2][0][1] = 1
            self.graph[10][3].append(20)
        elif self.kara == 2:
            self.logic[151][2][0][1] = 1
            self.graph[26][3].append(20)
            # Change "Sam" to "Samlet"
            self.location_text[45] = "\x63\x80\x8c\x8b\x84\xa4"
        elif self.kara == 3:
            self.logic[152][2][0][1] = 1
            self.graph[43][3].append(20)
        elif self.kara == 4:
            self.logic[153][2][0][1] = 1
            self.graph[53][3].append(20)
        elif self.kara == 5:
            self.logic[154][2][0][1] = 1
            self.graph[60][3].append(20)

        # Change logic based on which statues are required
        for x in self.statues:
            self.logic[155][2][x][1] = 1

#        print self.start_loc
#        for x in self.graph:
#            print x, self.graph[x]
#        for y in self.logic:
#            print y, self.logic[y]


    # Update item placement logic after abilities are placed
    def check_logic(self):
        abilities = [48,49,50,51,52,53]
        inaccessible = []

        # Check for abilities in critical Dark Spaces
        if self.item_locations[19][3] in abilities:         # Underground Tunnel
            inaccessible += [17,18]
        if self.item_locations[29][3] in abilities:         # Inca Ruins
            inaccessible += [26,27,30,31,32]
            self.graph[18][1].remove(19)
        if (self.item_locations[46][3] in abilities and     # Diamond Mine
            self.item_locations[47][3] in abilities and
            self.item_locations[48][3] in abilities):
            del logic[73]
        if (self.item_locations[58][3] in abilities and     # Sky Garden
            self.item_locations[59][3] in abilities and
            self.item_locations[60][3] in abilities):
            del logic[77]
        if self.item_locations[94][3] in abilities:         # Great Wall
            self.graph[200] = [False,[],"Great Wall - Behind Slider or Spin",[]]
            self.logic[200] = [45,200,[[49,1]]]
            self.logic[201] = [45,200,[[50,1]]]
            self.item_locations[93][0] = 200
            if self.item_locations[93][3] in abilities:
                inaccessible += [95]
        if self.item_locations[122][3] in abilities:        # Ankor Wat
            inaccessible += [117,118,119,120,121]
#        if self.item_locations[142][3] in abilities:        # Pyramid
#            inaccessible += [133,134,136,139,140]

        # Change graph node for inaccessible locations
        for x in inaccessible:
            self.item_locations[x][0] = INACCESSIBLE

    # Simulate inventory
    def get_inventory(self,start_items=[]):
        inventory = []
        for item in start_items:
            if self.item_pool[item][4]:
                inventory.append(item)

        negative_inventory = []
        for node in self.graph:
            if self.graph[node][0]:
                negative_inventory += self.graph[node][3]

        i = 0
        while i < len(inventory):
            item = inventory[i]
            if inventory[i] in negative_inventory:
                inventory.remove(item)
                negative_inventory.remove(item)
            else:
                i += 1

        return inventory

    # Takes a random seed and builds out a randomized world
    def randomize(self,seed_adj=0):
        self.initialize()

        solved = False

        random.seed(self.seed + seed_adj)

        # Assign map rewards
        self.map_rewards()

        # Initialize and shuffle location list
        item_locations = self.list_item_locations()
        random.shuffle(item_locations)

        # Fill the Mustic Statues
        self.fill_statues()
        if not self.lock_dark_spaces(item_locations):
            print "ERROR: Couldn't lock dark spaces"
            return False

        # Randomly place non-progression items and abilities
        non_prog_items = self.list_item_pool(0,[],2)
        non_prog_items += self.list_item_pool(0,[],3)

        # For Easy mode
        if self.logic_mode == "Chaos" or self.mode > 2:
            non_prog_items += self.list_item_pool(2)
        elif self.mode == 0:
            non_prog_items += [52]
        elif self.mode == 1:
            non_prog_items += [49,50,52,53]

        random.shuffle(non_prog_items)
        self.random_fill(non_prog_items,item_locations)

        # Check if ability placement affects logic
        self.check_logic()

        # List and shuffle remaining key items
        item_list = self.list_item_pool()
        random.shuffle(item_list)

        inventory = []

        # Forward fill progression items with Monte Carlo simulation method
        # Continue to place progression items until all locations are accessible
        done = False
        goal = False
        cycle = 0

        #while self.unaccessible_locations(item_locations):
        while not done:
            cycle += 1
            if cycle > MAX_CYCLES:
                print "ERROR: Max cycles exceeded"
                return False

            start_items = self.traverse()
            #print "We found these: ",start_items

            inv_size = len(self.get_inventory(start_items))
            if inv_size > MAX_INVENTORY:
                goal = False
                print "ERROR: Inventory capacity exceeded"
            else:
                goal = ((self.goal == "Dark Gaia" and self.graph[70][0]) or
                    (self.goal == "Red Jewel Hunt" and self.graph[68][0]))

            # Get list of new progression options
            progression_list = self.progression_list(start_items)

            done = goal and (self.logic_mode != "Completable" or progression_list == -1)
            #print done, progression_list

            if not done and progression_list == -1:       # No empty locations available
                removed = self.make_room(item_locations)
                if not removed:
                    print "ERROR: Could not remove non-progression item"
                    return False
                progression_list = []
            elif not done and progression_list == -2:     # All new locations have too many inventory items
                removed = self.make_room(item_locations,True)
                if not removed:
                    print "ERROR: Could not remove inventory item"
                    return False
                progression_list = []

            #print "To progress: ",progression_list

#            if not done and not progression_list:
#                #print "Gotta make room..."
#                removed = self.make_room(item_locations,inv_full)
#                if not removed:
#                    print "ERROR: Could not remove non-progression item"
#                    return False
#                #print "Cleared this location: ", removed

            if not done and progression_list:
                # Determine next progression items to add to accessible locations
                progression_mc = self.monte_carlo(progression_list)
                progress = False
                while not progress:
                    key = random.uniform(0,100)
                    #print key
                    items = []
                    for x in progression_mc:
                        if key <= x[0] and not items:
                            items = x[1]

                    if not items:
                        print "What happened?"
                        #done = True
                    elif self.forward_fill(items,item_locations):
                        progress = True
                        #print "We made progress!",items
                        #print self.graph

            #print goal, done

        #print "Unaccessible: ",self.unaccessible_locations(item_locations)
#        for node in self.graph:
#            if not self.graph[node][0]:
#                print "Can't reach ",self.graph[node][2]

        junk_items = self.list_item_pool()
        self.random_fill(junk_items,item_locations,False)

        placement_log = self.placement_log[:]
        random.shuffle(placement_log)
        self.in_game_spoilers(placement_log)

        #print cycle

        return True

    # Prepares dataset to give in-game spoilers
    def in_game_spoilers(self,placement_log=[]):
        for x in placement_log:
            item = x[0]
            location = x[1]

            if location not in self.free_locations:
                if item in self.required_items or item in self.good_items or location in self.trolly_locations:
                    spoiler_str = "\xd3" + self.location_text[location] + "\xac\x87\x80\xa3\xcb"
                    spoiler_str += self.item_text_short[item] + "\xc0"
                    # No in-game spoilers in Extreme mode
                    if self.mode == 3:
                        spoiler_str = "\xd3\x8d\x88\x82\x84\xac\xa4\xa2\xa9\xac\x83\x8e\x83\x8e\x8d\x86\x8e\x4f\xc0"
                    self.spoilers.append(spoiler_str)
                    #print item, location

    # Prints item and ability locations
    def generate_spoiler(self,folder="",version="",filename="IoGR_spoiler"):
        if folder == "":
            print "ERROR: No Folder Specified"
            return

        if self.mode == 0:
            mode_txt = "Easy"
        elif self.mode == 1:
            mode_txt = "Normal"
        elif self.mode == 2:
            mode_txt = "Hard"
        elif self.mode == 3:
            mode_txt = "Extreme"

        if self.kara == 1:
            kara_txt = "Edward's Castle"
        elif self.kara == 2:
            kara_txt = "Diamond Mine"
        elif self.kara == 3:
            kara_txt = "Angel Dungeon"
        elif self.kara == 4:
            kara_txt = "Mt. Kress"
        elif self.kara == 5:
            kara_txt = "Ankor Wat"

        f = open(folder + filename + ".txt", "w+")

        f.write("Illusion of Gaia Randomizer - " + version + "\r\n")
        f.write("Seed generated " + str(datetime.today()) + "\r\n")

        f.write("\r\n")
        f.write("Seed                                  >  " + str(self.seed) + "\r\n")
        f.write("Goal                                  >  " + str(self.goal) + "\r\n")
        f.write("Logic                                 >  " + str(self.logic_mode) + "\r\n")
        f.write("Difficulty                            >  " + mode_txt + "\r\n")
        f.write("\r\n")

        f.write("Statues Required                      >  " + str(self.statues) + "\r\n")
        f.write("Kara Location                         >  " + kara_txt + "\r\n")
        f.write("Jeweler Reward Amounts                >  " + str(self.gem) + "\r\n")
        f.write("Inca Tile (column, row)               >  " + str(self.incatile) + "\r\n")
        f.write("Hieroglyph Order                      >  " + str(self.hieroglyphs) + "\r\n")
        f.write("\r\n")

        for x in self.item_locations:
            item = self.item_locations[x][3]
            location_name = self.item_locations[x][9]
            item_name = self.item_pool[item][3]
            f.write(location_name + "  >  " + item_name + "\r\n")

    def print_enemy_locations(self,filepath,offset=0):
        f = open(filepath,"r+b")
        rom = f.read()
        for enemy in self.enemies:
            print self.enemies[enemy][3]
            done = False
            addr = int("c8200",16) + offset
            while not done:
                addr = rom.find(self.enemies[enemy][1],addr+1)
                if addr < 0 or addr > int("ce5e4",16)+offset:
                    done = True
                else:
                    f.seek(addr)
                    #f.write("\x55\x87\x8a\x05")
                    print " ", addr, hex(addr), binascii.hexlify(f.read(4))
        f.close

    # Prints item and ability locations
    def print_spoiler(self):
        if self.kara == 1:
            kara_txt = "Edward's Castle"
        elif self.kara == 2:
            kara_txt = "Diamond Mine"
        elif self.kara == 3:
            kara_txt = "Angel Dungeon"
        elif self.kara == 4:
            kara_txt = "Mt. Kress"
        elif self.kara == 5:
            kara_txt = "Ankor Wat"

        print ""
        print "Seed                                   >  ", self.seed
        print "Statues Required                       >  ", self.statues
        print "Kara Location                          >  ", kara_txt
        print "Jeweler Reward Amounts                 >  ", self.gem
        print "Inca Tile (column, row)                >  ", self.incatile
        print "Hieroglyph Order                       >  ", self.hieroglyphs
        print ""

        for x in self.item_locations:
            item = self.item_locations[x][3]
            location_name = self.item_locations[x][9]
            item_name = self.item_pool[item][3]
            print location_name,"  >  ",item_name


    # Modifies game ROM to reflect the current state of the World
    def write_to_rom(self,f,rom_offset=0):
        # Room-clearing rewards
        for map in self.maps:
            reward = self.maps[map][2]
            if reward > 0:
                f.seek(int("1aade",16) + map + rom_offset)
                if reward == 1:
                    f.write("\x01")
                elif reward == 2:
                    f.write("\x02")
                elif reward == 3:
                    f.write("\x03")

        # Items and abilities
        for x in self.item_locations:
            type = self.item_locations[x][1]

            # Write items to ROM
            if type == 1:
                item = self.item_locations[x][3]
                #print "Writing item ", item
                item_addr = self.item_locations[x][5]
                item_code = self.item_pool[item][2]
                text1_addr = self.item_locations[x][6]
                text2_addr = self.item_locations[x][7]
                text3_addr = self.item_locations[x][8]
                text_long = self.item_text_long[item]
                text_short = self.item_text_short[item]

                # Write item code to memory
                if item_code:
                    f.seek(int(item_addr,16)+rom_offset)
                    f.write(item_code)

                # Write item text, if appropriate
                if text1_addr:
                    f.seek(int(text1_addr,16)+rom_offset)
                    f.write(text_long)
                    #f.write("\xd3")
                    #f.write(text_short)
                    f.write("\xc0")

                # Write "inventory full" item text, if appropriate
                if text2_addr:
                    f.seek(int(text2_addr,16)+rom_offset)
                    #f.write("\xd3")
                    #f.write(text_short)
                    f.write(text_long)
                    f.write("\xcb\x45\x65\x4b\x4b\x4f\xc0") # Just says "FULL!"

                # Write jeweler inventory text, if apprpriate
                if text3_addr:
                    f.seek(int(text3_addr,16)+rom_offset)
                    f.write(text_short)

            # Write abilities to ROM
            elif type == 2:               # Check if filled
                ability = self.item_locations[x][3]
                ability_addr = self.item_locations[x][5]
                map = self.item_locations[x][8]

                # Change Dark Space type in event table
                if ability in [48,49,50,51,52,53]:
                    f.seek(int(ability_addr,16)+rom_offset)
                    f.write("\x05")

                # Update ability text table
                if ability == 48:                     # Psycho Dash
                    #f.seek(int("8eb5a",16)+2*i+rom_offset)
                    f.seek(int("8eb5a",16)+rom_offset)
                    f.write(map)
                if ability == 49:                     # Psycho Slide
                    f.seek(int("8eb5c",16)+rom_offset)
                    f.write(map)
                if ability == 50:                     # Spin Dash
                    f.seek(int("8eb5e",16)+rom_offset)
                    f.write(map)
                if ability == 51:                     # Dark Friar
                    f.seek(int("8eb60",16)+rom_offset)
                    f.write(map)
                if ability == 52:                     # Aura Barrier
                    f.seek(int("8eb62",16)+rom_offset)
                    f.write(map)
                if ability == 53:                     # Earthquaker
                    f.seek(int("8eb64",16)+rom_offset)
                    f.write(map)

        # Special code for 2-item event in Dao
        item1 = self.item_locations[125][3]
        item2 = self.item_locations[126][3]
        f.seek(int("8fde0",16)+rom_offset)
        f.write("\xd3" + self.item_text_short[item1] + "\xcb")
        f.write(self.item_text_short[item2] + "\xcf\xce")

        # Write in-game spoilers
        i = 0
        for addr in self.spoiler_addresses:
            f.seek(int(self.spoiler_addresses[addr],16)+rom_offset)
            if i < len(self.spoilers):
                f.write(self.spoilers[i])
                i += 1

        # Enemizer
        if self.enemizer != "None":
            self.enemize(f,rom_offset)
            #self.parse_maps(f,rom_offset)

        # Random start location
        if self.start_mode != "South Cape":
            #print self.start_loc
            map_str = self.item_locations[self.start_loc][8] + self.item_locations[self.start_loc][7]

            # Change game start location
            f.seek(int("be517",16) + rom_offset)
            f.write(map_str)

            # Change Dark Space warp location
            f.seek(int("8dbea",16) + rom_offset)
            f.write(map_str)

            # Change Dark Space warp text
            map_name = self.location_text[self.start_loc]
            f.seek(int("8de1f",16) + rom_offset)
            f.write(map_name + "\x0D\xCB\xAC\x4D\x8E\xCB\xAC\x69\x84\xA3\xCA")

            # Check for additional switches that need to be set
            switch_str = ""
            if self.start_loc == 30:     # Inca ramp can hardlock you
                switch_str = "\x02\xcd\x0c\x01"
            elif self.start_loc == 47:   # Diamond Mine behind fences
                switch_str = "\x02\xcd\x34\x01\x02\xcd\x35\x01\x02\xcd\x36\x01"

            if switch_str:
                f.seek(int("bfdf3",16) + rom_offset)
                f.write(switch_str + "\x02\xe0")

        #print "ROM successfully created"


    # Shuffle enemies in ROM
    def parse_maps(self,f,rom_offset=0):
        f.seek(int("d8000",16) + rom_offset)

        header_lengths = {
            "\x02": 1,
            "\x03": 7,
            "\x04": 6,
            "\x05": 7,
            "\x06": 4,
            "\x0e": 3,
            "\x10": 6,
            "\x11": 5,
            "\x13": 2,
            "\x14": 1,
            "\x15": 1,
            "\x17": 5
        }

        done = False
        addr = 0
        map_dataset = {}
        anchor_dataset = {}

        while not done:
            map_id = f.read(2)
            print binascii.hexlify(map_id)
            map_headers = []
            anchor_headers = []
            map_done = False
            anchor = False
            while not map_done:
                map_header = f.read(1)
                if map_header == "\x14":
                    anchor = True
                    anchor_id = f.read(1)
                    map_header += anchor_id
                    map_headers.append(map_header)
                    print binascii.hexlify(map_header)
                elif map_header == "\x00":
                    map_done = True
                    print binascii.hexlify(map_header)
                    print ""
                else:
                    header_len = header_lengths[map_header]
                    map_header += f.read(header_len)
                    map_headers.append(map_header)
                    print binascii.hexlify(map_header)
                    if anchor:
                        anchor_headers.append(map_header)

            anchor_dataset[map_id] = map_headers
            if anchor_headers:
                anchor_dataset[anchor_id] = anchor_headers

            if f.tell() >= int("daffe",16)+rom_offset:
                done = True

#        print map_headers
        print anchor_headers


    # Pick random start location
    def random_start(self):
        locations = []
        for loc in self.item_locations:
            if (self.start_mode == "Forced Unsafe" and self.item_locations[loc][6] == "Unsafe") or (
                self.start_mode != "Forced Unsafe" and self.item_locations[loc][6] == "Safe") or (
                self.item_locations[loc][6] == self.start_mode)):
                locations.append(loc)

        if not locations:
            print "ERROR: Something is fishy with start locations"
            return -1
        else:
            #return 93   # TESTING!
            return locations[random.randint(0,len(locations)-1)]

    # Shuffle enemies in ROM
    def enemize(self,f,rom_offset=0):
        f.seek(0)
        rom = f.read()

        #test_enemy = 13                         # TESTING!
        #test_set = self.enemies[test_enemy][0]

        complex_enemies = [4,15,53,62,88,103]  # Draco and Zip Flies can lock the game if too plentiful
        max_complex = 4

        # Get list of enemysets
        enemysets = []
        for set in self.enemysets:
            enemysets.append(set)

        f.seek(0)
        rom = f.read()

        # Shuffle enemy stats in Insane
        if self.enemizer == "Insane":
            insane_enemies = []
            insane_templates = []
            for enemy in self.enemies:
                if self.enemies[enemy][5] and enemy != 102:   # Special exception for Zombies
                    insane_enemies.append(enemy)
                    insane_templates.append(self.enemies[enemy][2])

            random.shuffle(insane_templates)
            insane_dictionary = {}
            i = 0

            for enemy in insane_enemies:
                insane_dictionary[enemy] = insane_templates[i]
                i += 1

        # Randomize enemy spritesets
        for map in self.maps:
            complex_ct = 0
            oldset = self.maps[map][0]
            # Determine new enemyset for map
            if self.enemizer == "Limited":
                sets = [oldset]
            elif not self.maps[map][7]:
                sets = enemysets[:]
            else:
                sets = self.maps[map][7][:]

            random.shuffle(sets)
            newset = sets[0]
            #if 1 in sets:      # TESTING!
            #    newset = 1
            #newset = test_set  # TESTING!

            # Gather enemies from old and new sets
            old_enemies = []
            new_enemies = []
            for enemy in self.enemies:
                if self.enemies[enemy][0] == oldset:
                    old_enemies.append(enemy)
                if self.enemies[enemy][0] == newset and self.enemies[enemy][5]:
                    new_enemies.append(enemy)

            # Update map header to reflect new enemyset
            if self.maps[map][3]:
                addr = rom.find(self.maps[map][3], int("d8000",16) + rom_offset)
                if addr < 0 or addr > int("daffe",16)+rom_offset:
                    print "ERROR: Couldn't find header for map ", map
                else:
                    f.seek(addr + self.maps[map][4])
                    f.write(self.enemysets[newset][0])

            # Randomize each enemy in map
            addr_start = self.maps[map][5]
            addr_end = self.maps[map][6]
            for enemy in old_enemies:
                #print self.enemies[enemy][3]
                done = False
                addr = int(addr_start,16) + rom_offset
                while not done:
                    addr = rom.find(self.enemies[enemy][1] + self.enemies[enemy][2],addr+1)
                    if addr < 0 or addr > int(addr_end,16)+rom_offset:
                        done = True
                    else:
                        # Pick an enemy from new set
                        enemytype = self.enemies[enemy][3]
                        walkable = self.enemies[enemy][4]

                        new_enemies_tmp = new_enemies[:]

                        # Special exception: 4-Ways cannot be on a #$XF x-coord
                        if newset == 1:
                            f.seek(addr-3)
                            xcoord = binascii.hexlify(f.read(1))
                            if xcoord[1] == "f":
                                new_enemies_tmp.remove(13)

                        random.shuffle(new_enemies_tmp)

                        i = 0
                        found_enemy = False

                        #if 13 in new_enemies_tmp:   # TESTING!
                        #    new_enemy = 13
                        #    found_enemy = True

                        while not found_enemy:
                            new_enemy = new_enemies_tmp[i]
                            new_enemytype = self.enemies[new_enemy][3]
                            new_walkable = self.enemies[new_enemy][4]
                            if walkable or new_enemytype == 3 or walkable == new_walkable or i == len(new_enemies_tmp)-1:
                                found_enemy = True
                                # Limit number of complex enemies per map
                                if new_enemy in complex_enemies:
                                    complex_ct += 1
                                    if complex_ct >= max_complex:
                                        for enemy_tmp in new_enemies:
                                            if enemy_tmp in complex_enemies:
                                                new_enemies.remove(enemy_tmp)
                                                i -= 1
                            i += 1
                        f.seek(addr-1)
                        #f.write("\x00" + self.enemies[test_enemy][1] + self.enemies[test_enemy][2])  # TESTING!
                        f.write("\x00" + self.enemies[new_enemy][1])
                        if self.enemizer == "Balanced" and enemy == 102:
                            f.write("\x47")
                        elif map != 27 and self.enemizer != "Balanced":           # Moon Tribe cave enemies retain same template
                            if self.enemizer == "Insane" and new_enemy != 102:  # Again, zombie exception
                                f.write(insane_dictionary[new_enemy])
                            else:
                                f.write(self.enemies[new_enemy][2])

        # Disable all non-enemy sprites
        if self.enemizer != "Limited":
            for sprite in self.nonenemy_sprites:
                f.seek(int(self.nonenemy_sprites[sprite][1],16) + rom_offset + 3)
                f.write("\x02\xe0")


    # Build world
    def __init__(self, seed, mode, goal="Dark Gaia", logic_mode="Completable",statues=[1,2,3,4,5,6],start_mode="South Cape",
        variant="None",enemizer="None",firebird=False,kara=3,gem=[3,5,8,12,20,30,50],incatile=[9,5],hieroglyphs=[1,2,3,4,5,6]):

        self.seed = seed
        self.statues = statues
        self.goal = goal
        self.logic_mode = logic_mode
        self.kara = kara
        self.gem = gem
        self.incatile = incatile
        self.hieroglyphs = hieroglyphs
        self.mode = mode
        self.start_mode = start_mode
        self.start_loc = 10
        self.variant = variant
        self.enemizer = enemizer
        self.firebird = firebird
        self.placement_log = []
        self.spoilers = []
        self.dark_space_sets = [[46,47],[58,60]]
        self.required_items = [20,36]
        self.good_items = [10,13,24,25,49,50,51]
        self.trolly_locations = [32,45,64,65,102,108,121,128,136,147]
        self.free_locations = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,24]

        # Initialize item pool, considers special attacks as "items"
        # Format = { ID:  [Quantity, Type code (1=item, 2=ability, 3=statue),
        #                  ROM Code, Name, TakesInventorySpace,
        #                  ProgressionType (1=unlocks new locations,2=quest item,3=no progression)] }
        self.item_pool = {
            0: [2,1,"\x00","Nothing",False,3],
            1: [45,1,"\x01","Red Jewel",False,1],
            2: [1,1,"\x02","Prison Key",True,1],
            3: [1,1,"\x03","Inca Statue A",True,1],
            4: [1,1,"\x04","Inca Statue B",True,1],
            5: [0,1,"\x05","Inca Melody",True,3],
            6: [12,1,"\x06","Herb",False,3],
            7: [1,1,"\x07","Diamond Block",True,1],
            8: [1,1,"\x08","Wind Melody",True,1],
            9: [1,1,"\x09","Lola's Melody",True,1],
            10: [1,1,"\x0a","Large Roast",True,1],
            11: [1,1,"\x0b","Mine Key A",True,1],
            12: [1,1,"\x0c","Mine Key B",True,1],
            13: [1,1,"\x0d","Memory Melody",True,1],
            14: [4,1,"\x0e","Crystal Ball",True,2],
            15: [1,1,"\x0f","Elevator Key",True,1],
            16: [1,1,"\x10","Mu Palace Key",True,1],
            17: [1,1,"\x11","Purification Stone",True,1],
            18: [2,1,"\x12","Statue of Hope",True,1],
            19: [2,1,"\x13","Rama Statue",False,2],
            20: [1,1,"\x14","Magic Dust",True,2],
            21: [0,1,"\x15","Blue Journal",False,3],
            22: [1,1,"\x16","Lance's Letter",False,3],
            23: [1,1,"\x17","Necklace Stones",True,1],
            24: [1,1,"\x18","Will",True,1],
            25: [1,1,"\x19","Teapot",True,1],
            26: [3,1,"\x1a","Mushroom Drops",True,1],
            27: [0,1,"\x1b","Bag of Gold",False,3],
            28: [1,1,"\x1c","Black Glasses",False,1],
            29: [1,1,"\x1d","Gorgon Flower",True,1],
            30: [1,1,"\x1e","Hieroglyph",False,2],
            31: [1,1,"\x1f","Hieroglyph",False,2],
            32: [1,1,"\x20","Hieroglyph",False,2],
            33: [1,1,"\x21","Hieroglyph",False,2],
            34: [1,1,"\x22","Hieroglyph",False,2],
            35: [1,1,"\x23","Hieroglyph",False,2],
            36: [1,1,"\x24","Aura",True,1],
            37: [1,1,"\x25","Lola's Letter",False,1],
            38: [1,1,"\x26","Father's Journal",False,2],
            39: [1,1,"\x27","Crystal Ring",False,1],
            40: [1,1,"\x28","Apple",True,1],
            41: [3,1,"\x29","HP Jewel",False,3],
            42: [1,1,"\x2a","DEF Jewel",False,3],
            43: [2,1,"\x2b","STR Jewel",False,3],
            44: [1,1,"\x2c","Light Jewel",False,3],
            45: [2,1,"\x2d","Dark Jewel",False,3],
            46: [1,1,"\x2e","2 Red Jewels",False,3],
            47: [1,1,"\x2f","3 Red Jewels",False,3],
            48: [1,2,"","Psycho Dash",False,1],
            49: [1,2,"","Psycho Slider",False,1],
            50: [1,2,"","Spin Dash",False,1],
            51: [1,2,"","Dark Friar",False,1],
            52: [1,2,"","Aura Barrier",False,1],
            53: [1,2,"","Earthquaker",False,1],
            54: [1,3,"","Mystic Statue 1",False,2],
            55: [1,3,"","Mystic Statue 2",False,2],
            56: [1,3,"","Mystic Statue 3",False,2],
            57: [1,3,"","Mystic Statue 4",False,2],
            58: [1,3,"","Mystic Statue 5",False,2],
            59: [1,3,"","Mystic Statue 6",False,2],
            60: [0,2,"","Nothing",False,3]
        }

        # Define Item/Ability/Statue locations
        # Format: { ID: [Region, Type (1=item,2=ability,3=statue), Filled Flag,
        #                Filled Item, Restricted Items, Item Addr, Text Addr, Text2 Addr,
        #                Special (map# or inventory addr), Name, Swapped Flag]}
        #         (For random start, [6]=Type, [7]=XY_spawn_data)
        self.item_locations = {
            0:  [1,1,False,0,[],"8d019","8d19d","","8d260",     "Jeweler Reward 1                    "],
            1:  [2,1,False,0,[],"8d028","8d1ba","","8d274",     "Jeweler Reward 2                    "],
            2:  [3,1,False,0,[],"8d037","8d1d7","","8d288",     "Jeweler Reward 3                    "],
            3:  [4,1,False,0,[],"8d04a","8d1f4","","8d29c",     "Jeweler Reward 4                    "],
            4:  [5,1,False,0,[],"8d059","8d211","","8d2b0",     "Jeweler Reward 5                    "],
            5:  [6,1,False,0,[],"8d069","8d2ea","","8d2c4",     "Jeweler Reward 6                    "],

            6:  [0,1,False,0,[],"F51D","F52D","F543","",        "South Cape: Bell Tower              "],
            7:  [0,1,False,0,[],"4846e","48479","","",          "South Cape: Fisherman               "], #text2 was 0c6a1
            8:  [0,1,False,0,[],"F59D","F5AD","F5C3","",        "South Cape: Lance's House           "],
            9:  [0,1,False,0,[],"499e4","49be5","","",          "South Cape: Lola                    "],
            10: [0,2,False,0,[51,52,53],"c830a","Safe","\xE0\x00\x70\x00\x83\x00\x43","\x01",
                                                                "South Cape: Dark Space              "],

            11: [7,1,False,0,[],"4c214","4c299","","",          "Edward's Castle: Hidden Guard       "],
            12: [7,1,False,0,[],"4d0ef","4d141","","",          "Edward's Castle: Basement           "],

            13: [8,1,False,0,[],"4d32f","4d4b1","","",          "Edward's Prison: Hamlet             "], #text 4d5f4?
            14: [8,2,False,0,[51,52,53],"c8637","","","\x0b",   "Edward's Prison: Dark Space         "],

            15: [9,1,False,0,[2],"1AFA9","","","",              "Underground Tunnel: Spike's Chest   "],
            16: [9,1,False,0,[2],"1AFAE","","","",              "Underground Tunnel: Small Room Chest"],
            17: [10,1,False,0,[2],"1AFB3","","","",             "Underground Tunnel: Ribber's Chest  "],
            18: [10,1,False,0,[],"F61D","F62D","F643","",       "Underground Tunnel: Barrels         "],
            19: [10,2,True,0,[],"c8aa2","Unsafe","\xA0\x00\xD0\x04\x83\x00\x74","\x12",
                                                                "Underground Tunnel: Dark Space      "],   # Always open

            20: [12,1,False,0,[9],"F69D","F6AD","F6C3","",      "Itory Village: Logs                 "],
            21: [13,1,False,0,[9],"4f375","4f38d","4f3a8","",   "Itory Village: Cave                 "],
            22: [12,2,False,0,[51,52,53],"c8b34","Safe","\x30\x04\x90\x00\x83\x00\x35","\x15",
                                                                "Itory Village: Dark Space           "],

            23: [73,1,False,0,[],"4fae1","4faf9","4fb16","",    "Moon Tribe: Cave                    "],

            24: [15,1,False,0,[],"1AFB8","","","",              "Inca Ruins: Diamond-Block Chest     "],
            25: [16,1,False,0,[7],"1AFC2","","","",             "Inca Ruins: Broken Statues Chest    "],
            26: [16,1,False,0,[7],"1AFBD","","","",             "Inca Ruins: Stone Lord Chest        "],
            27: [16,1,False,0,[7],"1AFC6","","","",             "Inca Ruins: Slugger Chest           "],
            28: [16,1,False,0,[7],"9c5bd","9c614","9c637","",   "Inca Ruins: Singing Statue          "],
            29: [16,2,True,0,[],"c9302","Unsafe","\x10\x01\x90\x00\x83\x00\x32","\x28",
                                                                "Inca Ruins: Dark Space 1            "],   # Always open
            30: [16,2,False,0,[],"c923b","Unsafe","\xC0\x01\x50\x01\x83\x00\x32","\x26",
                                                                "Inca Ruins: Dark Space 2            "],
            31: [17,2,False,0,[],"c8db8","","","\x1e",          "Inca Ruins: Final Dark Space        "],

            32: [19,1,False,0,[3,4,7,8],"5965e","5966e","","",  "Gold Ship: Seth                     "],

            33: [20,1,False,0,[],"F71D","F72D","F743","",       "Diamond Coast: Jar                  "],

            34: [21,1,False,0,[],"F79D","F7AD","F7C3","",       "Freejia: Hotel                      "],
            35: [21,1,False,0,[],"5b6d8","5b6e8","","",         "Freejia: Creepy Guy                 "],
            36: [21,1,False,0,[],"5cf9e","5cfae","5cfc4","",    "Freejia: Trash Can 1                "],
            37: [21,1,False,0,[],"5cf3d","5cf49","","",         "Freejia: Trash Can 2                "], #text2 was 5cf5b
            38: [21,1,False,0,[],"5b8b7","5b962","5b9ee","",    "Freejia: Snitch                     "], #text1 was @5b94d
            39: [21,2,False,0,[51,52,53],"c96ce","Safe","\x40\x00\xa0\x00\x83\x00\x11","\x34",
                                                                "Freejia: Dark Space                 "],

            40: [22,1,False,0,[],"1AFD0","","","",              "Diamond Mine: Chest                 "],
            41: [23,1,False,0,[],"5d7e4","5d819","5d830","",    "Diamond Mine: Trapped Laborer       "],
            42: [24,1,False,0,[],"aa777","aa85c","","",         "Diamond Mine: Laborer w/Elevator Key"], #text1 was aa811
            43: [25,1,False,0,[15],"5d4d2","5d4eb","5d506","",  "Diamond Mine: Morgue                "],
            44: [25,1,False,0,[15],"aa757","aa7ef","","",       "Diamond Mine: Laborer w/Mine Key    "], #text1 was aa7b4
            45: [26,1,False,0,[11,12,15],"5d2b0","5d2da","","", "Diamond Mine: Sam                   "],
            46: [22,2,False,0,[],"c9a87","Unsafe","\xb0\x01\x70\x01\x83\x00\x32","\x40",
                                                                "Diamond Mine: Appearing Dark Space  "], # Always open
            47: [22,2,False,0,[],"c98b0","Unsafe","\xd0\x00\xc0\x00\x83\x00\x61","\x3d",
                                                                "Diamond Mine: Dark Space at Wall    "],
            48: [23,2,False,0,[],"c9b49","","","\x42",          "Diamond Mine: Dark Space behind Wall"],

            49: [29,1,False,0,[],"1AFDD","","","",              "Sky Garden: (NE) Platform Chest     "],
            50: [29,1,False,0,[],"1AFD9","","","",              "Sky Garden: (NE) Blue Cyber Chest   "],
            51: [29,1,False,0,[],"1AFD5","","","",              "Sky Garden: (NE) Statue Chest       "],
            52: [30,1,False,0,[],"1AFE2","","","",              "Sky Garden: (SE) Dark Side Chest    "],
            53: [31,1,False,0,[],"1AFE7","","","",              "Sky Garden: (SW) Ramp Chest         "],
            54: [29,1,False,0,[],"1AFEC","","","",              "Sky Garden: (SW) Dark Side Chest    "],
            55: [72,1,False,0,[],"1AFF1","","","",              "Sky Garden: (NW) Top Chest          "],
            56: [72,1,False,0,[],"1AFF5","","","",              "Sky Garden: (NW) Bottom Chest       "],
            57: [29,2,False,0,[51,52,53],"c9d63","Unsafe","\x90\x00\x70\x00\x83\x00\x22","\x4c",
                                                                "Sky Garden: Dark Space (Foyer)      "],
            58: [29,2,False,0,[],"ca505","Unsafe","\x70\x00\xa0\x00\x83\x00\x11","\x56",
                                                                "Sky Garden: Dark Space (SE)         "], #in the room
            59: [29,2,False,0,[],"ca173","","","\x51",          "Sky Garden: Dark Space (SW)         "],
            60: [29,2,False,0,[],"ca422","Unsafe","\x20\x00\x70\x00\x83\x00\x44","\x54",
                                                                "Sky Garden: Dark Space (NW)         "],

            61: [33,1,False,0,[],"1AFFF","","","",              "Seaside Palace: Side Room Chest     "],
            62: [33,1,False,0,[],"1AFFA","","","",              "Seaside Palace: First Area Chest    "],
            63: [33,1,False,0,[],"1B004","","","",              "Seaside Palace: Second Area Chest   "],
            64: [34,1,False,0,[17],"68af7","68ea9","68f02","",  "Seaside Palace: Buffy               "],
            65: [35,1,False,0,[9,23],"6922d","6939e","693b7","","Seaside Palace: Coffin              "], #text1 was 69377
            66: [33,2,False,0,[51,52,53],"ca574","Safe","\xf0\x02\x90\x00\x83\x00\x64","\x5a",
                                                                "Seaside Palace: Dark Space          "],

            67: [37,1,False,0,[],"1B012","","","",              "Mu: Empty Chest 1                   "],
            68: [37,1,False,0,[],"1B01B","","","",              "Mu: Empty Chest 2                   "],
            69: [37,1,False,0,[],"698be","698d2","","",         "Mu: Hope Statue 1                   "],
            70: [39,1,False,0,[],"69966","69975","","",         "Mu: Hope Statue 2                   "],
            71: [40,1,False,0,[18],"1B00D","","","",            "Mu: Chest s/o Hope Room 2           "],
            72: [40,1,False,0,[18],"1B009","","","",            "Mu: Rama Chest N                    "],
            73: [40,1,False,0,[18],"1B016","","","",            "Mu: Rama Chest E                    "],
            74: [38,2,True,0,[],"ca92d","","","\x60",           "Mu: Open Dark Space                 "],   # Always open
            75: [71,2,False,0,[],"caa99","","","\x62",          "Mu: Slider Dark Space               "],

            76: [42,1,False,0,[],"F81D","F82D","F843","",       "Angel Village: Dance Hall           "],
            77: [42,2,False,0,[51,52,53],"caf67","Safe","\x90\x01\xb0\x00\x83\x01\x12","\x6c",
                                                                "Angel Village: Dark Space           "],

            78: [43,1,False,0,[],"1B020","","","",              "Angel Dungeon: Slider Chest         "],
            79: [43,1,False,0,[],"F89D","F8AD","F8C3","",       "Angel Dungeon: Ishtar's Room        "],
            80: [43,1,False,0,[],"1B02A","","","",              "Angel Dungeon: Puzzle Chest 1       "],
            81: [43,1,False,0,[],"1B02E","","","",              "Angel Dungeon: Puzzle Chest 2       "],
            82: [43,1,False,0,[],"1B025","","","",              "Angel Dungeon: Ishtar's Chest       "],

            83: [44,1,False,0,[],"F91D","F92D","F943","",       "Watermia: West Jar                  "],
            #84: [44,1,False,0,[],"7a5a8","","","",             "Watermia: Lance's Letter"],
            85: [44,1,False,0,[],"7ad21","7aede","","",         "Watermia: Lance                     "], #text2 was 7afa7
            86: [44,1,False,0,[],"F99D","F9AD","F9C3","",       "Watermia: Gambling House            "],
            87: [44,1,False,0,[],"79248","79288","792a1","",    "Watermia: Russian Glass             "],
            88: [44,2,False,0,[51,52,53],"cb644","Safe","\x40\x00\xa0\x00\x83\x00\x11","\x7c",
                                                                "Watermia: Dark Space                "],

            89: [45,1,False,0,[],"7b5c5","7b5d1","","",         "Great Wall: Necklace 1              "],
            90: [45,1,False,0,[],"7b625","7b631","","",         "Great Wall: Necklace 2              "],
            91: [45,1,False,0,[],"1B033","","","",              "Great Wall: Chest 1                 "],
            92: [45,1,False,0,[],"1B038","","","",              "Great Wall: Chest 2                 "],
            93: [80,2,False,0,[],"cbb11","Unsafe","\x60\x00\xc0\x02\x83\x20\x38","\x85",
                                                                "Great Wall: Archer Dark Space       "],
            94: [80,2,True,0,[],"cbb80","Unsafe","\x50\x01\x80\x04\x83\x00\x63","\x86",
                                                                "Great Wall: Platform Dark Space     "],   # Always open
            95: [46,2,False,0,[51],"cbc60","","","\x88",        "Great Wall: Appearing Dark Space    "],

            96: [48,1,False,0,[],"FA1D","FA2D","FA43","",       "Euro: Alley                         "],
            97: [48,1,False,0,[],"7c0b3","7c0f3","","",         "Euro: Apple Vendor                  "],
            98: [48,1,False,0,[],"7e51f","7e534","7e54a","",    "Euro: Hidden House                  "],
            99: [48,1,False,0,[],"7cd12","7cd39","7cd9b","",    "Euro: Store Item 1                  "],
            100: [48,1,False,0,[],"7cdf9","7ce28","7ce3e","",   "Euro: Store Item 2                  "], #text2 was 7cedd
            101: [48,1,False,0,[],"FA9D","FAAD","FAC3","",      "Euro: Laborer Room                  "],
            102: [49,1,False,0,[40],"7df58","7e10a","","",      "Euro: Ann                           "],
            103: [48,2,False,0,[51,52,53],"cc0b0","Safe","\xb0\x00\xb0\x00\x83\x00\x11","\x99",
                                                                "Euro: Dark Space                    "],

            104: [50,1,False,0,[],"1B03D","","","",             "Mt. Temple: Red Jewel Chest         "],
            105: [50,1,False,0,[],"1B042","","","",             "Mt. Temple: Drops Chest 1           "],
            106: [51,1,False,0,[],"1B047","","","",             "Mt. Temple: Drops Chest 2           "],
            107: [52,1,False,0,[],"1B04C","","","",             "Mt. Temple: Drops Chest 3           "],
            108: [53,1,False,0,[26],"1B051","","","",           "Mt. Temple: Final Chest             "],
            109: [50,2,False,0,[50],"cc24f","Unsafe","\xf0\x01\x10\x03\x83\x00\x44","\xa1",
                                                                "Mt. Temple: Dark Space 1            "],
            110: [50,2,False,0,[50],"cc419","Unsafe","\xc0\x07\xc0\x00\x83\x00\x28","\xa3",
                                                                "Mt. Temple: Dark Space 2            "],
            111: [52,2,False,0,[50],"cc7b8","","","\xa7",       "Mt. Temple: Dark Space 3            "],

            112: [54,1,False,0,[],"FB1D","FB2D","FB43","",      "Natives' Village: Statue Room       "],
            113: [55,1,False,0,[29],"893af","8942a","","",      "Natives' Village: Statue            "],
            114: [54,2,False,0,[51,52,53],"cca37","Safe","\xc0\x01\x50\x00\x83\x00\x22","\xac",
                                                                "Natives' Village: Dark Space        "],

            115: [56,1,False,0,[],"1B056","","","",              "Ankor Wat: Ramp Chest               "],
            116: [57,1,False,0,[],"1B05B","","","",              "Ankor Wat: Flyover Chest            "],
            117: [59,1,False,0,[],"1B060","","","",              "Ankor Wat: U-Turn Chest             "],
            118: [60,1,False,0,[28],"1B065","","","",            "Ankor Wat: Drop Down Chest          "],
            119: [60,1,False,0,[28],"1B06A","","","",            "Ankor Wat: Forgotten Chest          "],
            120: [59,1,False,0,[],"89fa3","89fbb","","",         "Ankor Wat: Glasses Location         "], #slow text @89fdc
            121: [60,1,False,0,[28],"89adc","89af1","89b07","",  "Ankor Wat: Spirit                   "], #item was 89b0d, text was 89e2e
            122: [76,2,True,0,[49,50],"cce92","Unsafe","\x20\x04\x30\x03\x83\x00\x46","\xb6",
                                                                 "Ankor Wat: Garden Dark Space        "],    # Always open
            123: [58,2,False,0,[49,50,51],"cd0a2","","","\xb8",  "Ankor Wat: Earthquaker Dark Space   "],
            124: [59,2,True,0,[49,50,51,53],"cd1a7","Unsafe","\xb0\x02\xc0\x01\x83\x00\x33","\xbb",
                                                                 "Ankor Wat: Drop Down Dark Space     "],   # Always open

            125: [61,1,False,0,[],"8b1b0","","","",              "Dao: Entrance Item 1                "],
            126: [61,1,False,0,[],"8b1b5","","","",              "Dao: Entrance Item 2                "],
            127: [61,1,False,0,[],"FB9D","FBAD","FBC3","",       "Dao: East Grass                     "],
            128: [61,1,False,0,[],"8b016","8b073","8b090","",    "Dao: Snake Game                     "],
            129: [61,2,False,0,[51,52,53],"cd3d0","Safe","\x20\x00\x80\x00\x83\x00\x23","\xc3",
                                                                 "Dao: Dark Space                     "],

            130: [62,1,False,0,[],"8dcb7","8e66c","8e800","",    "Pyramid: Dark Space Top             "], #text2 was 8e800
            131: [63,1,False,0,[36],"FC1D","FC2D","FC43","",     "Pyramid: Under Stairs               "],
            132: [64,1,False,0,[36],"8c7b2","8c7c9","","",       "Pyramid: Hieroglyph 1               "],
            133: [63,1,False,0,[36],"1B06F","","","",            "Pyramid: Room 2 Chest               "],
            134: [63,1,False,0,[36],"8c879","8c88c","","",       "Pyramid: Hieroglyph 2               "],
            135: [64,1,False,0,[36],"1B079","","","",            "Pyramid: Room 3 Chest               "],
            136: [78,1,False,0,[36],"8c921","8c934","","",       "Pyramid: Hieroglyph 3               "],
            137: [64,1,False,0,[36],"1B07E","","","",            "Pyramid: Room 4 Chest               "],
            138: [64,1,False,0,[36],"8c9c9","8c9dc","","",       "Pyramid: Hieroglyph 4               "],
            139: [63,1,False,0,[36],"1B074","","","",            "Pyramid: Room 5 Chest               "],
            140: [79,1,False,0,[36],"8ca71","8ca84","","",       "Pyramid: Hieroglyph 5               "],
            141: [77,1,False,0,[36],"8cb19","8cb2c","","",       "Pyramid: Hieroglyph 6               "],
            142: [77,2,True,0,[],"cd570","Unsafe","\xc0\x01\x90\x03\x83\x00\x44","\xcc",
                                                                 "Pyramid: Dark Space Bottom          "],   # Always open

            143: [66,1,False,0,[],"FC9D","FCAD","FCC3","",       "Babel: Pillow                       "],
            144: [66,1,False,0,[],"99a4f","99ae4","99afe","",    "Babel: Force Field                  "], #item was  99a61
            145: [66,2,False,0,[51,52,53],"ce09b","Forced Unsafe","\x90\x07\xb0\x01\x83\x10\x28","\xdf",
                                                                 "Babel: Dark Space Bottom            "],
            146: [67,2,False,0,[51,52,53],"ce159","Safe","\xb0\x02\xb0\x01\x83\x10\x23","\xe3",
                                                                 "Babel: Dark Space Top               "],

            147: [68,1,False,0,[],"1B083","","","",              "Jeweler's Mansion: Chest            "],

            148: [18,3,False,0,[55,56,57,58,59],"","","","",     "Castoth Prize                       "],
            149: [32,3,False,0,[54,56,57,58,59],"","","","",     "Viper Prize                         "],
            150: [41,3,False,0,[54,55,57,58,59],"","","","",     "Vampires Prize                      "],
            151: [47,3,False,0,[54,55,56,58,59],"","","","",     "Sand Fanger Prize                   "],
            152: [65,3,False,0,[54,55,56,57,59],"","","","",     "Mummy Queen Prize                   "],
            153: [67,3,False,0,[54,55,56,57,58],"","","","",     "Babel Prize                         "]
        }

        # World graph is initially populated only with "free" edges
        # Format: { Region ID: Traversed flag, [Accessible regions], Region Name],
        #                                                       ItemsToRemove }
        self.graph = {
            -1: [False,[0],"Game Start",[]],

            0:  [False,[7,14,15,74],"South Cape",[9]],

            74: [False,[],"Jeweler Access",[]],
            1:  [False,[],"Jeweler Reward 1",[]],
            2:  [False,[],"Jeweler Reward 2",[]],
            3:  [False,[],"Jeweler Reward 3",[]],
            4:  [False,[],"Jeweler Reward 4",[]],
            5:  [False,[],"Jeweler Reward 5",[]],
            6:  [False,[],"Jeweler Reward 6",[]],

            7:  [False,[0,8,14,15],"Edward's Castle",[]],
            8:  [False,[],"Edward's Prison",[2]],
            9:  [False,[],"Underground Tunnel - Behind Prison Key",[]],
            10: [False,[7,9],"Underground Tunnel - Behind Lilly",[]],
            12: [False,[0,7,14,15],"Itory Village",[23]],
            13: [False,[],"Itory Cave",[]],
            75: [False,[],"Got Lilly",[]],
            14: [False,[0,7,15],"Moon Tribe",[25]],
            73: [False,[],"Moon Tribe Cave",[]],
            15: [False,[0,7,14],"Inca Ruins",[7]],
            16: [False,[15],"Inca Ruins - Behind Diamond Tile & Psycho Dash",[8]],
            17: [False,[],"Inca Ruins - Behind Wind Melody",[3,4]],
            18: [False,[19],"Inca Ruins - Castoth",[]],
            19: [False,[20],"Gold Ship",[]],

            20: [False,[21,22,27,28],"Diamond Coast",[]],
            21: [False,[20,22,27,28,74],"Freejia",[]],
            22: [False,[20,21,27,28],"Diamond Mine",[15]],
            23: [False,[],"Diamond Mine - Behind Psycho Dash",[]],
            24: [False,[],"Diamond Mine - Behind Dark Friar",[]],
            25: [False,[],"Diamond Mine - Behind Elevator Key",[11,12]],
            26: [False,[],"Diamond Mine - Behind Mine Keys",[]],
            27: [False,[20,21,22,28],"Neil's Cottage",[13]],
            28: [False,[20,21,22,27,29],"Nazca Plain",[]],
            29: [False,[28],"Sky Garden",[14,14,14,14]],
            30: [False,[72],"Sky Garden - Behind Dark Friar",[]],
            72: [False,[],"Sky Garden - Behind Friar or Barrier",[]],
            31: [False,[],"Sky Garden - Behind Psycho Dash",[]],
            32: [False,[33],"Sky Garden - Viper",[]],

            33: [False,[],"Seaside Palace",[16,17]],
            34: [False,[],"Seaside Palace - Behind Purification Stone",[]],
            35: [False,[],"Seaside Palace - Behind Necklace",[]],
            36: [False,[37,42],"Seaside Palace - Mu Passage",[16]],
            37: [False,[],"Mu",[18]],
            38: [False,[],"Mu - Behind Hope Statue 1",[18]],
            71: [False,[],"Mu - Behind Dark Friar",[]],
            39: [False,[],"Mu - Behind Psycho Slide",[]],
            40: [False,[],"Mu - Behind Hope Statue 2",[19,19]],
            41: [False,[],"Mu - Vampires",[]],
            42: [False,[36,44,45,74],"Angel Village",[]],
            43: [False,[],"Angel Village Dungeon",[]],
            44: [False,[42,45,74],"Watermia",[24]],
            45: [False,[42,44,45,80],"Great Wall",[]],
            80: [False,[],"Great Wall - Behind Ramp",[]],
            46: [False,[],"Great Wall - Behind Dark Friar",[]],
            47: [False,[46],"Great Wall - Sand Fanger",[]],

            48: [False,[54,56,74],"Euro",[24,40]],
            49: [False,[],"Euro - Ann's Item",[]],
            50: [False,[],"Mt. Temple",[26]],
            51: [False,[],"Mt. Temple - Behind Drops 1",[26]],
            52: [False,[],"Mt. Temple - Behind Drops 2",[26]],
            53: [False,[],"Mt. Temple - Behind Drops 3",[]],
            54: [False,[48,56],"Natives' Village",[10,29]],
            55: [False,[],"Natives' Village - Statue Item",[]],
            56: [False,[48,54],"Ankor Wat",[]],
            76: [False,[56],"Ankor Wat - Garden",[]],
            57: [False,[56,76],"Ankor Wat - Behind Psycho Slide & Spin Dash",[]],
            58: [False,[],"Ankor Wat - Behind Dark Friar",[]],
            59: [False,[56],"Ankor Wat - Behind Earthquaker",[]],
            60: [False,[76],"Ankor Wat - Behind Black Glasses",[]],

            61: [False,[54,74],"Dao",[]],
            62: [False,[61],"Pyramid",[30,31,32,33,34,35,38]],
            77: [False,[62],"Pyramid - Bottom Level",[]],
            63: [False,[77,78,79],"Pyramid - Behind Aura",[]],
            64: [False,[77],"Pyramid - Behind Spin Dash",[]],
            78: [False,[77],"Pyramid - Behind Dark Friar",[]],
            79: [False,[77],"Pyramid - Behind Earthquaker",[]],
            65: [False,[],"Pyramid - Mummy Queen",[38]],

            66: [False,[],"Babel Tower",[]],
            67: [False,[61],"Babel Tower - Behind Crystal Ring and Aura",[]],
            68: [False,[61],"Jeweler's Mansion",[]],

            69: [False,[],"Rescue Kara",[]],
            70: [False,[],"Dark Gaia",[]]
        }

        # Define logical paths in dynamic graph
        # Format: { ID: [StartRegion, DestRegion, [[item1, qty1],[item2,qty2]...]]}
        self.logic = {
            # Jeweler Rewards
            0: [74,1,[[1,gem[0]]]],                    # Jeweler Reward 1
            1: [74,1,[[1,gem[0]-2],[46,1]]],
            2: [74,1,[[1,gem[0]-3],[47,1]]],
            3: [74,1,[[1,gem[0]-5],[46,1],[47,1]]],
            4: [1,2,[[1,gem[1]]]],                    # Jeweler Reward 2
            5: [1,2,[[1,gem[1]-2],[46,1]]],
            6: [1,2,[[1,gem[1]-3],[47,1]]],
            7: [1,2,[[1,gem[1]-5],[46,1],[47,1]]],
            8: [2,3,[[1,gem[2]]]],                    # Jeweler Reward 3
            9: [2,3,[[1,gem[2]-2],[46,1]]],
            10: [2,3,[[1,gem[2]-3],[47,1]]],
            11: [2,3,[[1,gem[2]-5],[46,1],[47,1]]],
            12: [3,4,[[1,gem[3]]]],                    # Jeweler Reward 4
            13: [3,4,[[1,gem[3]-2],[46,1]]],
            14: [3,4,[[1,gem[3]-3],[47,1]]],
            15: [3,4,[[1,gem[3]-5],[46,1],[47,1]]],
            16: [4,5,[[1,gem[4]]]],                    # Jeweler Reward 5
            17: [4,5,[[1,gem[4]-2],[46,1]]],
            18: [4,5,[[1,gem[4]-3],[47,1]]],
            19: [4,5,[[1,gem[4]-5],[46,1],[47,1]]],
            20: [5,6,[[1,gem[5]]]],                    # Jeweler Reward 6
            21: [5,6,[[1,gem[5]-2],[46,1]]],
            22: [5,6,[[1,gem[5]-3],[47,1]]],
            23: [5,6,[[1,gem[5]-5],[46,1],[47,1]]],
            24: [6,68,[[1,gem[6]]]],                   # Jeweler Reward 7 (Mansion)
            25: [6,68,[[1,gem[6]-2],[46,1]]],
            26: [6,68,[[1,gem[6]-3],[47,1]]],
            27: [6,68,[[1,gem[6]-5],[46,1],[47,1]]],

            # Inter-Continental Travel
            30: [0,20,[[37,1]]],         # Cape to Coast w/ Lola's Letter
            31: [0,44,[[37,1]]],         # Cape to Watermia w/ Lola's Letter
            32: [20,0,[[37,1]]],         # Coast to Cape w/ Lola's Letter
            33: [20,44,[[37,1]]],        # Coast to Watermia w/ Lola's Letter
            34: [44,0,[[37,1]]],         # Watermia to Cape w/ Lola's Letter
            35: [44,20,[[37,1]]],        # Watermia to Coast w/ Lola's Letter
            36: [27,48,[[13,1]]],        # Neil's to Euro w/ Memory Melody
            37: [27,61,[[13,1]]],        # Neil's to Dao w/ Memory Melody
            38: [27,66,[[13,1]]],        # Neil's to Babel w/ Memory Melody
            39: [14,28,[[25,1]]],        # Moon Tribe to Nazca w/ Teapot
            40: [14,33,[[25,1]]],        # Moon Tribe to Seaside Palace w/ Teapot
            41: [44,48,[[24,1]]],        # Watermia to Euro w/ Will
            42: [48,44,[[24,1]]],        # Euro to Watermia w/ Will
            43: [54,61,[[10,1]]],        # Natives' to Dao w/ Large Roast

            # SW Continent
            50: [0,12,[[9,1]]],          # Cape to Itory w/ Lola's Melody
            51: [8,9,[[2,1]]],           # Prison to Tunnel w/ Prison Key
            52: [75,10,[[2,1]]],         # Tunnel Progression w/ Lilly
            53: [12,13,[[48,1]]],        # Itory Cave w/ Psycho Dash
            54: [12,13,[[49,1]]],        # Itory Cave w/ Psycho Slide
            55: [12,13,[[50,1]]],        # Itory Cave w/ Spin Dash
            56: [12,75,[[23,1]]],        # Get Lilly w/ Necklace
            57: [14,29,[[25,1]]],        # Moon Tribe to Sky Garden w/ Teapot
            58: [15,16,[[7,1],[48,1]]],  # Inca Ruins w/ Tile and Psycho Dash
            59: [15,16,[[7,1],[49,1]]],  # Inca Ruins w/ Tile and Psycho Slide
            60: [15,16,[[7,1],[50,1]]],  # Inca Ruins w/ Tile and Spin Dash
            61: [16,17,[[8,1]]],         # Inca Ruins w/ Wind Melody
            62: [17,18,[[3,1],[4,1]]],   # Inca Ruins w/ Inca Statues
            63: [14,73,[[48,1]]],        # Moon Tribe Cave w/ Psycho Dash
            64: [14,73,[[49,1]]],        # Moon Tribe Cave w/ Psycho Slider
            65: [14,73,[[50,1]]],        # Moon Tribe Cave w/ Spin Dash

            # SE Continent
            70: [22,23,[[48,1]]],        # Diamond Mine Progression w/ Psycho Dash
            71: [22,23,[[49,1]]],        # Diamond Mine Progression w/ Psycho Slide
            72: [22,23,[[50,1]]],        # Diamond Mine Progression w/ Spin Dash
            73: [22,24,[[51,1]]],        # Diamond Mine Progression w/ Dark Friar
            74: [22,24,[[50,1]]],        # Diamond Mine Progression w/ Spin Dash
            75: [22,25,[[15,1]]],        # Diamond Mine Progression w/ Elevator Key
            76: [25,26,[[11,1],[12,1]]], # Diamond Mine Progression w/ Mine Keys
            77: [29,30,[[51,1]]],        # Sky Garden Progression w/ Dark Friar
            78: [29,72,[[52,1]]],        # Sky Garden Progression w/ Aura Barrier
            79: [29,32,[[14,4]]],        # Sky Garden Progression w/ Crystal Balls
            80: [29,31,[[48,1]]],        # Sky Garden Progression w/ Psycho Dash
            81: [29,31,[[49,1]]],        # Sky Garden Progression w/ Psycho Slide
            82: [29,31,[[50,1]]],        # Sky Garden Progression w/ Spin Dash

            # NE Continent
            90:  [33,34,[[17,1]]],         # Seaside Progression w/ Purity Stone
            91:  [33,35,[[9,1],[16,1],[23,1],[37,1]]],
                                           # Seaside Progression w/ Lilly
            92:  [33,36,[[16,1]]],         # Seaside to Mu w/ Mu Key
            93:  [36,33,[[16,1]]],         # Mu to Seaside w/ Mu Key
            94:  [37,38,[[18,1]]],         # Mu Progression w/ Statue of Hope 1
            95:  [38,71,[[51,1]]],         # Mu Progression w/ Dark Friar
            96:  [38,71,[[49,1]]],         # Mu Progression w/ Psycho Slide
            97:  [38,39,[[49,1]]],         # Mu Progression w/ Psycho Slide
            98:  [71,40,[[18,2]]],         # Mu Progression w/ Statue of Hope 2
            99:  [40,41,[[19,2]]],         # Mu Progression w/ Rama Statues
            100: [42,43,[[49,1]]],         # Angel Village to Dungeon w/ Slide
            101: [80,46,[[51,1]]],         # Great Wall Progression w/ Dark Friar
            102: [46,47,[[50,1]]],         # Great Wall Progression w/ Spin Dash
            103: [80,45,[[50,1]]],         # Escape Great Wall w/ Spin Dash

            # N Continent
            110: [48,49,[[40,1]]],        # Ann item w/ Apple
            111: [48,50,[[50,1]]],        # Euro to Mt. Temple w/ Spin Dash
            112: [50,51,[[26,1]]],        # Mt. Temple Progression w/ Drops 1
            113: [51,52,[[26,2]]],        # Mt. Temple Progression w/ Drops 2
            114: [52,53,[[26,3]]],        # Mt. Temple Progression w/ Drops 3
            115: [50,48,[[50,1]]],        # Mt. Temple to Euro w/ Spin
            116: [54,55,[[29,1]]],        # Natives' Village Progression w/ Flower
            117: [56,57,[[49,1],[50,1]]], # Ankor Wat Progression w/ Slide and Spin
            118: [57,58,[[51,1]]],        # Ankor Wat Progression w/ Dark Friar
            119: [57,58,[[36,1]]],        # Ankor Wat Progression w/ Aura
            120: [57,59,[[53,1]]],        # Ankor Wat Progression w/ Earthquaker
            121: [59,60,[[28,1],[49,1]]], # Ankor Wat Progression w/ Black Glasses

            # NW Continent
            130: [61,62,[[49,1]]],        # Pyramid foyer w/ Slide
            131: [61,62,[[50,1]]],        # Pyramid foyer w/ Spin
            132: [62,63,[[36,1]]],        # Pyramid Progression w/ Aura
            133: [77,78,[[51,1]]],        # Pyramid Progression w/ Dark Friar
            134: [77,79,[[53,1]]],        # Pyramid Progression w/ Earthquaker
            135: [62,65,[[30,1],[31,1],[32,1],[33,1],[34,1],[35,1],[38,1]]],
                                          # Pyramid Boss w/ Hieroglyphs and Journal
            136: [77,64,[[50,1]]],        # Pyramid Progression w/ Spin Dash

            # Babel/Jeweler Mansion
            140: [66,67,[[36,1],[39,1]]], # Babel Progression w/ Aura and Crystal Ring
            141: [68,67,[[49,1]]],         # Jeweler Mansion to Babel Top w/Slide

            # Endgame
            150: [10,69,[[20,2]]],        # Rescue Kara from Edward's w/ Magic Dust
            151: [26,69,[[20,2]]],        # Rescue Kara from Mine w/ Magic Dust
            152: [43,69,[[20,2]]],        # Rescue Kara from Angel w/ Magic Dust
            153: [53,69,[[20,2]]],        # Rescue Kara from Mt. Temple w/ Magic Dust
            154: [60,69,[[20,2]]],        # Rescue Kara from Ankor Wat w/ Magic Dust
            155: [69,70,[[36,1],[54,0],[55,0],[56,0],[57,0],[58,0],[59,0]]]
                                         # Beat Game w/Mystic Statues and Aura
        }

        # Define addresses for in-game spoiler text
        self.spoiler_addresses = {
            0: "4caf5",   # Edward's Castle guard, top floor (4c947)
            1: "4e9ff",   # Itory elder (4e929)
            2: "58ac0",   # Gold Ship queen (589ff)
            3: "5ad6b",   # Man at Diamond Coast (5ab5c)
            #4: "5bfde",   # Freejia laborer (5bfaa)
            5: "69167",   # Seaside Palace empty coffin (68feb)
            6: "6dc97",   # Ishtar's apprentice (6dc50)
            7: "79c81",   # Watermia, Kara's journal (79bf5)
            8: "7d892",   # Euro: Erasquez (7d79e)
            9: "89b2a",   # Ankor Wat, spirit (89abf)
            10: "8ad0c",   # Dao: girl with note (8acc5)
            11: "99b8f",   # Babel: spirit (99b2e)

        }

        # Define location text for in-game format
        self.location_text = {
            0: "\x64\x87\x84\xac\x49\x84\xa7\x84\x8b\x84\xa2",  # "the Jeweler"
            1: "\x64\x87\x84\xac\x49\x84\xa7\x84\x8b\x84\xa2",  # "the Jeweler"
            2: "\x64\x87\x84\xac\x49\x84\xa7\x84\x8b\x84\xa2",  # "the Jeweler"
            3: "\x64\x87\x84\xac\x49\x84\xa7\x84\x8b\x84\xa2",  # "the Jeweler"
            4: "\x64\x87\x84\xac\x49\x84\xa7\x84\x8b\x84\xa2",  # "the Jeweler"
            5: "\x64\x87\x84\xac\x49\x84\xa7\x84\x8b\x84\xa2",  # "the Jeweler"

            6: "\x63\x8e\xa5\xa4\x87\xac\x42\x80\xa0\x84",    # "South Cape"
            7: "\x63\x8e\xa5\xa4\x87\xac\x42\x80\xa0\x84",    # "South Cape"
            8: "\x63\x8e\xa5\xa4\x87\xac\x42\x80\xa0\x84",    # "South Cape"
            9: "\x63\x8e\xa5\xa4\x87\xac\x42\x80\xa0\x84",    # "South Cape"
            10: "\x63\x8e\xa5\xa4\x87\xac\x42\x80\xa0\x84",    # "South Cape"

            11: "\x44\x83\xa7\x80\xa2\x83\x0e\xa3\xac\x42\x80\xa3\xa4\x8b\x84",   # "Edward's Castle"
            12: "\x44\x83\xa7\x80\xa2\x83\x0e\xa3\xac\x42\x80\xa3\xa4\x8b\x84",   # "Edward's Castle"

            13: "\x44\x83\xa7\x80\xa2\x83\x0e\xa3\xac\x60\xa2\x88\xa3\x8e\x8d",   # "Edward's Prison"
            14: "\x44\x83\xa7\x80\xa2\x83\x0e\xa3\xac\x60\xa2\x88\xa3\x8e\x8d",   # "Edward's Prison"

            15: "\x44\x83\xa7\x80\xa2\x83\x0e\xa3\xac\x64\xa5\x8d\x8d\x84\x8b",   # "Edward's Tunnel"
            16: "\x44\x83\xa7\x80\xa2\x83\x0e\xa3\xac\x64\xa5\x8d\x8d\x84\x8b",   # "Edward's Tunnel"
            17: "\x44\x83\xa7\x80\xa2\x83\x0e\xa3\xac\x64\xa5\x8d\x8d\x84\x8b",   # "Edward's Tunnel"
            18: "\x44\x83\xa7\x80\xa2\x83\x0e\xa3\xac\x64\xa5\x8d\x8d\x84\x8b",   # "Edward's Tunnel"
            19: "\x44\x83\xa7\x80\xa2\x83\x0e\xa3\xac\x64\xa5\x8d\x8d\x84\x8b",   # "Edward's Tunnel"

            20: "\x48\xa4\x8e\xa2\xa9",   # "Itory"
            21: "\x48\xa4\x8e\xa2\xa9",   # "Itory"
            22: "\x48\xa4\x8e\xa2\xa9",   # "Itory"

            23: "\x4c\x8e\x8e\x8d\xac\x44\xa2\x88\x81\x84",   # "Moon Tribe"

            24: "\x48\x8d\x82\x80",   # "Inca"
            25: "\x48\x8d\x82\x80",   # "Inca"
            26: "\x48\x8d\x82\x80",   # "Inca"
            27: "\x48\x8d\x82\x80",   # "Inca"
            28: "\x63\x88\x8d\x86\x88\x8d\x86\xac\xa3\xa4\x80\xa4\xa5\x84",   # "Singing Statue"
            29: "\x48\x8d\x82\x80",   # "Inca"
            30: "\x48\x8d\x82\x80",   # "Inca"
            31: "\x48\x8d\x82\x80",   # "Inca"

            32: "\x46\x8e\x8b\x83\xac\x63\x87\x88\xa0",   # "Gold Ship"

            33: "\xd6\x0e\x42\x8e\x80\xa3\xa4",   # "Diamond Coast"

            34: "\x45\xa2\x84\x84\x89\x88\x80",   # "Freejia"
            35: "\x45\xa2\x84\x84\x89\x88\x80",   # "Freejia"
            36: "\x45\xa2\x84\x84\x89\x88\x80",   # "Freejia"
            37: "\x45\xa2\x84\x84\x89\x88\x80",   # "Freejia"
            38: "\x45\xa2\x84\x84\x89\x88\x80",   # "Freejia"
            39: "\x45\xa2\x84\x84\x89\x88\x80",   # "Freejia"

            40: "\xd6\x0e\x4c\x88\x8d\x84",       # "Diamond Mine"
            41: "\x4b\x80\x81\x8e\xa2\x84\xa2",   # "Laborer"
            42: "\x4b\x80\x81\x8e\xa2\x84\xa2",   # "Laborer"
            43: "\xd6\x0e\x4c\x88\x8d\x84",       # "Diamond Mine"
            44: "\x4b\x80\x81\x8e\xa2\x84\xa2",   # "Laborer"
            45: "\x63\x80\x8c",                   # "Sam"
            46: "\xd6\x0e\x4c\x88\x8d\x84",       # "Diamond Mine"
            47: "\xd6\x0e\x4c\x88\x8d\x84",       # "Diamond Mine"
            48: "\xd6\x0e\x4c\x88\x8d\x84",       # "Diamond Mine"


            49: "\x63\x8a\xa9\xac\x46\x80\xa2\x83\x84\x8d",   # "Sky Garden"
            50: "\x63\x8a\xa9\xac\x46\x80\xa2\x83\x84\x8d",   # "Sky Garden"
            51: "\x63\x8a\xa9\xac\x46\x80\xa2\x83\x84\x8d",   # "Sky Garden"
            52: "\x63\x8a\xa9\xac\x46\x80\xa2\x83\x84\x8d",   # "Sky Garden"
            53: "\x63\x8a\xa9\xac\x46\x80\xa2\x83\x84\x8d",   # "Sky Garden"
            54: "\x63\x8a\xa9\xac\x46\x80\xa2\x83\x84\x8d",   # "Sky Garden"
            55: "\x63\x8a\xa9\xac\x46\x80\xa2\x83\x84\x8d",   # "Sky Garden"
            56: "\x63\x8a\xa9\xac\x46\x80\xa2\x83\x84\x8d",   # "Sky Garden"
            57: "\x63\x8a\xa9\xac\x46\x80\xa2\x83\x84\x8d",   # "Sky Garden"
            58: "\x63\x8a\xa9\xac\x46\x80\xa2\x83\x84\x8d",   # "Sky Garden"
            59: "\x63\x8a\xa9\xac\x46\x80\xa2\x83\x84\x8d",   # "Sky Garden"
            60: "\x63\x8a\xa9\xac\x46\x80\xa2\x83\x84\x8d",   # "Sky Garden"

            61: "\xd7\x32\xd7\x93",   # "Seaside Palace"
            62: "\xd7\x32\xd7\x93",   # "Seaside Palace"
            63: "\xd7\x32\xd7\x93",   # "Seaside Palace"
            64: "\x41\xa5\x85\x85\xa9",   # "Buffy"
            65: "\x42\x8e\x85\x85\x88\x8d",   # "Coffin"
            66: "\xd7\x32\xd7\x93",   # "Seaside Palace"

            67: "\x4c\xa5",   # "Mu"
            68: "\x4c\xa5",   # "Mu"
            69: "\x4c\xa5",   # "Mu"
            70: "\x4c\xa5",   # "Mu"
            71: "\x4c\xa5",   # "Mu"
            72: "\x4c\xa5",   # "Mu"
            73: "\x4c\xa5",   # "Mu"
            74: "\x4c\xa5",   # "Mu"
            75: "\x4c\xa5",   # "Mu"

            76: "\xd6\x01\x66\x88\x8b\x8b\x80\x86\x84",   # "Angel Village"
            77: "\xd6\x01\x66\x88\x8b\x8b\x80\x86\x84",   # "Angel Village"
            78: "\xd6\x01\x66\x88\x8b\x8b\x80\x86\x84",   # "Angel Village"
            79: "\xd6\x01\x66\x88\x8b\x8b\x80\x86\x84",   # "Angel Village"
            80: "\xd6\x01\x66\x88\x8b\x8b\x80\x86\x84",   # "Angel Village"
            81: "\xd6\x01\x66\x88\x8b\x8b\x80\x86\x84",   # "Angel Village"
            82: "\xd6\x01\x66\x88\x8b\x8b\x80\x86\x84",   # "Angel Village"

            83: "\x67\x80\xa4\x84\xa2\x8c\x88\x80",   # "Watermia"
            84: "\x67\x80\xa4\x84\xa2\x8c\x88\x80",   # "Watermia"
            85: "\x4b\x80\x8d\x82\x84",   # "Lance"
            86: "\x67\x80\xa4\x84\xa2\x8c\x88\x80",   # "Watermia"
            87: "\x67\x80\xa4\x84\xa2\x8c\x88\x80",   # "Watermia"
            88: "\x67\x80\xa4\x84\xa2\x8c\x88\x80",   # "Watermia"

            89: "\xd6\x16\x67\x80\x8b\x8b",   # "Great Wall"
            90: "\xd6\x16\x67\x80\x8b\x8b",   # "Great Wall"
            91: "\xd6\x16\x67\x80\x8b\x8b",   # "Great Wall"
            92: "\xd6\x16\x67\x80\x8b\x8b",   # "Great Wall"
            93: "\xd6\x16\x67\x80\x8b\x8b",   # "Great Wall"
            94: "\xd6\x16\x67\x80\x8b\x8b",   # "Great Wall"
            95: "\xd6\x16\x67\x80\x8b\x8b",   # "Great Wall"

            96: "\x44\xa5\xa2\x8e",   # "Euro"
            97: "\x44\xa5\xa2\x8e",   # "Euro"
            98: "\x44\xa5\xa2\x8e",   # "Euro"
            99: "\x44\xa5\xa2\x8e",   # "Euro"
            100: "\x44\xa5\xa2\x8e",   # "Euro"
            101: "\x44\xa5\xa2\x8e",   # "Euro"
            102: "\x40\x8d\x8d",       # "Ann"
            103: "\x44\xa5\xa2\x8e",   # "Euro"

            104: "\x4c\xa4\x2a\xac\x4a\xa2\x84\xa3\xa3",   # "Mt. Kress"
            105: "\x4c\xa4\x2a\xac\x4a\xa2\x84\xa3\xa3",   # "Mt. Kress"
            106: "\x4c\xa4\x2a\xac\x4a\xa2\x84\xa3\xa3",   # "Mt. Kress"
            107: "\x4c\xa4\x2a\xac\x4a\xa2\x84\xa3\xa3",   # "Mt. Kress"
            108: "\x4c\xa4\x2a\xac\x4a\xa2\x84\xa3\xa3\xac\x6e\x84\x8d\x83\x6f",   # "Mt. Kress (end)"
            109: "\x4c\xa4\x2a\xac\x4a\xa2\x84\xa3\xa3",   # "Mt. Kress"
            110: "\x4c\xa4\x2a\xac\x4a\xa2\x84\xa3\xa3",   # "Mt. Kress"
            111: "\x4c\xa4\x2a\xac\x4a\xa2\x84\xa3\xa3",   # "Mt. Kress"

            112: "\xd7\x21\x66\x88\x8b\x8b\x80\x86\x84",   # "Native Village"
            113: "\x63\xa4\x80\xa4\xa5\x84",               # "Statue"
            114: "\xd7\x21\x66\x88\x8b\x8b\x80\x86\x84",   # "Native Village"

            115: "\x40\x8d\x8a\x8e\xa2\xac\x67\x80\xa4",   # "Ankor Wat"
            116: "\x40\x8d\x8a\x8e\xa2\xac\x67\x80\xa4",   # "Ankor Wat"
            117: "\x40\x8d\x8a\x8e\xa2\xac\x67\x80\xa4",   # "Ankor Wat"
            118: "\x40\x8d\x8a\x8e\xa2\xac\x67\x80\xa4",   # "Ankor Wat"
            119: "\x40\x8d\x8a\x8e\xa2\xac\x67\x80\xa4",   # "Ankor Wat"
            120: "\x63\x87\xa2\xa5\x81\x81\x84\xa2",       # "Shrubber"
            121: "\x63\xa0\x88\xa2\x88\xa4",               # "Spirit"
            122: "\x40\x8d\x8a\x8e\xa2\xac\x67\x80\xa4",   # "Ankor Wat"
            123: "\x40\x8d\x8a\x8e\xa2\xac\x67\x80\xa4",   # "Ankor Wat"
            124: "\x40\x8d\x8a\x8e\xa2\xac\x67\x80\xa4",   # "Ankor Wat"

            125: "\x43\x80\x8e",   # "Dao"
            126: "\x43\x80\x8e",   # "Dao"
            127: "\x43\x80\x8e",   # "Dao"
            128: "\x63\x8d\x80\x8a\x84\xac\x86\x80\x8c\x84",   # "Snake Game"
            129: "\x43\x80\x8e",   # "Dao"

            130: "\x46\x80\x88\x80",   # "Gaia"
            131: "\xd6\x3f",   # "Pyramid"
            132: "\xd6\x3f",   # "Pyramid"
            133: "\xd6\x3f",   # "Pyramid"
            134: "\xd6\x3f",   # "Pyramid"
            135: "\xd6\x3f",   # "Pyramid"
            136: "\x4a\x88\x8b\x8b\x84\xa2\xac\x26",   # "Killer 6"
            137: "\xd6\x3f",   # "Pyramid"
            138: "\xd6\x3f",   # "Pyramid"
            139: "\xd6\x3f",   # "Pyramid"
            140: "\xd6\x3f",   # "Pyramid"
            141: "\xd6\x3f",   # "Pyramid"
            142: "\xd6\x3f",   # "Pyramid"

            143: "\x41\x80\x81\x84\x8b",   # "Babel"
            144: "\x41\x80\x81\x84\x8b",   # "Babel"
            145: "\x41\x80\x81\x84\x8b",   # "Babel"
            146: "\x41\x80\x81\x84\x8b",   # "Babel"

            147: "\x49\x84\xa7\x84\x8b\x84\xa2\x0e\xa3\xac\x4c\x80\x8d\xa3\x88\x8e\x8d",   # "Jeweler's Mansion"

            148: "",   # "Castoth"
            149: "",   # "Viper"
            150: "",   # "Vampires"
            151: "",   # "Sand Fanger"
            152: "",   # "Mummy Queen"
            153: ""    # "Olman"

        }


        # Define long item text for in-game format
        self.item_text_long = {
            0: "\xd3\xd6\x1d\x8d\x8e\xa4\x87\x88\x8d\x86\x4f\xac\xac\xac\xac\xac\xac\xac\xac\xac\xac",
            1: "\xd3\xd6\x1d\x80\xac\x62\x84\x83\xac\x49\x84\xa7\x84\x8b\x4f\xac\xac\xac\xac\xac\xac",
            2: "\xd3\xd6\x1d\xa4\x87\x84\xac\x60\xa2\x88\xa3\x8e\x8d\xac\x4a\x84\xa9\x4f\xac\xac\xac",
            3: "\xd3\xd6\x1d\x48\x8d\x82\x80\xac\x63\xa4\x80\xa4\xa5\x84\xac\x40\x4f\xac\xac\xac\xac",
            4: "\xd3\xd6\x1d\x48\x8d\x82\x80\xac\x63\xa4\x80\xa4\xa5\x84\xac\x41\x4f\xac\xac\xac\xac",
            5: "",
            6: "\xd3\xd6\x1d\x80\x8d\xac\x87\x84\xa2\x81\x4f\xac\xac\xac\xac\xac\xac\xac\xac\xac\xac",
            7: "\xd3\xd6\x1d\xa4\x87\x84\xac\x43\x88\x80\x8c\x8e\x8d\x83\xac\x41\x8b\x8e\x82\x8a\x4f",
            8: "\xd3\xd6\x1d\xa4\x87\x84\xac\x67\x88\x8d\x83\xac\x4c\x84\x8b\x8e\x83\xa9\x4f\xac\xac",
            9: "\xd3\xd6\x1d\x4b\x8e\x8b\x80\x0e\xa3\xac\x4c\x84\x8b\x8e\x83\xa9\x4f\xac\xac\xac\xac",
            10: "\xd3\xd6\x1d\xa4\x87\x84\xac\x4b\x80\xa2\x86\x84\xac\x62\x8e\x80\xa3\xa4\x4f\xac\xac",
            11: "\xd3\xd6\x1d\x4c\x88\x8d\x84\xac\x4a\x84\xa9\xac\x40\x4f\xac\xac\xac\xac\xac\xac\xac",
            12: "\xd3\xd6\x1d\x4c\x88\x8d\x84\xac\x4a\x84\xa9\xac\x41\x4f\xac\xac\xac\xac\xac\xac\xac",
            13: "\xd3\xd6\x1d\xa4\x87\x84\xac\x4c\x84\x8c\x8e\xa2\xa9\xac\x4c\x84\x8b\x8e\x83\xa9\x4f",
            14: "\xd3\xd6\x1d\x80\xac\x42\xa2\xa9\xa3\xa4\x80\x8b\xac\x41\x80\x8b\x8b\x4f\xac\xac\xac",
            15: "\xd3\xd6\x1d\xa4\x87\x84\xac\x44\x8b\x84\xa6\x80\xa4\x8e\xa2\xac\x4a\x84\xa9\x4f\xac",
            16: "\xd3\xd6\x1d\xa4\x87\x84\xac\x4c\xa5\xac\x60\x80\x8b\x80\x82\x84\xac\x4a\x84\xa9\x4f",
            17: "\xd3\xd6\x1d\xa4\x87\x84\xac\x60\xa5\xa2\x88\xa4\xa9\xac\x63\xa4\x8e\x8d\x84\x4f\xac",
            18: "\xd3\xd6\x1d\x80\xac\x63\xa4\x80\xa4\xa5\x84\xac\x8e\x85\xac\x47\x8e\xa0\x84\x4f\xac",
            19: "\xd3\xd6\x1d\x80\xac\x62\x80\x8c\x80\xac\x63\xa4\x80\xa4\xa5\x84\x4f\xac\xac\xac\xac",
            20: "\xd3\xd6\x1d\xa4\x87\x84\xac\x4c\x80\x86\x88\x82\xac\x43\xa5\xa3\xa4\x4f\xac\xac\xac",
            21: "",
            22: "\xd3\xd6\x1d\x4b\x80\x8d\x82\x84\x0e\xa3\xac\x4b\x84\xa4\xa4\x84\xa2\x4f\xac\xac\xac",
            23: "\xd3\xd6\x1d\xa4\x87\x84\xac\x4d\x84\x82\x8a\x8b\x80\x82\x84\x4f\xac\xac\xac\xac\xac",
            24: "\xd3\xd6\x1d\xa4\x87\x84\xac\x67\x88\x8b\x8b\x4f\xac\xac\xac\xac\xac\xac\xac\xac\xac",
            25: "\xd3\xd6\x1d\xa4\x87\x84\xac\x64\x84\x80\xa0\x8e\xa4\x4f\xac\xac\xac\xac\xac\xac\xac",
            26: "\xd3\xd6\x1d\x4c\xa5\xa3\x87\xa2\x8e\x8e\x8c\xac\x43\xa2\x8e\xa0\xa3\x4f\xac\xac\xac",
            27: "",
            28: "\xd3\xd6\x1d\xa4\x87\x84\xac\x41\x8b\x80\x82\x8a\xac\x46\x8b\x80\xa3\xa3\x84\xa3\x4f",
            29: "\xd3\xd6\x1d\xa4\x87\x84\xac\x46\x8e\xa2\x86\x8e\x8d\xac\x45\x8b\x8e\xa7\x84\xa2\x4f",
            30: "\xd3\xd6\x1d\x80\xac\x47\x88\x84\xa2\x8e\x86\x8b\xa9\xa0\x87\xac\x64\x88\x8b\x84\x4f",
            31: "\xd3\xd6\x1d\x80\xac\x47\x88\x84\xa2\x8e\x86\x8b\xa9\xa0\x87\xac\x64\x88\x8b\x84\x4f",
            32: "\xd3\xd6\x1d\x80\xac\x47\x88\x84\xa2\x8e\x86\x8b\xa9\xa0\x87\xac\x64\x88\x8b\x84\x4f",
            33: "\xd3\xd6\x1d\x80\xac\x47\x88\x84\xa2\x8e\x86\x8b\xa9\xa0\x87\xac\x64\x88\x8b\x84\x4f",
            34: "\xd3\xd6\x1d\x80\xac\x47\x88\x84\xa2\x8e\x86\x8b\xa9\xa0\x87\xac\x64\x88\x8b\x84\x4f",
            35: "\xd3\xd6\x1d\x80\xac\x47\x88\x84\xa2\x8e\x86\x8b\xa9\xa0\x87\xac\x64\x88\x8b\x84\x4f",
            36: "\xd3\xd6\x1d\xa4\x87\x84\xac\x40\xa5\xa2\x80\x4f\xac\xac\xac\xac\xac\xac\xac\xac\xac",
            37: "\xd3\xd6\x1d\x4b\x8e\x8b\x80\x0e\xa3\xac\x4b\x84\xa4\xa4\x84\xa2\x4f\xac\xac\xac\xac",
            38: "\xd3\xd6\x1d\x45\x80\xa4\x87\x84\xa2\x0e\xa3\xac\x49\x8e\xa5\xa2\x8d\x80\x8b\x4f\xac",
            39: "\xd3\xd6\x1d\xa4\x87\x84\xac\x42\xa2\xa9\xa3\xa4\x80\x8b\xac\x62\x88\x8d\x86\x4f\xac",
            40: "\xd3\xd6\x1d\x80\x8d\xac\x40\xa0\xa0\x8b\x84\x4f\xac\xac\xac\xac\xac\xac\xac\xac\xac",
            41: "\xd3\xd6\x1d\x80\x8d\xac\x47\x60\xac\x49\x84\xa7\x84\x8b\x4f\xac\xac\xac\xac\xac\xac",
            42: "\xd3\xd6\x1d\x80\xac\x43\x44\x45\xac\x49\x84\xa7\x84\x8b\x4f\xac\xac\xac\xac\xac\xac",
            43: "\xd3\xd6\x1d\x80\xac\x63\x64\x62\xac\x49\x84\xa7\x84\x8b\x4f\xac\xac\xac\xac\xac\xac",
            44: "\xd3\xd6\x1d\x80\xac\x4b\x88\x86\x87\xa4\xac\x49\x84\xa7\x84\x8b\x4f\xac\xac\xac\xac",
            45: "\xd3\xd6\x1d\x80\xac\x43\x80\xa2\x8a\xac\x49\x84\xa7\x84\x8b\x4f\xac\xac\xac\xac\xac",
            46: "\xd3\xd6\x1d\x22\xac\x62\x84\x83\xac\x49\x84\xa7\x84\x8b\xa3\x4f\xac\xac\xac\xac\xac",
            47: "\xd3\xd6\x1d\x23\xac\x62\x84\x83\xac\x49\x84\xa7\x84\x8b\xa3\x4f\xac\xac\xac\xac\xac",
            48: "",
            49: "",
            50: "",
            51: "",
            52: "",
            53: "",
            54: "",
            55: "",
            56: "",
            57: "",
            58: "",
            59: "",
            60: ""
        }

        # Define short item text for in-game format
        # Currently only used in Jeweler's inventory
        self.item_text_short = {
            0: "\x4d\x8e\xa4\x87\x88\x8d\x86\xac\xac\xac\xac\xac\xac",
            1: "\x62\x84\x83\xac\x49\x84\xa7\x84\x8b\xac\xac\xac\xac",
            2: "\x60\xa2\x88\xa3\x8e\x8d\xac\x4a\x84\xa9\xac\xac\xac",
            3: "\x48\x8d\x82\x80\xac\x63\xa4\x80\xa4\xa5\x84\xac\x40",
            4: "\x48\x8d\x82\x80\xac\x63\xa4\x80\xa4\xa5\x84\xac\x41",
            5: "",
            6: "\x47\x84\xa2\x81\xac\xac\xac\xac\xac\xac\xac\xac\xac",
            7: "\x43\x88\x80\x8c\x8e\x8d\x83\xac\x41\x8b\x8e\x82\x8a",
            8: "\x67\x88\x8d\x83\xac\x4c\x84\x8b\x8e\x83\xa9\xac\xac",
            9: "\x4b\x8e\x8b\x80\x0e\xa3\xac\x4c\x84\x8b\x8e\x83\xa9",
            10: "\x4b\x80\xa2\x86\x84\xac\x62\x8e\x80\xa3\xa4\xac\xac",
            11: "\x4c\x88\x8d\x84\xac\x4a\x84\xa9\xac\x40\xac\xac\xac",
            12: "\x4c\x88\x8d\x84\xac\x4a\x84\xa9\xac\x41\xac\xac\xac",
            13: "\x4c\x84\x8c\x8e\xa2\xa9\xac\x4c\x84\x8b\x8e\x83\xa9",
            14: "\x42\xa2\xa9\xa3\xa4\x80\x8b\xac\x41\x80\x8b\x8b\xac",
            15: "\x44\x8b\x84\xa6\x80\xa4\x8e\xa2\xac\x4a\x84\xa9\xac",
            16: "\x4c\xa5\xac\x60\x80\x8b\x80\x82\x84\xac\x4a\x84\xa9",
            17: "\x60\xa5\xa2\x88\xa4\xa9\xac\x63\xa4\x8e\x8d\x84\xac",
            18: "\x47\x8e\xa0\x84\xac\x63\xa4\x80\xa4\xa5\x84\xac\xac",
            19: "\x62\x80\x8c\x80\xac\x63\xa4\x80\xa4\xa5\x84\xac\xac",
            20: "\x4c\x80\x86\x88\x82\xac\x43\xa5\xa3\xa4\xac\xac\xac",
            21: "",
            22: "\x4b\x80\x8d\x82\x84\xac\x4b\x84\xa4\xa4\x84\xa2\xac",
            23: "\x4d\x84\x82\x8a\x8b\x80\x82\x84\xac\xac\xac\xac\xac",
            24: "\x67\x88\x8b\x8b\xac\xac\xac\xac\xac\xac\xac\xac\xac",
            25: "\x64\x84\x80\xa0\x8e\xa4\xac\xac\xac\xac\xac\xac\xac",
            26: "\x63\x87\xa2\x8e\x8e\x8c\xac\x43\xa2\x8e\xa0\xa3\xac",
            27: "",
            28: "\x41\x8b\x80\x82\x8a\xac\x46\x8b\x80\xa3\xa3\x84\xa3",
            29: "\x46\x8e\xa2\x86\x8e\x8d\xac\x45\x8b\x8e\xa7\x84\xa2",
            30: "\x47\x88\x84\xa2\x8e\x86\x8b\xa9\xa0\x87\xac\xac\xac",
            31: "\x47\x88\x84\xa2\x8e\x86\x8b\xa9\xa0\x87\xac\xac\xac",
            32: "\x47\x88\x84\xa2\x8e\x86\x8b\xa9\xa0\x87\xac\xac\xac",
            33: "\x47\x88\x84\xa2\x8e\x86\x8b\xa9\xa0\x87\xac\xac\xac",
            34: "\x47\x88\x84\xa2\x8e\x86\x8b\xa9\xa0\x87\xac\xac\xac",
            35: "\x47\x88\x84\xa2\x8e\x86\x8b\xa9\xa0\x87\xac\xac\xac",
            36: "\x40\xa5\xa2\x80\xac\xac\xac\xac\xac\xac\xac\xac\xac",
            37: "\x4b\x8e\x8b\x80\x0e\xa3\xac\x4b\x84\xa4\xa4\x84\xa2",
            38: "\x49\x8e\xa5\xa2\x8d\x80\x8b\xac\xac\xac\xac\xac\xac",
            39: "\x42\xa2\xa9\xa3\xa4\x80\x8b\xac\x62\x88\x8d\x86\xac",
            40: "\x40\xa0\xa0\x8b\x84\xac\xac\xac\xac\xac\xac\xac\xac",
            41: "\x47\x60\xac\x49\x84\xa7\x84\x8b\xac\xac\xac\xac\xac",
            42: "\x43\x44\x45\xac\x49\x84\xa7\x84\x8b\xac\xac\xac\xac",
            43: "\x63\x64\x62\xac\x49\x84\xa7\x84\x8b\xac\xac\xac\xac",
            44: "\x4b\x88\x86\x87\xa4\xac\x49\x84\xa7\x84\x8b\xac\xac",
            45: "\x43\x80\xa2\x8a\xac\x49\x84\xa7\x84\x8b\xac\xac\xac",
            46: "\x22\xac\x62\x84\x83\xac\x49\x84\xa7\x84\x8b\xa3\xac",
            47: "\x23\xac\x62\x84\x83\xac\x49\x84\xa7\x84\x8b\xa3\xac",
            48: "\xd6\x3c\x43\x80\xa3\x87",
            49: "\xd6\x3c\x63\x8b\x88\x83\x84\xa2",
            50: "\xd7\x31\x43\x80\xa3\x87",
            51: "\xd6\x0c\x45\xa2\x88\x80\xa2",
            52: "\xd6\x03\x41\x80\xa2\xa2\x88\x84\xa2",
            53: "\x44\x80\xa2\xa4\x87\xa1\xa5\x80\x8a\x84\xa2",
            54: "",
            55: "",
            56: "",
            57: "",
            58: "",
            59: "",
            60: ""
        }

        # Database of enemy groups and spritesets
        # FORMAT: { ID: [ROM_Loction, HeaderCode, HeaderData, Name]}
        self.enemysets = {
            0: ["\x03\x00\x10\x10\xEC\x59\xCD\x01\x04\x00\x60\xA0\x8C\x75\xDE\x10\xD0\x21\x00\x47\xED\x9F","Underground Tunnel"],
            1: ["\x03\x00\x10\x10\xBC\x33\xC2\x01\x04\x00\x60\xA0\x0C\x77\xDE\x10\x2A\x0F\x00\xE6\x08\xD5","Inca Ruins (Mud Monster and Larva)"],
            2: ["\x03\x00\x10\x10\x23\x4D\xC2\x01\x04\x00\x60\xA0\xCC\x77\xDE\x10\x36\x23\x00\x24\x45\xCC","Inca Ruins (Statues)"],
            3: ["\x03\x00\x10\x10\x16\x5C\xCC\x01\x04\x00\x60\xA0\xCC\x7A\xDE\x10\x30\x29\x00\xBE\x2F\xCB","Diamond Mine"],
            4: ["\x03\x00\x10\x10\x62\x3D\xCF\x01\x04\x00\x60\xA0\x4C\x7C\xDE\x10\x54\x1D\x00\xEF\xEE\x9E","Sky Garden (top)"],
            5: ["\x03\x00\x10\x10\x62\x3D\xCF\x01\x04\x00\x60\xA0\x0C\x7D\xDE\x10\x54\x1D\x00\xEF\xEE\x9E","Sky Garden (bottom)"],
            6: ["\x03\x00\x10\x10\x2D\x2E\xCC\x01\x04\x00\x60\xA0\x00\x00\xDF\x10\x16\x1C\x00\x41\x36\xD1","Mu"],
            7: ["\x03\x00\x10\x10\xD1\x14\xCF\x01\x04\x00\x60\xA0\x40\x02\xDF\x10\x7F\x0F\x00\x2C\x2B\xD5","Angel Dungeon"],
            8: ["\x03\x00\x10\x10\x6D\x13\xD0\x01\x04\x00\x60\xA0\x40\x05\xDF\x10\xFF\x16\x00\xF7\xF3\x99","Great Wall"],
            9: ["\x03\x00\x10\x10\x00\x00\xD0\x01\x04\x00\x60\xA0\x40\x08\xDF\x10\x70\x0E\x00\x5C\x4D\xD8","Mt. Kress"],
            10: ["\x03\x00\x10\x10\xEA\x15\xCE\x01\x04\x00\x70\x90\x53\x55\xDE\x10\xD5\x14\x00\x08\x73\xCC","Ankor Wat (outside)"],
            11: ["\x03\x00\x10\x10\x81\x6A\xC1\x01\x04\x00\x70\x90\x13\x57\xDE\x10\x57\x10\x00\x5F\x39\xD4","Ankor Wat (inside)"],
            12: ["\x03\x00\x10\x10\x0d\x18\xcb\x01\x04\x00\x60\x90\x80\x0a\xdf\x10\xfb\x13\x00\x0e\x67\xd1","Pyramid"],
            13: ["\x03\x00\x10\x10\x16\x5C\xCC\x01\x04\x00\x60\xA0\xC0\x0C\xDF\x10\x30\x29\x00\xBE\x2F\xCB","Jeweler's Mansion"]
        }


        # Enemy map database
        # FORMAT: { ID: [EnemySet, RewardBoss(0 for no reward), Reward, SearchHeader,
        #           SpritesetOffset,EventAddrLow,EventAddrHigh,RestrictedEnemysets]}
        # ROM address for room reward table is mapID + $1aade
        self.maps = {
            # For now, no one can have enemyset 10 (Ankor Wat outside)
            # Underground Tunnel
            12: [0,1,0,"\x0C\x00\x02\x05\x03",4,"c867a","c86ac",[]],
            13: [0,1,0,"\x0D\x00\x02\x03\x03",4,"c86ac","c875c",[0,1,2,3,4,5,7,8,9,11,12,13]],
            14: [0,1,0,"\x0E\x00\x02\x03\x03",4,"c875c","c8847",[0,1,2,3,4,5,7,8,9,11,12,13]],     # Weird 4way issues
            15: [0,1,0,"\x0F\x00\x02\x03\x03",4,"c8847","c8935",[0,1,2,3,4,5,6,7,8,9,11,12,13]],
            18: [0,1,0,"\x12\x00\x02\x03\x03",4,"c8986","c8aa9",[0,1,2,3,4,5,7,8,9,11,12,13]],  # Spike balls

            # Inca Ruins
            27: [1,0,0,"\x1B\x00\x02\x05\x03",4,"c8c33","c8c87",[0,1,2,3,4,5,6,7,8,9,10,11,12,13]],  # Moon Tribe cave
            29: [1,1,0,"\x1D\x00\x02\x0F\x03",4,"c8cc4","c8d85",[0,1,2,3,4,5,6,7,8,9,11,12,13]],
            32: [1,1,0,"\x20\x00\x02\x08\x03",4,"c8e16","c8e75",[]],  # Broken statue
            33: [2,1,0,"\x21\x00\x02\x08\x03",4,"c8e75","c8f57",[0,1,2,3,4,5,7,8,9,11,12,13]],  # Floor switch
            34: [2,1,0,"\x22\x00\x02\x08\x03",4,"c8f57","c9029",[]],  # Floor switch
            35: [2,1,0,"\x23\x00\x02\x0A\x03",4,"c9029","c90d5",[0,1,2,3,4,5,7,8,9,11,12,13]],
            37: [1,1,0,"\x25\x00\x02\x08\x03",4,"c90f3","c91a0",[1]],  # Diamond block
            38: [1,1,0,"\x26\x00\x02\x08\x03",4,"c91a0","c9242",[]],  # Broken statues
            39: [1,1,0,"\x27\x00\x02\x0A\x03",4,"c9242","c92f2",[0,1,2,3,4,5,6,7,8,9,11,12,13]],
            40: [1,1,0,"\x28\x00\x02\x08\x03",4,"c92f2","c935f",[1]],  # Falling blocks

            # Diamond Mine
            61: [3,2,0,"\x3D\x00\x02\x08\x03",4,"c9836","c98b7",[0,1,2,3,4,5,6,7,8,9,11,12,13]],
            62: [3,2,0,"\x3E\x00\x02\x08\x03",4,"c98b7","c991a",[]],
            63: [3,2,0,"\x3F\x00\x02\x05\x03",4,"c991a","c9a41",[]],
            64: [3,2,0,"\x40\x00\x02\x08\x03",4,"c9a41","c9a95",[0,1,2,3,4,5,6,7,8,9,11,12,13]],  # Trapped laborer (??)
            65: [3,2,0,"\x41\x00\x02\x00\x03",4,"c9a95","c9b39",[0,2,3,4,5,11]],  # Stationary Grundit
            69: [3,2,0,"\x45\x00\x02\x08\x03",4,"c9ba1","c9bf4",[]],
            70: [3,2,0,"\x46\x00\x02\x08\x03",4,"c9bf4","c9c5c",[3,13]],

            # Sky Garden
            77: [4,2,0,"\x4D\x00\x02\x12\x03",4,"c9db3","c9e92",[]],
            78: [5,2,0,"\x4E\x00\x02\x10\x03",4,"c9e92","c9f53",[]],
            79: [4,2,0,"\x4F\x00\x02\x12\x03",4,"c9f53","ca01a",[4,5]],
            80: [5,2,0,"\x50\x00\x02\x10\x03",4,"ca01a","ca0cb",[0,1,2,3,4,5,6,7,8,9,11,12,13]],
            81: [4,2,0,"\x51\x00\x02\x12\x03",4,"ca0cb","ca192",[0,1,2,3,4,5,6,7,8,9,11,12,13]],
            82: [5,2,0,"\x52\x00\x02\x10\x03",4,"ca192","ca247",[4,5]],
            83: [4,2,0,"\x53\x00\x02\x12\x03",4,"ca247","ca335",[4,5]],
            84: [5,2,0,"\x54\x00\x02\x12\x03",4,"ca335","ca43b",[4,5]],

            # Mu
#            92: [6,0,0,"\x5C\x00\x02\x15\x03",4,[]],  # Seaside Palace
            95: [6,3,0,"\x5F\x00\x02\x14\x03",4,"ca71b","ca7ed",[0,1,2,3,4,5,6,7,8,9,11,12,13]],
            96: [6,3,0,"\x60\x00\x02\x14\x03",4,"ca7ed","ca934",[6]],
            97: [6,3,0,"\x61\x00\x02\x14\x03",4,"ca934","caa7b",[6]],
            98: [6,3,0,"\x62\x00\x02\x14\x03",4,"caa7b","cab28",[0,1,2,3,4,5,6,7,8,9,11,12,13]],
            100: [6,3,0,"\x64\x00\x02\x14\x03",4,"cab4b","cabd4",[0,1,2,3,4,5,6,7,8,9,11,12,13]],
            101: [6,3,0,"\x65\x00\x02\x14\x03",4,"cabd4","cacc3",[6]],

            # Angel Dungeon
            109: [7,3,0,"\x6D\x00\x02\x16\x03",4,"caf6e","cb04b",[2,7,8,9,11]],  # Add 10's back in once flies are fixed
            110: [7,3,0,"\x6E\x00\x02\x18\x03",4,"cb04b","cb13e",[2,7,8,9,11]],
            111: [7,3,0,"\x6F\x00\x02\x1B\x03",4,"cb13e","cb1ae",[2,7,8,9,11]],
            112: [7,3,0,"\x70\x00\x02\x16\x03",4,"cb1ae","cb258",[2,7,8,9,11]],
            113: [7,3,0,"\x71\x00\x02\x18\x03",4,"cb258","cb29e",[2,7,8,9,11]],
            114: [7,3,0,"\x72\x00\x02\x18\x03",4,"cb29e","cb355",[2,7,8,9,11]],

            # Great Wall
            130: [8,4,0,"\x82\x00\x02\x1D\x03",4,"cb6c1","cb845",[2,7,8,9,11]],  # Add 10's back in once flies are fixed
            131: [8,4,0,"\x83\x00\x02\x1D\x03",4,"cb845","cb966",[2,7,8,9,11]],
            133: [8,4,0,"\x85\x00\x02\x1D\x03",4,"cb97d","cbb18",[2,7,8,9,11]],
            134: [8,4,0,"\x86\x00\x02\x1D\x03",4,"cbb18","cbb87",[2,7,8,9,11]],
            135: [8,4,0,"\x87\x00\x02\x1D\x03",4,"cbb87","cbc3b",[2,7,8,9]],
            136: [8,4,0,"\x88\x00\x02\x1D\x03",4,"cbc3b","cbd0a",[2,7,8,9,11]],

            # Mt Temple
            160: [9,4,0,"\xA0\x00\x02\x20\x03",4,"cc18c","cc21c",[]],
            161: [9,4,0,"\xA1\x00\x02\x20\x03",4,"cc21c","cc335",[]],
            162: [9,4,0,"\xA2\x00\x02\x20\x03",4,"cc335","cc3df",[]],
            163: [9,4,0,"\xA3\x00\x02\x20\x03",4,"cc3df","cc4f7",[]],
            164: [9,4,0,"\xA4\x00\x02\x20\x03",4,"cc4f7","cc5f8",[0,1,2,3,4,5,7,8,9,11,12,13]],
            165: [9,4,0,"\xA5\x00\x02\x20\x03",4,"cc5f8","cc703",[]],
            166: [9,4,0,"\xA6\x00\x02\x20\x03",4,"cc703","cc7a1",[]],
            167: [9,4,0,"\xA7\x00\x02\x20\x03",4,"cc7a1","cc9a3",[]],
            168: [9,4,0,"\xA8\x00\x02\x20\x03",4,"cc9a3","cca02",[]],

            # Ankor Wat
            176: [10,6,0,"\xB0\x00\x02\x2C\x03",4,"ccb1b","ccbd8",[]],
            177: [11,6,0,"\xB1\x00\x02\x08\x03",4,"ccbd8","ccca5",[0,1,2,3,4,5,7,8,9,11,12,13]],
            178: [11,6,0,"\xB2\x00\x02\x08\x03",4,"ccca5","ccd26",[0,1,2,3,4,5,7,8,9,11,12,13]],
            179: [11,6,0,"\xB3\x00\x02\x08\x03",4,"ccd26","ccd83",[]],
            180: [11,6,0,"\xB4\x00\x02\x08\x03",4,"ccd83","ccdd7",[0,1,2,3,4,5,7,8,9,11,12,13]],
            181: [11,6,0,"\xB5\x00\x02\x08\x03",4,"ccdd7","cce7b",[0,1,2,3,4,5,6,7,8,9,11,12,13]],
            182: [10,6,0,"\xB6\x00\x02\x2C\x03",4,"cce7b","cd005",[]],
            183: [11,6,0,"\xB7\x00\x02\x08\x03",4,"cd005","cd092",[0,1,2,3,4,5,6,7,8,9,11,12,13]],  # Earthquaker Golem
            184: [11,6,0,"\xB8\x00\x02\x08\x03",4,"cd092","cd0df",[0,1,2,3,4,5,7,8,9,11,12,13]],
            185: [11,6,0,"\xB9\x00\x02\x08\x03",4,"cd0df","cd137",[]],
            186: [10,6,0,"\xBA\x00\x02\x2C\x03",4,"cd137","cd197",[]],
            187: [11,6,0,"\xBB\x00\x02\x08\x03",4,"cd197","cd1f4",[]],
            188: [11,6,0,"\xBC\x00\x02\x24\x03",4,"cd1f4","cd29a",[0,1,2,3,4,5,6,7,8,9,11,12,13]],
            189: [11,6,0,"\xBD\x00\x02\x08\x03",4,"cd29a","cd339",[]],
            190: [11,6,0,"\xBE\x00\x02\x08\x03",4,"cd339","cd392",[]],

            # Pyramid
            204: [12,5,0,"\xCC\x00\x02\x08\x03",4,"cd539","cd58c",[]],
            206: [12,5,0,"\xCE\x00\x02\x08\x03",4,"cd5c6","cd650",[]],
            207: [12,5,0,"\xCF\x00\x02\x08\x03",4,"cd650","cd6f3",[0,1,2,3,4,5,6,7,8,9,10,11,12,13]],
            208: [12,5,0,"\xD0\x00\x02\x08\x03",4,"cd6f3","cd752",[]],
            209: [12,5,0,"\xD1\x00\x02\x08\x03",4,"cd752","cd81b",[]],
            210: [12,5,0,"\xD2\x00\x02\x08\x03",4,"cd81b","cd8f1",[]],
            211: [12,5,0,"\xD3\x00\x02\x08\x03",4,"cd8f1","cd9a1",[]],
            212: [12,5,0,"\xD4\x00\x02\x08\x03",4,"cd9a1","cda80",[]],
            213: [12,5,0,"\xD5\x00\x02\x08\x03",4,"cda80","cdb4b",[]],
            214: [12,5,0,"\xD6\x00\x02\x26\x03",4,"cdb4b","cdc1e",[0,1,2,3,4,5,6,7,8,9,11,12,13]],
            215: [12,5,0,"\xD7\x00\x02\x28\x03",4,"cdc1e","cdcfd",[0,2,3,4,5,6,8,9,11,12,13]],
            216: [12,5,0,"\xD8\x00\x02\x08\x03",4,"cdcfd","cde4f",[]],
            217: [12,5,0,"\xD9\x00\x02\x26\x03",4,"cde4f","cdf3c",[0,1,2,3,4,5,6,7,8,9,11,12,13]],
            219: [12,5,0,"\xDB\x00\x02\x26\x03",4,"cdf76","ce010",[0,1,2,3,4,5,6,7,8,9,11,12,13]],

            # Jeweler's Mansion
            233: [13,0,0,"\xE9\x00\x02\x22\x03",4,"ce224","ce3a6",[0,1,2,3,4,5,6,7,8,9,11,12,13]]

        }

        # Database of enemy types
        # FORMAT: { ID: [Enemyset, Event addr, VanillaTemplate,
        #           Type(1=stationary,2=walking,3=flying),OnWalkableTile,CanBeRandom,Name]}
        self.enemies = {
            # Underground Tunnel
            0: [0,"\x55\x87\x8a","\x05",2,True,True,"Bat"], # a8755
            1: [0,"\x6c\x82\x8a","\x01",2,True,True,"Ribber"],
            2: [0,"\x00\x80\x8a","\x02",1,False,True,"Canal Worm"],
            3: [0,"\xf7\x85\x8a","\x03",2,True,False,"King Bat"],
            4: [0,"\x76\x84\x8a","\x10",2,True,True,"Skull Chaser"],
            5: [0,"\xff\x86\x8a","\x04",2,True,False,"Bat Minion 1"],
            6: [0,"\x9a\x86\x8a","\x04",2,True,False,"Bat Minion 2"],
            7: [0,"\x69\x86\x8a","\x04",2,True,False,"Bat Minion 3"],
            8: [0,"\xcb\x86\x8a","\x04",2,True,False,"Bat Minion 4"],

            # Inca Ruins
            10: [1,"\xb7\x8d\x8a","\x0b",2,True,True,"Slugger"],
            11: [1,"\xb6\x8e\x8a","\x0b",2,True,False,"Scuttlebug"],
            12: [1,"\x1b\x8b\x8a","\x0a",2,True,True,"Mudpit"],
            13: [1,"\x70\x8c\x8a","\x0c",1,True,True,"Four Way"],
            14: [2,"\xee\x97\x8a","\x0f",2,True,True,"Splop"],
            15: [2,"\xbc\x98\x8a","\x0e",3,False,True,"Whirligig"],
            16: [2,"\xc2\x95\x8a","\x0d",2,True,False,"Stone Lord R"],  # shoots fire
            17: [2,"\xb3\x95\x8a","\x0d",2,True,True,"Stone Lord D"],  # shoots fire
            18: [2,"\xb8\x95\x8a","\x0d",2,True,False,"Stone Lord U"],  # shoots fire
            19: [2,"\xbd\x95\x8a","\x0d",2,True,False,"Stone Lord L"],  # shoots fire
            20: [2,"\x70\x90\x8a","\x0d",2,True,False,"Stone Guard R"], # throws spears
            21: [2,"\x6b\x90\x8a","\x0d",2,True,False,"Stone Guard L"], # throws spears
            22: [2,"\x61\x90\x8a","\x0d",2,True,True,"Stone Guard D"], # throws spears
            23: [2,"\xc3\x99\x8a","\x0e",1,False,False,"Whirligig (stationary)"],

            # Diamond Mine
            30: [3,"\xca\xaa\x8a","\x18",2,True,True,"Flayzer 1"],
            31: [3,"\x54\xaa\x8a","\x18",2,True,False,"Flayzer 2"],
            32: [3,"\x8a\xaa\x8a","\x18",2,True,False,"Flayzer 3"],
            33: [3,"\x03\xb1\x8a","\x19",2,True,True,"Eye Stalker"],
            34: [3,"\xb3\xb0\x8a","\x19",2,True,False,"Eye Stalker (stone)"],
            35: [3,"\xf5\xaf\x8a","\x1a",1,True,True,"Grundit"],
#            36: [3,"\xf5\xa4\x8a","\x1a","Grundit (stationary)"],  # Can't randomize this guy

            # Sky Garden
            40: [4,"\xb0\xb4\x8a","\x1d",2,True,True,"Blue Cyber"],
            41: [4,"\x20\xc5\x8a","\x1b",2,True,True,"Dynapede 1"],
            42: [4,"\x33\xc5\x8a","\x1b",2,True,False,"Dynapede 2"],
            43: [5,"\xb0\xb8\x8a","\x1e",2,True,True,"Red Cyber"],
            44: [5,"\x16\xc8\x8a","\x1c",2,True,True,"Nitropede"],

            # Mu
            50: [6,"\xcc\xe6\x8a","\x2b",2,True,True,"Slipper"],
            51: [6,"\x5c\xe4\x8a","\x2a",2,True,True,"Skuddle"],
            52: [6,"\x9e\xdd\x8a","\x28",2,True,True,"Cyclops"],
            53: [6,"\x6e\xe2\x8a","\x29",3,True,True,"Flasher"],
            54: [6,"\x07\xde\x8a","\x28",2,True,False,"Cyclops (asleep)"],
            55: [6,"\xf4\xe6\x8a","\x2b",2,True,True,"Slipper (falling)"],

            # Angel Dungeon
            60: [7,"\x9f\xee\x8a","\x2d",3,False,True,"Dive Bat"],
            61: [7,"\x51\xea\x8a","\x2c",2,True,True,"Steelbones"],
            62: [7,"\x33\xef\x8a","\x2e",1,True,True,"Draco"],   # False for now...
            63: [7,"\xc7\xf0\x8a","\x2e",1,True,True,"Ramskull"],

            # Great Wall
            70: [8,"\x55\x91\x8b","\x33",2,True,True,"Archer 1"],
            71: [8,"\xfe\x8e\x8b","\x33",2,True,False,"Archer Statue"],
            72: [8,"\xbe\x8d\x8b","\x34",2,True,True,"Eyesore"],
            73: [8,"\x70\x8c\x8b","\x35",3,False,True,"Fire Bug 1"],
            74: [8,"\x70\x8c\x8b","\x33",3,False,False,"Fire Bug 2"],
            75: [8,"\x23\x94\x8b","\x32",2,True,True,"Asp"],
            76: [8,"\x65\x91\x8b","\x33",2,True,False,"Archer 2"],
            77: [8,"\x77\x91\x8b","\x33",2,True,False,"Archer 3"],
            78: [8,"\x72\x8f\x8b","\x46",2,True,False,"Archer Statue (switch) 1"],
            79: [8,"\x4f\x8f\x8b","\x33",2,True,False,"Archer Statue (switch) 2"],

            # Mt. Kress
            80: [9,"\xac\x9b\x8b","\x3e",3,True,True,"Skulker (N/S)"],
            81: [9,"\x4e\x9c\x8b","\x3e",3,True,True,"Skulker (E/W)"],
            82: [9,"\x44\x9c\x8b","\x3e",3,True,False,"Skulker (E/W)"],
            83: [9,"\xa2\x9b\x8b","\x3e",3,True,False,"Skulker (E/W)"],
            84: [9,"\x8b\x9e\x8b","\x3d",3,False,True,"Yorrick (E/W)"],
            85: [9,"\x53\x9f\x8b","\x3d",3,False,False,"Yorrick (E/W)"],
            86: [9,"\x0f\x9d\x8b","\x3d",3,False,True,"Yorrick (N/S)"],
            87: [9,"\xcd\x9d\x8b","\x3d",3,False,False,"Yorrick (N/S)"],
            88: [9,"\x3b\x98\x8b","\x3f",3,False,True,"Fire Sprite"],
            89: [9,"\xcf\xa0\x8b","\x3c",2,True,True,"Acid Splasher"],
            90: [9,"\xa1\xa0\x8b","\x3c",2,True,False,"Acid Splasher (stationary E)"],
            91: [9,"\x75\xa0\x8b","\x3c",2,True,False,"Acid Splasher (stationary W)"],
            92: [9,"\x49\xa0\x8b","\x3c",2,True,False,"Acid Splasher (stationary S)"],
            93: [9,"\x1d\xa0\x8b","\x3c",2,True,False,"Acid Splasher (stationary N)"],

            # Ankor Wat
            100: [10,"\xd7\xb1\x8b","\x49",2,True,True,"Shrubber"],
            101: [10,"\xb4\xb1\x8b","\x49",2,True,False,"Shrubber 2"],
            102: [10,"\x75\xb2\x8b","\x46",2,True,True,"Zombie"],
            103: [10,"\x4f\xaf\x8b","\x4a",3,True,True,"Zip Fly"],    # False for now...
            104: [11,"\x8d\xbd\x8b","\x42",3,True,True,"Goldcap"],
            105: [11,"\x25\xb8\x8b","\x45",2,True,True,"Gorgon"],
            106: [11,"\x17\xb8\x8b","\x45",2,True,False,"Gorgon (jump down)"],
            107: [11,"\xbb\xbf\x8b","\x43",2,True,False,"Frenzie"],
            108: [11,"\xd0\xbf\x8b","\x43",2,True,True,"Frenzie 2"],
            109: [11,"\x66\xbb\x8b","\x44",1,False,True,"Wall Walker"],
            110: [11,"\x66\xbb\x8b","\x3a",1,False,False,"Wall Walker 2"],
            111: [11,"\x5c\xbb\x8b","\x44",1,False,False,"Wall Walker 3"],
            112: [11,"\x5c\xbb\x8b","\x3a",1,False,False,"Wall Walker 4"],
            113: [11,"\xaf\x99\x88","\x45",2,True,False,"Gorgon (block)"],

            # Pyramid
            120: [12,"\x5f\xc6\x8b","\x4f",1,True,True,"Mystic Ball (stationary)"],
            121: [12,"\xfc\xc5\x8b","\x4f",2,True,True,"Mystic Ball"],
            122: [12,"\xa3\xc5\x8b","\x4f",2,True,True,"Mystic Ball"],
            123: [12,"\x9d\xc3\x8b","\x4e",2,True,True,"Tuts"],
            124: [12,"\x98\xc7\x8b","\x51",1,True,True,"Blaster"],
            125: [12,"\x84\xc1\x8b","\x4c",2,True,False,"Haunt (stationary)"],
            126: [12,"\xa7\xc1\x8b","\x4c",2,True,True,"Haunt"],

            # Babel Tower
#            130: [14,"\xd7\x99\x8a","\x5a","Castoth (boss)"],
#            131: [14,"\xd5\xd0\x8a","\x5b","Viper (boss)"],
#            132: [14,"\x50\xf1\x8a","\x5c","Vampire (boss)"],
#            133: [14,"\x9c\xf1\x8a","\x5c","Vampire (boss)"],
#            134: [14,"\x00\x80\x8b","\x5d","Sand Fanger (boss)"],
#            135: [14,"\x1a\xa6\x8b","\x5e","Mummy Queen (boss)"],

            # Jeweler's Mansion
            140: [13,"\xca\xaa\x8a","\x61",2,True,True,"Flayzer"],
            141: [13,"\xf5\xaf\x8a","\x63",1,True,True,"Grundit"],
            142: [13,"\xd8\xb0\x8a","\x62",2,True,False,"Eye Stalker 1"],
            143: [13,"\x03\xb1\x8a","\x62",2,True,True,"Eye Stalker 2"]

            # Bosses
#            24: [15,"\x03\x9b\x8a","\x14","Castoth (boss)"],
#            45: [15,"\x6f\xd1\x8a","\x27","Viper (boss)"],
#            55: [15,"\xf7\xf1\x8a","\x2f","Vampire (boss)"],
#            56: [15,"\xc8\xf3\x8a","\x30","Vampire (boss)"],
#            79: [15,"\x5c\x81\x8b","\x36","Sand Fanger (boss)"],
#            128: [15,"\xb6\xa6\x8b","\x50","Mummy Queen (boss)"],
#            143: [15,"\x09\xf7\x88","\x5f","Solid Arm (boss)"],
#            140: [15,"\xaa\xee\x8c","\x54","Dark Gaia"]

        }


        # Database of non-enemy sprites to disable in enemizer
        # FORMAT: { ID: [Enemyset, Event addr, Name]}
        self.nonenemy_sprites = {
            # Underground Tunnel
            0: [0,"a8835","Movable statue"],
            1: [0,"a87ce","Falling spear 1"],
            2: [0,"a87c3","Falling spear 2"],
            3: [0,"a8aae","Spike ball 1"],
            4: [0,"a8a0f","Spike ball 2"],
            5: [0,"a8a7d","Spike ball 3"],
            6: [0,"a8a46","Spike ball 4"],
            7: [0,"a89de","Spike ball 5"],

            # Inca Ruins
            10: [1,"9c26f","Skeleton 1"],
            11: [1,"9c798","Skeleton 2"],
#            12: [1,"9c89d","Skeleton 3"],   # Spriteset already restricted for this room
            13: [1,"9c8f7","Skeleton 4"],
            14: [1,"a8896","Broken statue (chest)"],
            15: [1,"a88de","Broken statue (blockade)"],

            # Diamond Mine
            20: [3,"5d6a8","Elevator sign"],
            21: [3,"aa4f5","Elevator platform 1"],
            22: [3,"aa50c","Elevator platform 2"],
            23: [3,"aa4e2","Elevator platform 3"],

            # Sky Garden
            30: [4,"5f8c0","Broken statue"],
            31: [4,"ac0fe","Sword statue 1"],
#            32: [4,"ac150","Sword statue 2"],
            33: [4,"ac3b3","Sword statue 3"],
#            34: [4,"ac409","Sword statue 4"],
            35: [4,"accd4","Fire snake (top)"],
            36: [5,"accf1","Fire snake (bottom)"],

            # Mu
            40: [6,"69ce9","Floor spikes 1"],
            41: [6,"69d1f","Floor spikes 2"],
            42: [6,"ae943","Fire snake"],
#            43: [6,"69d4d","Donut"],

            # Angel
            50: [7,"6d56f","Flame 1"],
            51: [7,"6d57e","Flame 2"],
            52: [7,"6d58f","Flame 3"],

            # Great Wall
            60: [8,"b8c30","Wall spike 1"],
            61: [8,"b8bf8","Wall spike 2"],
            62: [8,"7bd17","Wall spike 3"],
            63: [8,"7bd46","Wall spike 4"],
            64: [8,"7bd75","Wall spike 5"],
            65: [8,"7bce8","Wall spike 5"],

            # Mt Kress (nothing)

            # Ankor Wat
            80: [11,"89f2c","Floating crystal"],
            81: [11,"89ffc","Skeleton 1"],
            82: [11,"8a25e","Skeleton 2"]

            # Pyramid
#            90: [12,"8b6a2","Warp point"],
#            91: [12,"8cd6c","Warp point"],

            # Jeweler's Mansion (nothing)

        }
