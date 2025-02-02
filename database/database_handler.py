import asyncio
from motor.motor_asyncio import AsyncIOMotorClient as MotorClient
import sqlite3
from sqlite3 import Cursor
import typing
from motor import core as MotorCore
from pymongo import ReturnDocument, MongoClient
import uuid
import os





class MongoDatabase(object):
    """
    A class to handle all the database operations for sqlite3 and is used for backup when connection is lost to mongodb or other main database
    """
    def __init__(self) -> None:
        self.new_table = Cursor()
    
    def update_table(self,new_table):
        self.table = new_table






class MongoDatabase(object):
    """
    A clas to handle all the database operations for mongodb
    raw_operations/operation: -> {"path.to.key":"value"}
    
    """
    def __init__(self,client:typing.Optional[MotorClient],collection:typing.Optional[MotorCore.AgnosticCollection],document:typing.Optional[typing.Dict]={}):
        self.client:MotorClient = client
        self.collection:MotorCore.AgnosticCollection = collection
        self.document:typing.Dict = document
        self.document_id = {"_id":document['_id']}

    def gather_operations(self,operations):
        sorted_operations = {}
        for operation in operations:
            sorted_operations.update(operation)
        
        return sorted_operations
    async def set_items(self,raw_operations:typing.Dict):
        """Add a new key|value pair into the document
        Args:
            raw_operations (Dict): the operations to preform into the document
        Example:
            set_items({"user.John Doe":"pets:[]"}) # adds the name key with the value John Doe
        Returns:
            None: None
        
        """
        operations = {"$set":raw_operations}
        self.document = await self.collection.find_one_and_update(self.document_id,operations,return_document=ReturnDocument.AFTER)
    async def inc_operation(self,operations:typing.Dict):
        """Increment value of specified key
        Args:
            key_path (str): The path of the key
        Example:
            inc_operation("user.age",1) # increments the age by 1
        """
        self.document = await self.collection.find_one_and_update(self.document_id,operations,return_document=ReturnDocument.AFTER)
    async def rename_key(self,raw_operations:typing.Dict):
        """Rename a specified key
        Args:
            key_path (str): the path to the key to rename
            new_name (str): the new name for the key
        Example:
            rename_key("user.accounts.owners","authorized_users") # owners -> authorized_users
        """
        operations = {"$rename":raw_operations}
        self.document =await self.collection.find_one_and_update(self.document_id,operations,return_document=ReturnDocument.AFTER)
    
    async def unset_item(self,raw_operations:str):
        """Remove/unset a key from the dict/document
        Args:
            key_path (str): The dot notation path to the key
        Example: 
            unset_item("user.accounts") # removes the accounts key
        """
        operation = {"$unset":{raw_operations:""}}
        self.document =await self.collection.find_one_and_update(self.document_id,operation,return_document=ReturnDocument.AFTER)
    
    async def append_array(self,operations:typing.Dict):
        """Add an element or elements to an array
        Args:
            array_path (str): The dot notation path of the array
            values (typing.Union[int,str,typing.List]): a list of values or an int to add
        Example: 
            append_array("user.pets",["value1","value2"]) # adds value1 and value2 to the array
        Returns:
            _type_: _description_
        """
        operation = {"$addToSet":operations}
        self.document =await self.collection.find_one_and_update(self.document_id,operation,return_document=ReturnDocument.AFTER)
    
    async def pop_array(self,array_path,first_or_last:int):
        """
        Remove the first or last element of the array
        Args:
            array_path (int): The dot notation path of the array
            first_or_last (int): 1 to remove last and -1 to remove the first
        Example: 
            pop_array("array_path",1) # removes the last element
        Returns:
            pymongo.results.UpdateResult: An instance of the pymongo.results.UpdateResult
        """
        operation = {"$pop":{array_path:first_or_last}}
        self.document = await self.collection.find_one_and_update(self.document_id,operation,return_document=ReturnDocument.AFTER)
    async def pull_item(self,operations:typing.Dict):
        """Remove an element given specific index
        Args:
            operations (dict): the pull operations to preform
        Example: 
            pull_item({"user.pets":value_to_remove}) # removes the value from the array
        Returns:
            None
        """
        operation = {"$pull":operations}
        self.document = await self.collection.find_one_and_update(self.document_id,operation,return_document=ReturnDocument.AFTER)
    
    async def custom_operation(self,*operations):
        self.document = await self.collection.find_one_and_update(self.document_id,self.gather_operations(operations),return_document=ReturnDocument.AFTER)



class RanwbotMusic(MongoDatabase):
    def __init__(self):
        self.client:MongoClient = MotorClient(os.getenv("MONGO"))
        self.database:MotorCore.AgnosticDatabase = self.client['Discord-Bot-Database']
        self.collection:MotorCore.AgnosticCollection = self.database['General']
        self.document:typing.Dict[typing.Any,typing.Any]
        self.doc_id = {"_id":"music"}

    async def load_document(self):
        music_doc = await self.collection.find_one({"_id":"music"})
        if music_doc:
            self.document = music_doc
            self.doc_id['_id'] = music_doc['_id']
        else:
            self.document = {"_id":"music","userPlaylist":{}}
            await self.collection.insert_one(self.document)

    async def change_volume(self,guild_id:int,volume:int):
        await self.collection.find_one_and_update(self.doc_id,{"$set":{f"{guild_id}.vol":volume}})


    async def remove_song(self,user_id:int,song:str):
        await self.collection.find_one_and_update(self.doc_id,{"$pull":{f"userPlaylist.{user_id}":song}})


    async def save_song(self,user_id:int,track_info:typing.Dict):
        if user_id not in self.document['userPlaylist']:
            await self.collection.find_one_and_update(self.doc_id,{"$set":{f"userPlaylist.{user_id}":[track_info]}})
        else:
            await self.collection.find_one_and_update(self.doc_id,{"$push":{f"userPlaylist.{user_id}":track_info}})