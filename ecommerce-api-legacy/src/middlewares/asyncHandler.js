// Express 4 não repassa Promise rejeitada ao middleware de erro sozinho.
module.exports = (handler) => (req, res, next) => Promise.resolve(handler(req, res, next)).catch(next);
