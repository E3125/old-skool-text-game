from thing import *
from console import *

class Container(Thing):
    def __init__(self, ID):
        Thing.__init__(self, ID)
        self.contents = []
        self.max_weight_carried = 1
        self.max_volume_carried = 1

    def insert(self, obj):
        cons.debug("in insert")
        # error checking for max weight etc goes here
        contents_weight = 0
        contents_volume = 0
        cons.debug("going to start looping")
        for w in self.contents:
            contents_weight = contents_weight + w.weight
            contents_volume = contents_volume + w.volume
        cons.debug("done looping - carrying %d weight and %d volume" % (contents_weight, contents_volume))
        if self.max_weight_carried >= contents_weight+obj.weight and self.max_volume_carried >= contents_volume+obj.volume:
            cons.debug("can fit %d more weight and %d more volume" % (obj.weight, obj.volume))
            obj.set_location(self)   # make this container the location of obj
            self.contents.append(obj)
        else:
            cons.write("The weight(%d) and volume(%d) of the %s can't be held by the %s, "
                  "which can only carry %d grams and %d liters (currently "
                  "holding %d grams and %d liters)" 
                  % (obj.weight, obj.volume, obj.id, self.id, self.max_weight_carried, self.max_volume_carried, contents_weight, contents_volume))

    def set_max_weight_carried(self, max_grams_carried):
        self.max_weight_carried = max_grams_carried

    def set_max_volume_carried(self, max_liters_carried):
        self.max_volume_carried = max_liters_carried

    def extract(self, obj):
        if (obj in self.contents) == False:
            cons.write("Error! ",self.id," doesn't contain item ",obj.id)
            return
            
        found = -1
        for i in range(0, len(self.contents)):
            if obj == self.contents[i]:
                found = i
                break
        assert found != -1
        del self.contents[i]

    def look_at(self, cons, oDO, oIDO):
        Thing.look_at(self, cons, oDO, oIDO)
        if bool(len(self.contents)) and self.contents != [cons.user]:
            cons.write("Inside there is:")
            for item in self.contents:
                if item != cons.user:
                    cons.write(item.short_desc)
        else:
            cons.write("It is empty.")