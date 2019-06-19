from datetime import datetime
import binascii
import random
import quintet_text

MAX_INVENTORY = 15
PROGRESS_ADJ = [1.5, 1.25, 1, 1]   # Required items are more likely to be placed in easier modes

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
                        self.unfill_item(loc)
                        unfilled.append(loc)
                        done = True
                    elif not inv and self.graph[region][0] and self.item_pool[item][5] != 1:
                        self.unfill_item(loc)
                        unfilled.append(loc)
                        done = True
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
        to_visit = [0]
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
    def random_fill(self,items=[],item_locations=[]):
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
                    location_type = self.item_locations[dest][1]
                    filled = self.item_locations[dest][2]
                    restrictions = self.item_locations[dest][4]
                    if not filled and item_type == location_type and item not in restrictions:
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
                            self.placement_log.append([item,dest])
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

        # Chaos mode
        if self.logic_mode == "Chaos":
            # Add "Inaccessible" node to graph
            self.graph[71] = [False,[],"Inaccessible",[]]

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
        if self.item_locations[93][3] in abilities:         # Great Wall
            self.graph[100] = [False,[],"Great Wall - Behind Spin",[]]
            self.logic[200] = [45,100,[[50,1]]]
            self.item_locations[94][0] = 100
            if self.item_locations[94][3] in abilities:
                inaccessible += [95]
        if self.item_locations[122][3] in abilities:        # Ankor Wat
            inaccessible += [117,118,119,120,121]
        if self.item_locations[142][3] in abilities:        # Pyramid
            inaccessible += [133,134,136,139,140]

        # Change graph node for inaccessible locations
        for x in inaccessible:
            self.item_locations[x][0] = 71

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
    def randomize(self):
        self.initialize()

        solved = False

        random.seed(self.seed)

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
        if self.mode == 1:
            non_prog_items += [52]
        elif self.mode == 2:
            non_prog_items += [49,50,52,53]
        else:
            non_prog_items += self.list_item_pool(2)

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

        #while self.unaccessible_locations(item_locations):
        while not done:
            start_items = self.traverse()
            #print "We found these: ",start_items

            inv_size = len(self.get_inventory(start_items))
            if inv_size > MAX_INVENTORY:
                print "ERROR: Inventory capacity exceeded"

            # Get list of new progression options
            progression_list = self.progression_list(start_items)

            if progression_list == -1:       # No empty locations available
                removed = self.make_room(item_locations)
                if not removed:
                    print "ERROR: Could not remove non-progression item"
                    return False
                progression_list = []
            elif progression_list == -2:     # All new locations have too many inventory items
                removed = self.make_room(item_locations,True)
                if not removed:
                    print "ERROR: Could not remove inventory item"
                    return False
                progression_list = []

            #print "To progress: ",progression_list

            # Check for finished state, or dead-end state
            goal = ((self.goal == "Dark Gaia" and self.graph[70][0]) or
                (self.goal == "Red Jewel Hunt" and self.graph[68][0]))

            done = goal and (self.logic_mode != "Completable" or not progression_list)
            #print done, progression_list

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
        self.random_fill(junk_items,item_locations)

        placement_log = self.placement_log[:]
        random.shuffle(placement_log)
        self.in_game_spoilers(placement_log)

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
        f.seek(int("8b21b",16)+rom_offset)
        f.write(self.item_text_short[item1])
        f.write("\xcb")
        f.write(self.item_text_short[item2])
        f.write("\xc0")

        # Write in-game spoilers
        i = 0
        for addr in self.spoiler_addresses:
            f.seek(int(self.spoiler_addresses[addr],16)+rom_offset)
            if i < len(self.spoilers):
                f.write(self.spoilers[i])
                i += 1

        #self.enemize(f,rom_offset)
        #print "ROM successfully created"

    # Shuffle enemies in ROM
    def enemize(self,f,rom_offset=0):
        # Make all spritesets equal to Underground Tunnel
        for set in self.spritesets:
            f.seek(int(self.spritesets[set][0],16)+rom_offset)
            f.write(self.spritesets[0][1])

        # Turn all enemies into bats
        f.seek(0)
        rom = f.read()
        for enemy in self.enemies:
            #print self.enemies[enemy][3]
            done = False
            addr = int("c8200",16) + rom_offset
            while not done:
                addr = rom.find(self.enemies[enemy][1] + self.enemies[enemy][2],addr+1)
                if addr < 0 or addr > int("ce5e4",16)+rom_offset:
                    done = True
                else:
                    f.seek(addr)
                    #print addr
                    f.write("\x55\x87\x8a\x05")
                    #print " ", addr, hex(addr), binascii.hexlify(f.read(4))

    # Build world
    def __init__(self, seed, mode, goal="Dark Gaia", logic_mode="Completable",
        statues=[1,2,3,4,5,6],kara=3,gem=[3,5,8,12,20,30,50],incatile=[9,5],hieroglyphs=[1,2,3,4,5,6]):

        self.seed = seed
        self.statues = statues
        self.goal = goal
        self.logic_mode = logic_mode
        self.kara = kara
        self.gem = gem
        self.incatile = incatile
        self.hieroglyphs = hieroglyphs
        self.mode = mode
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
        self.item_locations = {
            0: [1,1,False,0,[],"8d019","8d19d","","8d260",      "Jeweler Reward 1                    "],
            1: [2,1,False,0,[],"8d028","8d1ba","","8d274",      "Jeweler Reward 2                    "],
            2: [3,1,False,0,[],"8d037","8d1d7","","8d288",      "Jeweler Reward 3                    "],
            3: [4,1,False,0,[],"8d04a","8d1f4","","8d29c",      "Jeweler Reward 4                    "],
            4: [5,1,False,0,[],"8d059","8d211","","8d2b0",      "Jeweler Reward 5                    "],
            5: [6,1,False,0,[],"8d069","8d2ea","","8d2c4",      "Jeweler Reward 6                    "],

            6: [0,1,False,0,[],"F51D","F52D","F543","",         "South Cape: Bell Tower              "],
            7: [0,1,False,0,[],"4846e","48479","","",           "South Cape: Fisherman               "], #text2 was 0c6a1
            8: [0,1,False,0,[],"F59D","F5AD","F5C3","",         "South Cape: Lance's House           "],
            9: [0,1,False,0,[],"499e4","49be5","","",           "South Cape: Lola                    "],
            10: [0,2,False,0,[51,52,53],"c830a","","","\x01",   "South Cape: Dark Space              "],

            11: [7,1,False,0,[],"4c214","4c299","","",          "Edward's Castle: Hidden Guard       "],
            12: [7,1,False,0,[],"4d0ef","4d141","","",          "Edward's Castle: Basement           "],

            13: [8,1,False,0,[],"4d32f","4d4b1","","",          "Edward's Prison: Hamlet             "], #text 4d5f4?
            14: [8,2,False,0,[51,52,53],"c8637","","","\x0b",   "Edward's Prison: Dark Space         "],

            15: [9,1,False,0,[2],"1AFA9","","","",              "Underground Tunnel: Spike's Chest   "],
            16: [9,1,False,0,[2],"1AFAE","","","",              "Underground Tunnel: Small Room Chest"],
            17: [10,1,False,0,[2],"1AFB3","","","",             "Underground Tunnel: Ribber's Chest  "],
            18: [10,1,False,0,[],"F61D","F62D","F643","",       "Underground Tunnel: Barrels         "],
            19: [10,2,True,0,[],"c8aa2","","","\x12",           "Underground Tunnel: Dark Space      "],   # Always open

            20: [12,1,False,0,[9],"F69D","F6AD","F6C3","",      "Itory Village: Logs                 "],
            21: [13,1,False,0,[9],"4f375","4f38d","4f3a8","",   "Itory Village: Cave                 "],
            22: [12,2,False,0,[51,52,53],"c8b34","","","\x15",  "Itory Village: Dark Space           "],

            23: [14,1,False,0,[],"4fae1","4faf9","4fb16","",    "Moon Tribe: Cave                    "],

            24: [15,1,False,0,[],"1AFB8","","","",              "Inca Ruins: Diamond-Block Chest     "],
            25: [16,1,False,0,[7],"1AFC2","","","",             "Inca Ruins: Broken Statues Chest    "],
            26: [16,1,False,0,[7],"1AFBD","","","",             "Inca Ruins: Stone Lord Chest        "],
            27: [16,1,False,0,[7],"1AFC6","","","",             "Inca Ruins: Slugger Chest           "],
            28: [16,1,False,0,[7],"9c5bd","9c614","9c637","",   "Inca Ruins: Singing Statue          "],
            29: [16,2,True,0,[],"c9302","","","\x28",           "Inca Ruins: Dark Space 1            "],   # Always open
            30: [16,2,False,0,[],"c923b","","","\x26",          "Inca Ruins: Dark Space 2            "],
            31: [17,2,False,0,[],"c8db8","","","\x1e",          "Inca Ruins: Final Dark Space        "],

            32: [19,1,False,0,[3,4,7,8],"5965e","5966e","","",  "Gold Ship: Seth                     "],

            33: [20,1,False,0,[],"F71D","F72D","F743","",       "Diamond Coast: Jar                  "],

            34: [21,1,False,0,[],"F79D","F7AD","F7C3","",       "Freejia: Hotel                      "],
            35: [21,1,False,0,[],"5b6d8","5b6e8","","",         "Freejia: Creepy Guy                 "],
            36: [21,1,False,0,[],"5cf9e","5cfae","5cfc4","",    "Freejia: Trash Can 1                "],
            37: [21,1,False,0,[],"5cf3d","5cf49","","",         "Freejia: Trash Can 2                "], #text2 was 5cf5b
            38: [21,1,False,0,[],"5b8b7","5b962","5b9ee","",    "Freejia: Snitch                     "], #text1 was @5b94d
            39: [21,2,False,0,[51,52,53],"c96ce","","","\x34",  "Freejia: Dark Space                 "],

            40: [22,1,False,0,[],"1AFD0","","","",              "Diamond Mine: Chest                 "],
            41: [23,1,False,0,[],"5d7e4","5d819","5d830","",    "Diamond Mine: Trapped Laborer       "],
            42: [24,1,False,0,[],"aa777","aa85c","","",         "Diamond Mine: Laborer w/Elevator Key"], #text1 was aa811
            43: [25,1,False,0,[15],"5d4d2","5d4eb","5d506","",  "Diamond Mine: Morgue                "],
            44: [25,1,False,0,[15],"aa757","aa7ef","","",       "Diamond Mine: Laborer w/Mine Key    "], #text1 was aa7b4
            45: [26,1,False,0,[11,12,15],"5d2b0","5d2da","","", "Diamond Mine: Sam                   "],
            46: [22,2,False,0,[],"c9a87","","","\x40",          "Diamond Mine: Appearing Dark Space  "], # Always open
            47: [22,2,False,0,[],"c98b0","","","\x3d",          "Diamond Mine: Dark Space at Wall    "],
            48: [23,2,False,0,[],"c9b49","","","\x42",          "Diamond Mine: Dark Space behind Wall"],

            49: [29,1,False,0,[],"1AFDD","","","",              "Sky Garden: (NE) Platform Chest     "],
            50: [29,1,False,0,[],"1AFD9","","","",              "Sky Garden: (NE) Blue Cyber Chest   "],
            51: [29,1,False,0,[],"1AFD5","","","",              "Sky Garden: (NE) Statue Chest       "],
            52: [30,1,False,0,[],"1AFE2","","","",              "Sky Garden: (SE) Dark Side Chest    "],
            53: [31,1,False,0,[],"1AFE7","","","",              "Sky Garden: (SW) Ramp Chest         "],
            54: [29,1,False,0,[],"1AFEC","","","",              "Sky Garden: (SW) Dark Side Chest    "],
            55: [30,1,False,0,[],"1AFF1","","","",              "Sky Garden: (NW) Top Chest          "],
            56: [30,1,False,0,[],"1AFF5","","","",              "Sky Garden: (NW) Bottom Chest       "],
            57: [29,2,False,0,[51,52,53],"c9d63","","","\x4c",  "Sky Garden: Dark Space (Foyer)      "],
            58: [29,2,False,0,[],"ca505","","","\x56",          "Sky Garden: Dark Space (SE)         "], #in the room
            59: [29,2,False,0,[],"ca173","","","\x51",          "Sky Garden: Dark Space (SW)         "],
            60: [29,2,False,0,[],"ca422","","","\x54",          "Sky Garden: Dark Space (NW)         "],

            61: [33,1,False,0,[],"1AFFF","","","",              "Seaside Palace: Side Room Chest     "],
            62: [33,1,False,0,[],"1AFFA","","","",              "Seaside Palace: First Area Chest    "],
            63: [33,1,False,0,[],"1B004","","","",              "Seaside Palace: Second Area Chest   "],
            64: [34,1,False,0,[17],"68af7","68ea9","68f02","",  "Seaside Palace: Buffy               "],
            65: [35,1,False,0,[9,23],"6922d","6939e","693b7","","Seaside Palace: Coffin              "], #text1 was 69377
            66: [33,2,False,0,[51,52,53],"ca574","","","\x5a",  "Seaside Palace: Dark Space          "],

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
            77: [42,2,False,0,[51,52,53],"caf67","","","\x6c",  "Angel Village: Dark Space           "],

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
            88: [44,2,False,0,[51,52,53],"cb644","","","\x7c",  "Watermia: Dark Space                "],

            89: [45,1,False,0,[],"7b5c5","7b5d1","","",         "Great Wall: Necklace 1              "],
            90: [45,1,False,0,[],"7b625","7b631","","",         "Great Wall: Necklace 2              "],
            91: [45,1,False,0,[],"1B033","","","",              "Great Wall: Chest 1                 "],
            92: [45,1,False,0,[],"1B038","","","",              "Great Wall: Chest 2                 "],
            93: [45,2,False,0,[],"cbb11","","","\x85",          "Great Wall: Archer Dark Space       "],
            94: [45,2,True,0,[],"cbb80","","","\x86",           "Great Wall: Platform Dark Space     "],   # Always open
            95: [46,2,False,0,[51],"cbc60","","","\x88",        "Great Wall: Appearing Dark Space    "],

            96: [48,1,False,0,[],"FA1D","FA2D","FA43","",       "Euro: Alley                         "],
            97: [48,1,False,0,[],"7c0b3","7c0f3","","",         "Euro: Apple Vendor                  "],
            98: [48,1,False,0,[],"7e51f","7e534","7e54a","",    "Euro: Hidden House                  "],
            99: [48,1,False,0,[],"7cd12","7cd39","7cd9b","",    "Euro: Store Item 1                  "],
            100: [48,1,False,0,[],"7cdf9","7ce28","7ce3e","",   "Euro: Store Item 2                  "], #text2 was 7cedd
            101: [48,1,False,0,[],"FA9D","FAAD","FAC3","",      "Euro: Laborer Room                  "],
            102: [49,1,False,0,[40],"7df58","7e10a","","",      "Euro: Ann                           "],
            103: [48,2,False,0,[51,52,53],"cc0b0","","","\x99", "Euro: Dark Space                    "],

            104: [50,1,False,0,[],"1B03D","","","",             "Mt. Temple: Red Jewel Chest         "],
            105: [50,1,False,0,[],"1B042","","","",             "Mt. Temple: Drops Chest 1           "],
            106: [51,1,False,0,[],"1B047","","","",             "Mt. Temple: Drops Chest 2           "],
            107: [52,1,False,0,[],"1B04C","","","",             "Mt. Temple: Drops Chest 3           "],
            108: [53,1,False,0,[26],"1B051","","","",           "Mt. Temple: Final Chest             "],
            109: [50,2,False,0,[50],"cc24f","","","\xa1",       "Mt. Temple: Dark Space 1            "],
            110: [50,2,False,0,[50],"cc419","","","\xa3",       "Mt. Temple: Dark Space 2            "],
            111: [52,2,False,0,[50],"cc7b8","","","\xa7",       "Mt. Temple: Dark Space 3            "],

            112: [54,1,False,0,[],"FB1D","FB2D","FB43","",      "Natives' Village: Statue Room       "],
            113: [55,1,False,0,[29],"893af","8942a","","",      "Natives' Village: Statue            "],
            114: [54,2,False,0,[51,52,53],"cca37","","","\xac", "Natives' Village: Dark Space        "],

            115: [56,1,False,0,[],"1B056","","","",              "Ankor Wat: Ramp Chest               "],
            116: [57,1,False,0,[],"1B05B","","","",              "Ankor Wat: Flyover Chest            "],
            117: [59,1,False,0,[],"1B060","","","",              "Ankor Wat: U-Turn Chest             "],
            118: [60,1,False,0,[28],"1B065","","","",            "Ankor Wat: Drop Down Chest          "],
            119: [60,1,False,0,[28],"1B06A","","","",            "Ankor Wat: Forgotten Chest          "],
            120: [59,1,False,0,[],"89fa3","89fbb","","",         "Ankor Wat: Glasses Location         "], #slow text @89fdc
            121: [60,1,False,0,[28],"89adc","89af1","89b07","",  "Ankor Wat: Spirit                   "], #item was 89b0d, text was 89e2e
            122: [57,2,True,0,[49,50],"cce92","","","\xb6",      "Ankor Wat: Garden Dark Space        "],    # Always open
            123: [58,2,False,0,[49,50,51],"cd0a2","","","\xb8",  "Ankor Wat: Earthquaker Dark Space   "],
            124: [60,2,True,0,[49,50,51,53],"cd1a7","","","\xbb","Ankor Wat: Drop Down Dark Space     "],   # Always open

            125: [61,1,False,0,[],"8b1b0","","","",              "Dao: Entrance Item 1                "],
            126: [61,1,False,0,[],"8b1b5","","","",              "Dao: Entrance Item 2                "],
            127: [61,1,False,0,[],"FB9D","FBAD","FBC3","",       "Dao: East Grass                     "],
            128: [61,1,False,0,[],"8b016","8b073","8b090","",    "Dao: Snake Game                     "],
            129: [61,2,False,0,[51,52,53],"cd3d0","","","\xc3",  "Dao: Dark Space                     "],

            130: [62,1,False,0,[],"8dcb7","8e66c","8e800","",    "Pyramid: Dark Space Top             "], #text2 was 8e800
            131: [63,1,False,0,[36],"FC1D","FC2D","FC43","",     "Pyramid: Under Stairs               "],
            132: [64,1,False,0,[36],"8c7b2","8c7c9","","",       "Pyramid: Hieroglyph 1               "],
            133: [63,1,False,0,[36],"1B06F","","","",            "Pyramid: Room 2 Chest               "],
            134: [63,1,False,0,[36],"8c879","8c88c","","",       "Pyramid: Hieroglyph 2               "],
            135: [64,1,False,0,[36],"1B079","","","",            "Pyramid: Room 3 Chest               "],
            136: [63,1,False,0,[36],"8c921","8c934","","",       "Pyramid: Hieroglyph 3               "],
            137: [64,1,False,0,[36],"1B07E","","","",            "Pyramid: Room 4 Chest               "],
            138: [64,1,False,0,[36],"8c9c9","8c9dc","","",       "Pyramid: Hieroglyph 4               "],
            139: [63,1,False,0,[36],"1B074","","","",            "Pyramid: Room 5 Chest               "],
            140: [63,1,False,0,[36],"8ca71","8ca84","","",       "Pyramid: Hieroglyph 5               "],
            141: [63,1,False,0,[36],"8cb19","8cb2c","","",       "Pyramid: Hieroglyph 6               "],
            142: [63,2,True,0,[],"cd570","","","\xcc",           "Pyramid: Dark Space Bottom          "],   # Always open

            143: [66,1,False,0,[],"FC9D","FCAD","FCC3","",       "Babel: Pillow                       "],
            144: [66,1,False,0,[],"99a4f","99ae4","99afe","",    "Babel: Force Field                  "], #item was  99a61
            145: [66,2,False,0,[51,52,53],"ce09b","","","\xdf",  "Babel: Dark Space Bottom            "],
            146: [67,2,False,0,[51,52,53],"ce160","","","\xe3",  "Babel: Dark Space Top               "],

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
            0: [False,[7,14,15],"South Cape",[9]],

            1: [False,[],"Jeweler Reward 1",[]],
            2: [False,[],"Jeweler Reward 2",[]],
            3: [False,[],"Jeweler Reward 3",[]],
            4: [False,[],"Jeweler Reward 4",[]],
            5: [False,[],"Jeweler Reward 5",[]],
            6: [False,[],"Jeweler Reward 6",[]],

            7: [False,[8],"Edward's Castle",[]],
            8: [False,[],"Edward's Prison",[2]],
            9: [False,[],"Underground Tunnel - Behind Prison Key",[]],
            10: [False,[],"Underground Tunnel - Behind Lilly",[]],
            12: [False,[],"Itory Village",[23]],
            13: [False,[],"Itory Cave",[]],
            14: [False,[],"Moon Tribe",[25]],
            15: [False,[],"Inca Ruins",[7]],
            16: [False,[],"Inca Ruins - Behind Diamond Tile & Psycho Dash",[8]],
            17: [False,[],"Inca Ruins - Behind Wind Melody",[3,4]],
            18: [False,[19],"Inca Ruins - Castoth",[]],
            19: [False,[20],"Gold Ship",[]],

            20: [False,[21,22,27,28],"Diamond Coast",[]],
            21: [False,[],"Freejia",[]],
            22: [False,[],"Diamond Mine",[15]],
            23: [False,[],"Diamond Mine - Behind Psycho Dash",[]],
            24: [False,[],"Diamond Mine - Behind Dark Friar",[]],
            25: [False,[],"Diamond Mine - Behind Elevator Key",[11,12]],
            26: [False,[],"Diamond Mine - Behind Mine Keys",[]],
            27: [False,[20,21,22,28],"Neil's Cottage",[13]],
            28: [False,[20,21,22,27,29],"Nazca Plain",[]],
            29: [False,[],"Sky Garden",[14,14,14,14]],
            30: [False,[],"Sky Garden - Behind Dark Friar",[]],
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
            42: [False,[36,44,45],"Angel Village",[]],
            43: [False,[],"Angel Village Dungeon",[]],
            44: [False,[42,45],"Watermia",[24]],
            45: [False,[],"Great Wall",[]],
            46: [False,[],"Great Wall - Behind Dark Friar",[]],
            47: [False,[],"Great Wall - Sand Fanger",[]],

            48: [False,[54,56],"Euro",[24,40]],
            49: [False,[],"Euro - Ann's Item",[]],
            50: [False,[],"Mt. Temple",[26]],
            51: [False,[],"Mt. Temple - Behind Drops 1",[26]],
            52: [False,[],"Mt. Temple - Behind Drops 2",[26]],
            53: [False,[],"Mt. Temple - Behind Drops 3",[]],
            54: [False,[48,56],"Natives' Village",[10,29]],
            55: [False,[],"Natives' Village - Statue Item",[]],
            56: [False,[],"Ankor Wat",[]],
            57: [False,[],"Ankor Wat - Behind Psycho SLide & Spin Dash",[]],
            58: [False,[],"Ankor Wat - Behind Dark Friar",[]],
            59: [False,[],"Ankor Wat - Behind Earthquaker",[]],
            60: [False,[],"Ankor Wat - Behind Black Glasses",[]],

            61: [False,[],"Dao",[]],
            62: [False,[61],"Pyramid",[30,31,32,33,34,35,38]],
            63: [False,[],"Pyramid - Behind Aura",[]],
            64: [False,[],"Pyramid - Behind Spin Dash",[]],
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
            0: [0,1,[[1,gem[0]]]],                    # Jeweler Reward 1
            1: [0,1,[[1,gem[0]-2],[46,1]]],
            2: [0,1,[[1,gem[0]-3],[47,1]]],
            3: [0,1,[[1,gem[0]-5],[46,1],[47,1]]],
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
            30: [0,20,[[37,1]]],          # Cape to Coast w/ Lola's Letter
            31: [0,44,[[37,1]]],         # Cape to Watermia w/ Lola's Letter
            32: [27,48,[[13,1]]],        # Neil's to Euro w/ Memory Melody
            33: [27,61,[[13,1]]],        # Neil's to Dao w/ Memory Melody
            34: [27,66,[[13,1]]],        # Neil's to Babel w/ Memory Melody
            35: [29,28,[[25,1]]],        # Sky Garden to Nazca w/ Teapot
            36: [29,33,[[25,1]]],        # Sky Garden to Seaside Palace w/ Teapot
            37: [44,48,[[24,1]]],        # Watermia to Euro w/ Will
            38: [48,44,[[24,1]]],        # Euro to Watermia w/ Will
            39: [54,61,[[10,1]]],        # Natives' to Dao w/ Large Roast

            # SW Continent
            50: [0,12,[[9,1]]],          # Cape to Itory w/ Lola's Melody
            51: [8,9,[[2,1]]],           # Prison to Tunnel w/ Prison Key
            52: [9,10,[[9,1],[23,1]]],   # Tunnel Progression w/ Necklace & Lola's Melody
            53: [12,13,[[48,1]]],        # Itory Cave w/ Psycho Dash
            54: [12,13,[[49,1]]],        # Itory Cave w/ Psycho Slide
            55: [12,13,[[50,1]]],        # Itory Cave w/ Spin Dash
            56: [14,29,[[25,1]]],        # Moon Tribe to Sky Garden w/ Teapot
            57: [15,16,[[7,1],[48,1]]],  # Inca Ruins w/ Tile and Psycho Dash
            58: [15,16,[[7,1],[49,1]]],  # Inca Ruins w/ Tile and Psycho Slide
            59: [15,16,[[7,1],[50,1]]],  # Inca Ruins w/ Tile and Spin Dash
            60: [16,17,[[8,1]]],         # Inca Ruins w/ Wind Melody
            61: [17,18,[[3,1],[4,1]]],   # Inca Ruins w/ Inca Statues

            # SE Continent
            70: [22,23,[[48,1]]],        # Diamond Mine Progression w/ Psycho Dash
            71: [22,23,[[49,1]]],        # Diamond Mine Progression w/ Psycho Slide
            72: [22,23,[[50,1]]],        # Diamond Mine Progression w/ Spin Dash
            73: [22,24,[[51,1]]],        # Diamond Mine Progression w/ Dark Friar
            74: [22,24,[[50,1]]],        # Diamond Mine Progression w/ Spin Dash
            75: [22,25,[[15,1]]],        # Diamond Mine Progression w/ Elevator Key
            76: [25,26,[[11,1],[12,1]]], # Diamond Mine Progression w/ Mine Keys
            77: [29,30,[[51,1]]],        # Sky Garden Progression w/ Dark Friar
            78: [29,32,[[14,4]]],        # Sky Garden Progression w/ Crystal Balls
            79: [29,31,[[48,1]]],        # Sky Garden Progression w/ Psycho Dash
            80: [29,31,[[49,1]]],        # Sky Garden Progression w/ Psycho Slide
            81: [29,31,[[50,1]]],        # Sky Garden Progression w/ Spin Dash

            # NE Continent
            90: [33,34,[[17,1]]],         # Seaside Progression w/ Purity Stone
            91: [33,35,[[9,1],[23,1]]],   # Seaside Progression w/ Lilly
            92: [33,36,[[16,1]]],         # Seaside to Mu w/ Mu Key
            93: [36,33,[[16,1]]],         # Mu to Seaside w/ Mu Key
            94: [37,38,[[18,1]]],         # Mu Progression w/ Statue of Hope 1
            95: [38,71,[[51,1]]],         # Mu Progression w/ Dark Friar
            96: [38,71,[[49,1]]],         # Mu Progression w/ Psycho Slide
            97: [38,39,[[49,1]]],         # Mu Progression w/ Psycho Slide
            98: [71,40,[[18,2]]],         # Mu Progression w/ Statue of Hope 2
            99: [40,41,[[19,2]]],         # Mu Progression w/ Rama Statues
            100: [42,43,[[49,1]]],        # Angel Village to Dungeon w/ Slide
            101: [45,46,[[51,1]]],        # Great Wall Progression w/ Dark Friar
            102: [46,47,[[50,1]]],        # Great Wall Progression w/ Spin Dash

            # N Continent
            110: [48,49,[[40,1]]],        # Ann item w/ Apple
            111: [48,50,[[50,1]]],        # Euro to Mt. Temple w/ Spin Dash
            112: [50,51,[[26,1]]],        # Mt. Temple Progression w/ Drops 1
            113: [51,52,[[26,2]]],        # Mt. Temple Progression w/ Drops 2
            114: [52,53,[[26,3]]],        # Mt. Temple Progression w/ Drops 3
            115: [54,55,[[29,1]]],        # Natives' Village Progression w/ Flower
            116: [56,57,[[49,1],[50,1]]], # Ankor Wat Progression w/ Slide and Spin
            117: [57,58,[[51,1]]],        # Ankor Wat Progression w/ Dark Friar
            118: [57,58,[[36,1]]],        # Ankor Wat Progression w/ Aura
            119: [57,59,[[53,1]]],        # Ankor Wat Progression w/ Earthquaker
            120: [59,60,[[28,1]]],        # Ankor Wat Progression w/ Black Glasses

            # NW Continent
            130: [61,62,[[49,1]]],        # Pyramid foyer w/ Slide
            131: [61,62,[[50,1]]],        # Pyramid foyer w/ Spin
            #132: [61,54,[[10,1]]],        # Dao to Natives' w/ Large Roast
            133: [62,63,[[36,1]]],        # Pyramid Progression w/ Aura
            134: [62,65,[[30,1],[31,1],[32,1],[33,1],[34,1],[35,1],[38,1]]],
                                          # Pyramid Boss w/ Hieroglyphs and Journal
            135: [63,64,[[50,1]]],        # Pyramid Progression w/ Spin Dash

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

            76: "\xd6\x01\xd6\xec",   # "Angel Village"
            77: "\xd6\x01\xd6\xec",   # "Angel Village"
            78: "\xd6\x01\xd6\xec",   # "Angel Village"
            79: "\xd6\x01\xd6\xec",   # "Angel Village"
            80: "\xd6\x01\xd6\xec",   # "Angel Village"
            81: "\xd6\x01\xd6\xec",   # "Angel Village"
            82: "\xd6\x01\xd6\xec",   # "Angel Village"

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

            112: "\xd7\x21\xd6\xec",                       # "Natives' Village"
            113: "\x63\xa4\x80\xa4\xa5\x84",               # "Statue"
            114: "\xd7\x21\xd6\xec",                       # "Natives' Village"

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
        # Database of room clearing rewards
        # FORMAT: ID: [Map#, VanillaRewardCode (1=HP,2=STR,3=DEF), AreaName]
        # ROM address is mapID + 1aade
        self.room_rewards = {
            0: [12, 1, "Underground Tunnel"],
            1: [13, 2, "Underground Tunnel"],
            2: [14, 3, "Underground Tunnel"],
            3: [15, 1, "Underground Tunnel"],
            4: [18, 3, "Underground Tunnel"],
            5: [29, 2, "Inca Ruins"],
            6: [32, 2, "Inca Ruins"],
            7: [33, 3, "Inca Ruins"],
            8: [34, 1, "Inca Ruins"],
            9: [35, 1, "Inca Ruins"],
            10: [37, 3, "Inca Ruins"],
            11: [38, 2, "Inca Ruins"],
            12: [39, 1, "Inca Ruins"],
            13: [40, 3, "Inca Ruins"],
            14: [61, 1, "Diamond Mine"],
            15: [62, 1, "Diamond Mine"],
            16: [63, 2, "Diamond Mine"],
            17: [64, 3, "Diamond Mine"],
            18: [65, 3, "Diamond Mine"],
            19: [69, 2, "Diamond Mine"],
            20: [70, 1, "Diamond Mine"],
            21: [77, 1, "Sky Garden"],
            22: [78, 3, "Sky Garden"],
            23: [79, 2, "Sky Garden"],
            24: [80, 1, "Sky Garden"],
            25: [81, 3, "Sky Garden"],
            26: [82, 2, "Sky Garden"],
            27: [83, 1, "Sky Garden"],
            28: [84, 3, "Sky Garden"],
            29: [95, 1, "Mu"],
            30: [96, 2, "Mu"],
            31: [97, 3, "Mu"],
            32: [98, 1, "Mu"],
            33: [100, 3, "Mu"],
            34: [101, 2, "Mu"],
            35: [109, 2, "Angel Dungeon"],
            36: [110, 1, "Angel Dungeon"],
            37: [111, 2, "Angel Dungeon"],
            38: [112, 3, "Angel Dungeon"],
            39: [113, 1, "Angel Dungeon"],
            40: [114, 3, "Angel Dungeon"],
            41: [130, 3, "Great Wall"],
            42: [131, 1, "Great Wall"],
            43: [132, 2, "Great Wall"],
            44: [133, 1, "Great Wall"],
            45: [134, 3, "Great Wall"],
            46: [135, 2, "Great Wall"],
            47: [136, 1, "Great Wall"],
            48: [160, 2, "Mt. Temple"],
            49: [161, 3, "Mt. Temple"],
            50: [162, 1, "Mt. Temple"],
            51: [163, 2, "Mt. Temple"],
            52: [164, 1, "Mt. Temple"],
            53: [165, 3, "Mt. Temple"],
            54: [166, 1, "Mt. Temple"],
            55: [167, 3, "Mt. Temple"],
            56: [168, 2, "Mt. Temple"],
            57: [176, 1, "Ankor Wat"],
            58: [177, 2, "Ankor Wat"],
            59: [178, 3, "Ankor Wat"],
            60: [179, 1, "Ankor Wat"],
            61: [180, 3, "Ankor Wat"],
            62: [181, 2, "Ankor Wat"],
            63: [182, 1, "Ankor Wat"],
            64: [183, 2, "Ankor Wat"],
            65: [184, 3, "Ankor Wat"],
            66: [185, 1, "Ankor Wat"],
            67: [186, 3, "Ankor Wat"],
            68: [187, 2, "Ankor Wat"],
            69: [188, 1, "Ankor Wat"],
            70: [189, 3, "Ankor Wat"],
            71: [190, 1, "Ankor Wat"],
            72: [204, 3, "Pyramid"],
            73: [205, 2, "Pyramid"],
            74: [206, 3, "Pyramid"],
            75: [207, 3, "Pyramid"],
            76: [208, 3, "Pyramid"],
            77: [209, 2, "Pyramid"],
            78: [210, 1, "Pyramid"],
            79: [211, 3, "Pyramid"],
            80: [212, 1, "Pyramid"],
            81: [213, 2, "Pyramid"],
            82: [214, 3, "Pyramid"],
            83: [215, 2, "Pyramid"],
            84: [216, 3, "Pyramid"],
            85: [217, 2, "Pyramid"],
            86: [219, 2, "Pyramid"]

        }

        # Database of enemy types
        # FORMAT: { ID: [Enemy set ID, Event addr, VanillaTemplate, Name]}
        self.enemies = {
            0: [0,"\x55\x87\x8a","\x05","Underground Tunnel: Bat"], # a8755
            1: [0,"\x6c\x82\x8a","\x01","Underground Tunnel: Ribber"],
            2: [0,"\x00\x80\x8a","\x02","Underground Tunnel: Canal Worm"],
            3: [0,"\xf7\x85\x8a","\x03","Underground Tunnel: King Bat"],
            4: [0,"\x76\x84\x8a","\x10","Underground Tunnel: Skull Chaser"],
            5: [0,"\xff\x86\x8a","\x04","Underground Tunnel: Bat Minion 1"],
            6: [0,"\x9a\x86\x8a","\x04","Underground Tunnel: Bat Minion 2"],
            7: [0,"\x69\x86\x8a","\x04","Underground Tunnel: Bat Minion 3"],
            8: [0,"\xcb\x86\x8a","\x04","Underground Tunnel: Bat Minion 4"],

            10: [1,"\xb7\x8d\x8a","\x0b","Inca Ruins: Slugger"],
            11: [1,"\x1b\x8b\x8a","\x0a","Inca Ruins: Mudpit"],
            12: [1,"\x70\x8c\x8a","\x0c","Inca Ruins: Four Way"],
            13: [1,"\xee\x97\x8a","\x0f","Inca Ruins: Splop"],
            14: [1,"\xb6\x8e\x8a","\x0b","Inca Ruins: Scuttlebug"],
            15: [1,"\xbc\x98\x8a","\x0e","Inca Ruins: Whirligig"],
            16: [1,"\xc2\x95\x8a","\x0d","Inca Ruins: Stone Lord"],  # shoots fire
            17: [1,"\x70\x90\x8a","\x0d","Inca Ruins: Stone Guard"], # throws spears
            18: [1,"\xc3\x99\x8a","\x0e","Inca Ruins: Whirligig (stationary)"],
            19: [1,"\x03\x9b\x8a","\x14","Inca Ruins: Castoth (boss)"],

            20: [2,"\xca\xaa\x8a","\x18","Diamond Mine: Flayzer"],
            21: [2,"\xf5\xaf\x8a","\x1a","Diamond Mine: Grundit"],
            22: [2,"\x03\xb1\x8a","\x19","Diamond Mine: Eye Stalker"],
            23: [2,"\x8a\xaa\x8a","\x18","Diamond Mine: Flayzer (master)"],
            24: [2,"\xf5\xa4\x8a","\x1a","Diamond Mine: Grundit (stationary)"],
            25: [2,"\xb3\xb0\x8a","\x19","Diamond Mine: Eye Stalker (stone)"],
            26: [2,"\xd8\xb0\x8a","\x62","Diamond Mine: Eye Stalker (stone)"],

            30: [3,"\xb0\xb4\x8a","\x1d","Sky Garden: Blue Cyber"],
            31: [3,"\x33\xc5\x8a","\x1b","Sky Garden: Dynapede"],
            32: [3,"\xb0\xb8\x8a","\x1e","Sky Garden: Red Cyber"],
            33: [3,"\x16\xc8\x8a","\x1c","Sky Garden: Nitropede"],
            34: [3,"\x6f\xd1\x8a","\x27","Sky Garden: Viper (boss)"],

            40: [5,"\xcc\xe6\x8a","\x2b","Mu: Slipper"],
            41: [5,"\x5c\xe4\x8a","\x2a","Mu: Skuddle"],
            42: [5,"\x9e\xdd\x8a","\x28","Mu: Cyclops"],
            43: [5,"\x6e\xe2\x8a","\x29","Mu: Flasher"],
            44: [5,"\x07\xde\x8a","\x28","Mu: Cyclops (asleep)"],
            45: [5,"\xf7\xf1\x8a","\x2f","Mu: Vampire (boss)"],
            46: [5,"\xc8\xf3\x8a","\x30","Mu: Vampire (boss)"],

            50: [6,"\x9f\xee\x8a","\x2d","Angel Dungeon: Dive Bat"],
            51: [6,"\x51\xea\x8a","\x2c","Angel Dungeon: Steelbones"],
            52: [6,"\x33\xef\x8a","\x2e","Angel Dungeon: Draco"],
            53: [6,"\xc7\xf0\x8a","\x2e","Angel Dungeon: Ramskull"],

            60: [7,"\x55\x91\x8b","\x33","Great Wall: Archer 1"],
            61: [7,"\xfe\x8e\x8b","\x33","Great Wall: Archer Statue"],
            62: [7,"\xbe\x8d\x8b","\x34","Great Wall: Eyesore"],
            63: [7,"\x70\x8c\x8b","\x35","Great Wall: Fire Bug"],
            64: [7,"\x23\x94\x8b","\x32","Great Wall: Asp"],
            65: [7,"\x65\x91\x8b","\x33","Great Wall: Archer 2"],
            66: [7,"\x77\x91\x8b","\x33","Great Wall: Archer 3"],
            67: [7,"\x72\x8f\x8b","\x33","Great Wall: Archer Statue (switch)"],
            68: [7,"\x5c\x81\x8b","\x36","Great Wall: Sand Fanger (boss)"],

            70: [8,"\xac\x9b\x8b","\x3e","Mt Temple: Skulker (N/S)"],
            71: [8,"\x4e\x9c\x8b","\x3e","Mt Temple: Skulker (E/W)"],
            72: [8,"\x44\x9c\x8b","\x3e","Mt Temple: Skulker (E/W)"],
            73: [8,"\xa2\x9b\x8b","\x3e","Mt Temple: Skulker (E/W)"],
            74: [8,"\x8b\x9e\x8b","\x3d","Mt Temple: Yorrick (E/W)"],
            75: [8,"\x53\x9f\x8b","\x3d","Mt Temple: Yorrick (E/W)"],
            76: [8,"\x0f\x9d\x8b","\x3d","Mt Temple: Yorrick (N/S)"],
            77: [8,"\xcd\x9d\x8b","\x3d","Mt Temple: Yorrick (N/S)"],
            78: [8,"\x3b\x98\x8b","\x3f","Mt Temple: Fire Sprite"],
            79: [8,"\x1d\xa0\x8b","\x3c","Mt Temple: Acid Splasher 2"],
            80: [8,"\xa1\xa0\x8b","\x3c","Mt Temple: Acid Splasher (stationary E)"],
            81: [8,"\x75\xa0\x8b","\x3c","Mt Temple: Acid Splasher (stationary W)"],
            82: [8,"\x49\xa0\x8b","\x3c","Mt Temple: Acid Splasher (stationary S)"],
            83: [8,"\xcf\xa0\x8b","\x3c","Mt Temple: Acid Splasher (stationary N)"],

            90: [9,"\xd7\xb1\x8b","\x49","Ankor Wat: Shrubber"],
            91: [9,"\xb4\xb1\x8b","\x49","Ankor Wat: Shrubber 2"],
            92: [9,"\x75\xb2\x8b","\x46","Ankor Wat: Zombie"],
            93: [9,"\x8d\xbd\x8b","\x42","Ankor Wat: Goldcap"],
            94: [9,"\x25\xb8\x8b","\x45","Ankor Wat: Gorgon"],
            95: [9,"\x17\xb8\x8b","\x45","Ankor Wat: Gorgon (jump down)"],
            96: [9,"\xbb\xbf\x8b","\x43","Ankor Wat: Frenzie"],
            97: [9,"\xd0\xbf\x8b","\x43","Ankor Wat: Frenzie 2"],
            98: [9,"\x66\xbb\x8b","\x44","Ankor Wat: Wall Walker"],
            99: [9,"\x5c\xbb\x8b","\x44","Ankor Wat: Wall Walker 2"],
            100: [9,"\x4f\xaf\x8b","\x4a","Ankor Wat: Zip Fly"],

            110: [10,"\x5f\xc6\x8b","\x4f","Pyramid: Mystic Ball (stationary)"],
            111: [10,"\xfc\xc5\x8b","\x4f","Pyramid: Mystic Ball"],
            112: [10,"\xa3\xc5\x8b","\x4f","Pyramid: Mystic Ball"],
            113: [10,"\x9d\xc3\x8b","\x4e","Pyramid: Tuts"],
            114: [10,"\x98\xc7\x8b","\x51","Pyramid: Blaster"],
            115: [10,"\x84\xc1\x8b","\x4c","Pyramid: Haunt (stationary)"],
            116: [10,"\xa7\xc1\x8b","\x4c","Pyramid: Haunt"],
            #117: [10,"\x\x\x","\x","Pyramid: Haunt's Spirit"],     # bc2d0
            118: [10,"\xb6\xa6\x8b","\x50","Pyramid: Mummy Queen (boss)"],

            130: [11,"\xd7\x99\x8a","\x5a","Babel: Castoth (boss)"],
            131: [11,"\xd5\xd0\x8a","\x5b","Babel: Viper (boss)"],
            132: [11,"\x50\xf1\x8a","\x5c","Babel: Vampire (boss)"],
            133: [11,"\x9c\xf1\x8a","\x5c","Babel: Vampire (boss)"],
            134: [11,"\x00\x80\x8b","\x5d","Babel: Sand Fanger (boss)"],
            135: [11,"\x1a\xa6\x8b","\x5e","Babel: Mummy Queen (boss)"],
            136: [11,"\x09\xf7\x88","\x5f","Jeweler's Mansion: Solid Arm (boss)"],

            140: [12,"\xaa\xee\x8c","\x54","Final Boss: Dark Gaia"]

        }

        # Database of enemy spritesets
        # FORMAT: { ID: [ROM_Loction, HeaderData, Name]}
        self.spritesets = {
            0: ["d82a2","\x03\x00\x10\x10\xEC\x59\xCD\x01\x04\x00\x60\xA0\x8C\x75\xDE\x10\xD0\x21\x00\x47\xED\x9F","Underground Tunnel"],
            1: ["d85ac","\x03\x00\x10\x10\xBC\x33\xC2\x01\x04\x00\x60\xA0\x0C\x77\xDE\x10\x2A\x0F\x00\xE6\x08\xD5","Inca Ruins"],
            2: ["d8c37","\x03\x00\x10\x10\x16\x5C\xCC\x01\x04\x00\x60\xA0\xCC\x7A\xDE\x10\x30\x29\x00\xBE\x2F\xCB","Diamond Mine"],
            3: ["d8e0e","\x03\x00\x10\x10\x62\x3D\xCF\x01\x04\x00\x60\xA0\x4C\x7C\xDE\x10\x54\x1D\x00\xEF\xEE\x9E","Sky Garden"],
            4: ["d9123","\x03\x00\x10\x10\xEC\x59\xCD\x01\x04\x00\x60\xA0\x8C\x75\xDE\x10\xD0\x21\x00\x47\xED\x9F","Seaside Palace"],
            5: ["d9275","\x03\x00\x10\x10\x2D\x2E\xCC\x01\x04\x00\x60\xA0\x00\x00\xDF\x10\x16\x1C\x00\x41\x36\xD1","Mu"],
            6: ["d95b2","\x03\x00\x10\x10\xD1\x14\xCF\x01\x04\x00\x60\xA0\x40\x02\xDF\x10\x7F\x0F\x00\x2C\x2B\xD5","Angel Dungeon"],
            7: ["d9968","\x03\x00\x10\x10\x6D\x13\xD0\x01\x04\x00\x60\xA0\x40\x05\xDF\x10\xFF\x16\x00\xF7\xF3\x99","Great Wall"],
            8: ["d9eae","\x03\x00\x10\x10\x00\x00\xD0\x01\x04\x00\x60\xA0\x40\x08\xDF\x10\x70\x0E\x00\x5C\x4D\xD8","Mt. Kress"],
            9: ["da18b","\x03\x00\x10\x10\xEA\x15\xCE\x01\x04\x00\x70\x90\x53\x55\xDE\x10\xD5\x14\x00\x08\x73\xCC","Ankor Wat"],
            10: ["da618","\x03\x00\x10\x10\x0D\x18\xCB\x01\x04\x00\x60\x90\x80\x0A\xDF\x10\xFB\x13\x00\x0E\x67\xD1","Pyramid"],
            11: ["dabfc","\x03\x00\x10\x10\x16\x5C\xCC\x01\x04\x00\x60\xA0\xC0\x0C\xDF\x10\x30\x29\x00\xBE\x2F\xCB","Jeweler's Mansion"]
        }
