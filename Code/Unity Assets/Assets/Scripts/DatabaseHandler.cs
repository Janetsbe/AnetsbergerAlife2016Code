using MongoDB.Driver;
using System.Collections;
using MongoDB.Bson;
using MongoDB.Driver.Builders;
using System;
using UnityEngine;
using MongoDB.Bson.Serialization;
using System.Linq;

public class DatabaseHandler {

    MongoServerSettings settings = new MongoServerSettings();
    MongoServer server;
    MongoDatabase database;
    MongoCollection<BsonDocument> msg;
    MongoCollection<BsonDocument> robotData;

    // Use this for initialization
    public DatabaseHandler(string databaseName) {
        settings.Server = new MongoServerAddress("localhost", 27017);
        server = new MongoServer(settings);
        database = server.GetDatabase(databaseName);
        msg = database.GetCollection("messages");
        robotData = database.GetCollection("robotdata");
        Debug.Log(robotData);
     
    }
	
	// Update is called once per frame
	void Update () {
      
	}


    //Write a message to the DB collection "messages"
    public void WriteToDB<T>(string messageType, T message) {
        BsonValue bsonMsg = BsonValue.Create(message);

        IMongoQuery query = Query.Matches("_id", messageType);
        UpdateBuilder updateBuilder = new UpdateBuilder();
        IMongoUpdate update = updateBuilder.Set("value", bsonMsg);
        msg.Update(query, update);
    }

    public void WriteSensorData(int[][] sensorData, string robotID) {
        Debug.Log("Writing sensor data");

        foreach(int[] row in sensorData) { 
        //string dataRowString = string.Join(", ", Array.ConvertAll(subarray, x => x.ToString()));
            BsonArray sensorDataRow = BsonArray.Create(row);
            Debug.Log(sensorDataRow);
            IMongoQuery query = Query.Matches("_id", robotID);
            UpdateBuilder updateBuilder = new UpdateBuilder();
            IMongoUpdate update = updateBuilder.Push("sensorData", sensorDataRow);//Set("positions", posString);
            robotData.Update(query, update);
        }
    }

    public void ClearSensorData(string robotID) {
        //Debug.Log(sensorDataRow);
        BsonArray emptyArray = BsonArray.Create(new int[0]);
        IMongoQuery query = Query.Matches("_id", robotID);
        UpdateBuilder updateBuilder = new UpdateBuilder();
        IMongoUpdate update = updateBuilder.Set("sensorData", emptyArray);
        robotData.Update(query, update);
    }

    public void WriteSensorDataRow(int[] sensorValues, string robotID) {
        //Debug.Log("Writing sensor data");
        
        //string dataRowString = string.Join(", ", Array.ConvertAll(subarray, x => x.ToString()));
        BsonArray sensorDataRow = BsonArray.Create(sensorValues);
        Debug.Log(sensorDataRow);
        IMongoQuery query = Query.Matches("_id", robotID);
        UpdateBuilder updateBuilder = new UpdateBuilder();
        IMongoUpdate update = updateBuilder.Push("sensorData", sensorDataRow);
        robotData.Update(query, update);
        
       
    }

    //Write a set of position vectors to the database.
    public void WritePosition(string position, string robotID, bool rerun) {
        Debug.Log("SETTING POSITIONS");
        BsonValue posString = BsonValue.Create(position.ToString());
        IMongoQuery query = Query.Matches("_id", robotID);
        UpdateBuilder updateBuilder = new UpdateBuilder();
        string fieldName = !rerun ? "positions" : "rerunPositions";
        IMongoUpdate update = updateBuilder.Push(fieldName, posString);
        robotData.Update(query, update);
    }

    public float[,] ReadController(int numJoints) {
        BsonDocument result = msg.FindOne(Query.Matches("_id", "controller"));
        BsonArray tempBsonArray = result["value"].AsBsonArray;
        float[,] controller = new float[numJoints, 3];

        int i = 0;
        foreach (BsonArray subarray in tempBsonArray) {
            int j = 0;
            foreach (var element in subarray) {
                controller[i, j] = (float)element.ToDouble();
                j++;
            }
            i++;
        }
        return controller;
    }


    public T ReadFromDB<T>(string messageType) {
        T value;
        BsonDocument result = msg.FindOne(Query.Matches("_id", messageType));
        try {
            if (typeof(T) == typeof(string[])) {
                ArrayList tempList = new ArrayList();
                BsonArray resultArray = result["value"].AsBsonArray;
                foreach (var element in resultArray)
                {
                    tempList.Add(element.ToString());
                }
                value = (T)System.Convert.ChangeType(tempList.ToArray(typeof(string)), typeof(T));
            }
            else {
                value = (T)System.Convert.ChangeType(result["value"], typeof(T));
            }
        } catch {
            System.Console.WriteLine("Error: nothing to read");
            value = default(T);
        }

        return value;
    }

    public void CloseConnection() {
        server.Disconnect();
    }



}
