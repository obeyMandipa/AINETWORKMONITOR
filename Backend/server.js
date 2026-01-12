const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const SNMPCollector = require('./services/snmpCollector');
const http = require('http');
const {Server} = required('socket.io');

// Express app setup
const app = express();
const server = http.createServer(app);
const io = new Server(server, {cors: {origin: '*'}});

app.use(cors());
app.use(express.json());

// MongoDB connection
mongoose.connect('mongodb://localhost:27017/network_monitor', {
    useNewUrlParser: true, 
    useUnifiedTopology: true
});


//metrics API endpoint
app.get('/api/metrics', async (req, res) => {
    const TrafficMetric = mongoose.model('TrafficMetric');
    const metrics = await TrafficMetric.find()
    .sort({timestamp: -1})
    .limit(100);
    res.json(metrics);
});

//start SNMP polling
const collector = new SNMPCollector();
collector.startPolling();

// Socket.io for real time updates
io.on('connection', (socket) => {
    console.log('Dashboard connected');

    socket.on('disconnect', () => {
        console.log('Dashboard disconnected');
    });
});

server.listen(3001, () => {
    console.log('server listening on port 3001')
});