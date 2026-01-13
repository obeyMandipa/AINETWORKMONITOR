/*
rovides structured logging for your Node.js backend application. 
It captures, formats, and stores logs for debugging, monitoring, and troubleshooting
 */
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
    winston.format.errors({ stack: true }),
    
    // ✅ CUSTOM PRETTY FORMAT - New lines + spacing
    winston.format.printf(({ timestamp, level, message, stack }) => {
      const msg = stack ? `${message}\n${stack}` : message;
      return `\n┌─ ${timestamp} [${level.toUpperCase()}] ────────────────────────────────
│  ${msg}
└───────────────────────────────────────────────────────────────────────────\n`;
    })
  ),
  transports: [
    new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
    new winston.transports.File({ filename: 'logs/combined.log' }),
    
    // Console with colors + pretty format
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.timestamp({ format: 'HH:mm:ss' }),
        winston.format.printf(({ timestamp, level, message, stack }) => {
          const msg = stack ? `${message}\n${stack}` : message;
          return `┌─ ${timestamp} [${level}] ${msg}
└──────────────────────────────────────`;
        })
      )
    })
  ]
});

module.exports = logger;

