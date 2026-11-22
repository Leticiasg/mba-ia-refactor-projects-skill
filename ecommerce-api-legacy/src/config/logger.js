const LEVELS = { debug: 10, info: 20, warn: 30, error: 40 };

function createLogger(level = 'info') {
  const threshold = LEVELS[level] || LEVELS.info;
  const log = (name, writer) => (...args) => {
    if (LEVELS[name] >= threshold) writer(`[${name.toUpperCase()}]`, ...args);
  };
  return {
    debug: log('debug', console.debug),
    info: log('info', console.info),
    warn: log('warn', console.warn),
    error: log('error', console.error),
  };
}

module.exports = { createLogger };
