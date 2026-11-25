// Constantes de domínio usadas por mais de uma camada.
const PAYMENT_STATUS = Object.freeze({
  PAID: 'PAID',
  DENIED: 'DENIED',
});

// Regra do gateway simulado: cartões que começam com este prefixo são aprovados.
const APPROVED_CARD_PREFIX = '4';

// Dígitos do cartão que podem aparecer em log.
const CARD_DIGITS_IN_LOG = 4;

module.exports = { PAYMENT_STATUS, APPROVED_CARD_PREFIX, CARD_DIGITS_IN_LOG };
