from pymongo import MongoClient
from bson import ObjectId
from DayManager import DayManager
from pointers import time_pointers, day_transformers

class PoolManager():
    
    def __init__(self):
        client = MongoClient()
        self.daymanager = DayManager()
        self.database = client['pool_group']

    def init_pool(self):
        return {
            "title": None, 
            "closed": False, 
            "time_value": {
                "close_datetime": self.daymanager.get_close_pool( self.daymanager.add_day() ),
                "pool_day": self.daymanager.get_today(),
                "time_pointers": "oggi"
            }

    def close_pool(self, _id):
        self.database.pool.update_one({"_id": _id}, {"$set": {'closed': True}} )

    def pools_same_day(self, chat_id, time_value):
        return self.database.pool.find_one({
            "chat_id": chat_id, 
            "closed": False, 
            "time_value.pool_day": time_value['pool_day'], 
            "time_value.time_pointers": time_value['time_pointers']
        }) is None
    
    def get_opened_pools(self, chat_id, owner=None):
        if owner != None:
            opened_pool = self.database.pool.find_one({"chat_id": chat_id, "closed": False, "owner": owner})
        else:
            opened_pool = self.database.pool.find({"chat_id": chat_id, "closed": False})
        return list(opened_pool)

    def get_pools_toclose(self, time_pointer):
        pools = self.database.pool.find({
            "time_value.time_pointers": time_pointer,
            "time_value.pool_day": self.daymanager.get_today(), 
            "time_value.close_datetime": self.daymanager.get_close_pool(hour=time_pointers[time_pointer])
        })
        return list(pools)

    def new_pool(self, pooldict):
        self.database.pool.insert_one( pooldict )
        return pooldict['_id']
    
    def update_pool(self, _id, pooldict):
        self.database.pool.update_one({"_id": _id}, {"$set": pooldict })