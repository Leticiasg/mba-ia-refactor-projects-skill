// Express 4 não captura Promise rejeitada sozinho.
module.exports = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);
