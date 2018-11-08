from pymongo import MongoClient
from bson import ObjectId
from DayManager import DayManager
from support_object import time_pointers, day_transformers

class ProposeManager():
    
    def __init__(self):
        client = MongoClient()
        self.daymanager = DayManager()
        self.database = client['pool_group']

    def get_propose(self, _id):
        return self.database.pending_propose.find_one({"_id": ObjectId(_id)})        

    def new_propose(self, proposedict):
        self.database.pending_propose.insert_one( proposedict )
        return proposedict['_id']
    
    def update_propose(self, _id, proposedict):
        self.database.pending_propose.update_one({"_id": _id}, {"$set": proposedict })

    def add_proposal(self, pool_propose, new_propose):
        if [ p['propose'] for p in pool_propose if p['propose'] in new_propose] != new_propose:
            for propose in new_propose:
                if propose not in [ p['propose'] for p in pool_propose ]:
                    pool_propose.append({
                        "propose": propose, 
                        "voted_by": []
                    })
        return pool_propose
    
    