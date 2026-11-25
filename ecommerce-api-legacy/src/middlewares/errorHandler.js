const { AppError } = require('./errors');
const logger = require('../config/logger');

// Respostas de erro em texto, como a API original.
// eslint-disable-next-line no-unused-vars
module.exports = (err, req, res, next) => {
  if (err instanceof AppError) return res.status(err.statusCode).send(err.message);
  if (err.type === 'entity.parse.failed') return res.status(400).send('Bad Request');
  logger.error(`Erro não tratado em ${req.method} ${req.path}`, err);
  return res.status(500).send('Erro interno do servidor');
};
