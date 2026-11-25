// Logger com níveis sobre o console (sem dependência nova).
const settings = require('./settings');

const LEVELS = { debug: 10, info: 20, warn: 30, error: 40 };
const threshold = LEVELS[settings.logLevel] || LEVELS.info;

function log(level, message, ...extra) {
  if (LEVELS[level] < threshold) return;
  const line = `${new Date().toISOString()} [${level.toUpperCase()}] ${message}`;
  const write = level === 'error' ? console.error : level === 'warn' ? console.warn : console.log;
  write(line, ...extra);
}

module.exports = {
  debug: (msg, ...extra) => log('debug', msg, ...extra),
  info: (msg, ...extra) => log('info', msg, ...extra),
  warn: (msg, ...extra) => log('warn', msg, ...extra),
  error: (msg, ...extra) => log('error', msg, ...extra),
};
