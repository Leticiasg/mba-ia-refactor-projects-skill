const { PAYMENT_STATUS, APPROVED_CARD_PREFIX } = require('../config/settings');

// Integração com o gateway de pagamento (simulada: aprova pelo prefixo do cartão).
module.exports = ({ gatewayKey, logger }) => {
  if (!gatewayKey) logger.warn('PAYMENT_GATEWAY_KEY não definida; gateway em modo simulado.');

  return {
    authorize({ cardNumber }) {
      logger.info(`Processando cartão final ${cardNumber.slice(-4)}`);
      return cardNumber.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
    },
  };
};
