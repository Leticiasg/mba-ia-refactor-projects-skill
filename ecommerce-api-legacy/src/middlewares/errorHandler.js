const { AppError } = require('./errors');

module.exports = (logger) => (err, req, res, next) => {
  if (res.headersSent) return next(err);
  if (err instanceof AppError) return res.status(err.statusCode).send(err.message);
  if (err.type === 'entity.parse.failed') return res.status(400).send('Bad Request');
  logger.error('Erro não tratado:', err);
  return res.status(500).send('Erro interno do servidor');
};
