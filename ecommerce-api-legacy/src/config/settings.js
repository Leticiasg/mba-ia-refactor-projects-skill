const crypto = require('crypto');

const settings = {
  port: Number(process.env.PORT || 3000),
  dbPath: process.env.DB_PATH || ':memory:',
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
  adminToken: process.env.ADMIN_TOKEN || '',
  logLevel: process.env.LOG_LEVEL || 'info',
};

const PAYMENT_STATUS = Object.freeze({ PAID: 'PAID', DENIED: 'DENIED' });

// Regra do gateway simulado: cartões que começam com este prefixo são aprovados.
const APPROVED_CARD_PREFIX = '4';

// Usado quando o checkout chega sem senha (o contrato original aceita isso).
const generateRandomPassword = () => crypto.randomBytes(16).toString('hex');

module.exports = { settings, PAYMENT_STATUS, APPROVED_CARD_PREFIX, generateRandomPassword };
