import json
import time
import uuid

import paho.mqtt.client as mqtt
import psycopg2

#pip install paho-mqtt
#pip install psycopg2

# Making a database to AIS-datas

# --- Change your own informations here ----------

dbname = "postgres"
password = "1234"
user = "postgres"
port = 5432     

#name is used when connecting to MQT broker
APP_NAME = "AIS DataLoader 1.0"

#Connect to PostgreSQL database
conn = psycopg2.connect(host="localhost", dbname=dbname, user=user,
                         password=password, port=port)

#Create a cursor object for executing SQL commands
cur = conn.cursor()

#MQTT connection callback
#Runs when the client connects to the broker
def on_connect(client, userdata, flags, reason_code, properties):

    if reason_code == 0: #code 0 means connection successfull
        print("Connected")
        #Subscribe to AIS vessel topics (/location and /metadata)
        client.subscribe("vessels-v2/+/#")
       
    else:
        print("Failed to connect, return code %d\n", reason_code)

#MQTT message callback
#Runs every time a message is received
def on_message(client, userdata, msg):

    try: #Decode JSON message payload
        data = json.loads(msg.payload.decode("utf-8"))
        #Split topic into parts
        parts = msg.topic.split("/")
        msg_type = parts[-1]   # location or metadata
        
        # LOCATION
        # Vessel position updates
        if msg_type == "location":
            mmsi = int(parts[1]) #Extract location from topic
            #Extract location fields from JSON message
            time = data["time"]
            lat = data["lat"]
            lon = data["lon"]
            rot = data["rot"]
            sog = data["sog"]
            cog = data["cog"]
            navStat = data["navStat"]
            heading = data["heading"]

        #Create table if it doesn't exist
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ais_locations(
                id SERIAL PRIMARY KEY,
                mmsi INT,
                time INT,
                lat REAL,
                lon REAL,
                rot REAL,
                sog REAL,
                cog REAL,
                navStat REAL,
                heading REAL); """)
            
            #Insert AIS location data into database
            cur.execute("""
                INSERT INTO ais_locations(mmsi, time, lat, lon, rot, sog, cog, navStat, heading)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""", (mmsi, time, lat, lon, rot, sog, cog, navStat, heading))
            
            #Save changes to database
            conn.commit()

        #METADATA 
        #Vessel static information
        elif msg_type == "metadata":
            mmsi = int(parts[1]) #Extract MMSI
            #Extract metadata fields
            name = data["name"]
            timestamp = int(data["timestamp"])
            destination = data["destination"]
            type = int(data["type"])
            imo= int(data["imo"])
            callSign = data["callSign"]
            draught = float(data["draught"])

            #Create vessel metadata table if it doesn't exist
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ais_vessels(
                id SERIAL PRIMARY KEY,
                mmsi INT,
                name VARCHAR(255),
                timestamp NUMERIC,
                destination VARCHAR(255),
                type INT,
                imo INT,
                callSign VARCHAR(255),
                draught REAL); """)
            
            #Insert vessel metadata into database
            cur.execute("""
                INSERT INTO ais_vessels(mmsi, name, timestamp, destination, type, imo, callSign, draught)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""", (mmsi, name, timestamp, destination, type, imo, callSign, draught))
            
            #Save changes
            conn.commit()        

    #Error handling
    except Exception as e:
        print("Error:", e) #Print error message
        conn.rollback() #Rollback transaction to avoid corrupted data

#MQTT Client configuration
#Create a unique client ID using app name + random uuid
client_name = "{}; {}".format(APP_NAME, str(uuid.uuid4()))

#Create MQTT client
client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    transport="websockets", #(Digitraffic requires Websockets)
    client_id=client_name,)

#Assign callback functions
client.on_connect = on_connect
client.on_message = on_message

#Enable TLS encryption for secure connection
client.tls_set()

#Connect to Digitraffic AIS broker
client.connect("meri.digitraffic.fi", 443)

#Start MQTT client loop
client.loop_start()
time.sleep(3600) # Change this if needed

client.loop_stop() #stop receiving message
client.disconnect() #Disconnect from broker

#Close database connection
conn.close()
cur.close()
