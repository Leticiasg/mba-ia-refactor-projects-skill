// Configuração vinda do ambiente. Só o que não é segredo tem valor padrão.
const settings = {
  port: Number(process.env.PORT || 3000),
  dbPath: process.env.DB_PATH || ':memory:',
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
  adminToken: process.env.ADMIN_TOKEN || '',
  logLevel: process.env.LOG_LEVEL || 'info',
};

const PAYMENT_STATUS = Object.freeze({ PAID: 'PAID', DENIED: 'DENIED' });

// Gateway simulado: cartões com este prefixo são aprovados.
const APPROVED_CARD_PREFIX = '4';
const CARD_NUMBER_PATTERN = /^\d{12,19}$/;

module.exports = { settings, PAYMENT_STATUS, APPROVED_CARD_PREFIX, CARD_NUMBER_PATTERN };
