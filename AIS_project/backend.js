//import required libraries
const express = require("express");
const { Pool } = require("pg");

//create an Express application
const app = express();

// CORS middleware allows requests from any origin
//It prevents CORS errors when frontend and backend run on different ports
app.use((req, res, next) => {
    res.header("Access-Control-Allow-Origin", "*");
    res.header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept");
    next();
});

//Database connection
//create a connection pool for PostreSQL
const pool = new Pool({
    user: "postgres",
    host: "localhost",
    database: "postgres",
    password: "1234",
    port: 5433
});

//Static files
//serve static files from the "public" folder
app.use(express.static("public"));

//API endpoint
//GET endpoint to retrieve ship information
app.get("/api/ships", async (req, res) => {
    //Query the database
    const result = await pool.query(`

SELECT DISTINCT ON (l.mmsi)
l.mmsi,
l.lat,
l.lon,
l.sog,
l.cog,
v.name

FROM ais_locations l

LEFT JOIN ais_vessels v
ON l.mmsi = v.mmsi

ORDER BY l.mmsi, l.time DESC

`);

    res.json(result.rows);

});

//Start the server on port 3000
app.listen(3000, () => {
    console.log("Server running http://localhost:3000");
});
