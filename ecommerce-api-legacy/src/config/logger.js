const { settings } = require('./settings');

const LEVELS = { debug: 10, info: 20, warn: 30, error: 40 };
const threshold = LEVELS[settings.logLevel] || LEVELS.info;

function write(level, method, args) {
  if (LEVELS[level] < threshold) return;
  console[method](`[${new Date().toISOString()}] ${level.toUpperCase()}`, ...args);
}

module.exports = {
  debug: (...args) => write('debug', 'log', args),
  info: (...args) => write('info', 'log', args),
  warn: (...args) => write('warn', 'warn', args),
  error: (...args) => write('error', 'error', args),
};
