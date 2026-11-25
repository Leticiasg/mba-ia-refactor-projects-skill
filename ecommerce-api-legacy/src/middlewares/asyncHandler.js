// Express 4 não captura Promise rejeitada: encaminha o erro para o errorHandler.
module.exports = (handler) => (req, res, next) =>
  Promise.resolve(handler(req, res, next)).catch(next);
