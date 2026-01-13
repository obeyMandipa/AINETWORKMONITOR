/**
 * Backend/services/snmpCollector.js
 * ---------------------------------
 * Purpose:
 *  - Polls network devices using SNMP to collect traffic and system metrics.
 *  - Persists a record of collected metrics to MongoDB via a Mongoose model.
 *  - Publishes raw metric payloads to a Kafka topic for downstream processing.
 *
 * How it works (high-level):
 *  1) For each target device defined in `DEVICES`, the collector establishes or
 *     reuses an SNMP session.
 *  2) It queries specific OIDs (object identifiers) to obtain interface counters
 *     and system metrics (CPU, memory).
 *  3) Writes a `TrafficMetric` document into MongoDB and publishes the same
 *     JSON payload to the `raw_metrics` Kafka topic.
 */

// External dependencies
const snpm = require('snmp-native'); // library to interact with SNMP devices
const log = console.log;
const mongoose = require('mongoose'); // MongoDB ORM
const {Kafka, Partitioners} = require('kafkajs'); // Kafka client

// Mongoose model: stores a snapshot of traffic/system metrics for a device/interface
const TrafficMetric = mongoose.model('TrafficMetric', new mongoose.Schema({
    deviceId: String,
    interface: String,
    timestamp: {type: Date, default: Date.now},
    bytesIn: Number,
    bytesOut: Number,
    packetsIn: Number,
    packetsOut: Number,
    packetsDropped: Number,
    cpuUsage: Number,
    memoryUsage: Number,
}));

// Kafka Producer Setup
// - Instantiate a Kafka client and create a producer to publish raw measurement messages.
// - Ensure your Kafka broker is reachable at the address below, or change as needed.
const kafkaClient = new Kafka({clientId: 'snmp-collector', brokers: ['localhost:9092']});
const producer = kafkaClient.producer({
    createPartitioner: Partitioners.LegacyPartitioner
});

// Example devices to poll. In a real installation this could be driven by a
// configuration file or a database table and would include device-specific
// SNMP credentials and interface mappings.
const DEVICES = [
    {id: 'router1', host: '192.168.1.1', community: 'public'},
    {id: 'switch1', host: '192.168.1.2', community: 'public'},
    {id: 'firewall1', host: '192.168.1.3', community: 'public'},
];

// OIDs for the various metrics. They map a friendly name to the SNMP OID used
// to query the value. Note that table columns (e.g., ifInOctets) are commonly
// indexed per-interface; the code appends an interface index (like '1') to query
// a specific instance.
const OIDS = {
    bytesIn: [1,3,6,1,2,1,2,2,1,10], // ifInOctets
    bytesOut: [1,3,6,1,2,1,2,2,1,16], // ifOutOctets
    packetsIn: [1,3,6,1,2,1,2,2,1,11], // ifInUcastPkts
    packetsOut: [1,3,6,1,2,1,2,2,1,17], // ifOutUcastPkts
    packetsDropped: [1,3,6,1,2,1,2,2,1,8], // ifInDiscards
    cpuUsage: '1.3.6.1.4.1.9.9.109.0.5', // system CPU load (vendor-specific)
    memoryUsage: '1.3.6.1.4.1.9.9.480.0.5' // memory usage (vendor-specific)
};

/**
 * SNMPCollector
 *  - Manages SNMP sessions and polling lifecycle for the configured devices.
 */
class SNMPCollector {
    constructor() {
        // Simple in-memory cache of SNMP sessions keyed by device id
        this.sessionCache = new Map();
    }

    /**
     * createSession(device)
     *  - Reuses an existing session if available, otherwise creates a new
     *    SNMP v2c session for the given device.
     * @param {Object} device - {id, host, community}
     * @returns {Object} snmp session
     */
    async createSession(device) {
        if (this.sessionCache.has(device.id)) {
            return this.sessionCache.get(device.id);
        }

        const session = snpm.createSession(device.host, device.community, {
            timeout: 3000,
            version: snpm.Version2c
        });

        this.sessionCache.set(device.id, session);
        return session;
    }

    /**
     * getMetric(session, oid)
     *  - Performs a single SNMP GET call and resolves with the value. The
     *    function returns a Promise so it can be used with Promise.all/settled.
     * @param {Object} session - SNMP session returned by createSession
     * @param {String|Array} oid - OID to query (array or dot-notation string)
     */
    async getMetric(session, oid) {
        return new Promise((resolve, reject) => {
            session.get({oid: oid}, (error, varbinds) => {
                if (error) {
                    return reject(error);
                }
                resolve(varbinds[0].value);
            });
        });
    }

    /**
     * pollDevice(device)
     *  - Gathers all defined metrics for `device`, persists to MongoDB and
     *    publishes the payload to Kafka. Uses Promise.allSettled so a single
     *    failed OID read won't stop the other fetches.
     * @param {Object} device - device configuration from DEVICES
     * @returns {Object} consolidated metric payload
     */
    async pollDevice(device) {
        try{
            const session = await this.createSession(device);
            const metrics = await Promise.allSettled([
                // For table-based OIDs (array form above), the code appends the
                // interface index (e.g., '1') to request a specific instance.
                this.getMetric(session, OIDS.bytesIn + '1'),
                this.getMetric(session, OIDS.bytesOut + '1'),
                this.getMetric(session, OIDS.packetsIn + '1'),
                this.getMetric(session, OIDS.packetsOut + '1'),
                this.getMetric(session, OIDS.packetsDropped + '1'),
                this.getMetric(session, OIDS.cpuUsage),
                this.getMetric(session, OIDS.memoryUsage)
            ]);

            // Build a canonical payload. Values default to 0 on read failure.
            const metric = {
                device_id: device.id,
                interface: '1', // Example: querying interface index 1
                bytes_in: metrics[0].status === 'fulfilled' ? metrics[0].value : 0,
                bytes_out: metrics[1].status === 'fulfilled' ? metrics[1].value : 0,
                packets_in: metrics[2].status === 'fulfilled' ? metrics[2].value : 0,
                packets_out: metrics[3].status === 'fulfilled' ? metrics[3].value : 0,
                packets_dropped: metrics[4].status === 'fulfilled' ? metrics[4].value : 0,
                cpu_usage: metrics[5].status === 'fulfilled' ? metrics[5].value : 0,
                memory_usage: metrics[6].status === 'fulfilled' ? metrics[6].value : 0,
                latency_ms: Math.random() * 50 + 10 // Simulated latency for example
            };

            // Persist to MongoDB for long-term storage / historical queries
            await TrafficMetric.create(metric);

            // Publish raw message to Kafka for downstream pipelines (parsing, alerts, etc.)
            await producer.send({
                topic: 'raw_metrics',
                messages: [{value: JSON.stringify(metric)}],
            });

            log(`Polled ${device.id}: ${metric.bytes_in} bytes in`);
            return metric;
        }

        catch (error) {
            // Log the error; production code should include retry/backoff logic
            log(`SNMP poll failed for ${device.id}:`, error)
        }
    }

    /**
     * startPolling()
     *  - Connects the Kafka producer and starts a periodic polling loop.
     *  - The interval here is short for demo purposes; adjust to your needs.
     */
    async startPolling() {
        await producer.connect();

        setInterval(async () => {
            for (const device of DEVICES) {
                await this.pollDevice(device);
            }
        }, 3000); // every 3 seconds (adjust to 30s/5m in production)

        log('SNMP Collector started polling devices every 30 secs.');
    }
}

// Export the collector class so the application entrypoint can instantiate and
// start polling or run polls on demand.
module.exports = SNMPCollector;