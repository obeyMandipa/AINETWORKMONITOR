require('dotenv').config();
const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const SNMPCollector = require('./services/snmpCollector');
const { createServer} = require('http');
const {Server} = require('socket.io');
const path = require('path');
const logger = require('./utils/logger');



// Express app setup
const app = express();
const server = createServer(app);
const io = new Server(server, {
    cors: {
        origin: "http://localhost:3000",
        methods: ["GET", "POST"]
    }
    });

app.use(cors({ origin: "http://localhost:3000" }));
app.use(express.json());

// MongoDB connection
mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/network_monitor')
  .then(() => logger.info('MongoDB connected'))
  .catch(err => logger.error('MongoDB connection error:', err));


//metrics API endpoint
app.get('/api/metrics', async (req, res) => {
  try {
    const TrafficMetric = mongoose.model('TrafficMetric');
    const metrics = await TrafficMetric.find({})
      .sort({ timestamp: -1 })
      .limit(100);
    res.json(metrics);
  } catch (error) {
    logger.error('Metrics API error:', error);
    res.status(500).json({ error: 'Failed to fetch metrics' });
  }
}); console

app.get('/api/metrics/:device', async (req, res) => {
  try {
    const TrafficMetric = mongoose.model('TrafficMetric');
    const { device } = req.params;
    const metrics = await TrafficMetric.find({ device_id: device })
      .sort({ timestamp: -1 })
      .limit(100);
    res.json(metrics);
  } catch (error) {
    logger.error('Metrics API error:', error);
    res.status(500).json({ error: 'Failed to fetch metrics' });
  }
});

app.get('/api/health', (req, res) => {
  res.json({ status: 'OK', timestamp: new Date().toISOString() });
});

// Socket.io Real-time Updates
io.on('connection', (socket) => {
  logger.info('Dashboard client connected:', socket.id);
  
  socket.on('disconnect', () => {
    logger.info('Dashboard client disconnected:', socket.id);
  });
});

// Export io for SNMP collector
global.io = io;


//start SNMP polling
const collector = new SNMPCollector();
collector.startPolling();

// Error handling
process.on('uncaughtException', (error) => {
  logger.error('Uncaught Exception:', error);
  process.exit(1);
});


const PORT = process.env.PORT || 3001;
server.listen(PORT, () => {
  logger.info(`Server running on port ${PORT}`);
});