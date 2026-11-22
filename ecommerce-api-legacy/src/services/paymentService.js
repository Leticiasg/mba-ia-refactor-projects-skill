const { PAYMENT_STATUS, APPROVED_CARD_PREFIX } = require('../config/settings');

// Gateway simulado. A chave fica guardada aqui e nunca vai para log.
module.exports = ({ gatewayKey, logger }) => ({
  charge({ cardNumber, amount }) {
    if (!gatewayKey) logger.debug('PAYMENT_GATEWAY_KEY não definida; usando gateway simulado.');
    logger.info(`Processando cartão final ${cardNumber.slice(-4)} no valor de ${amount}`);
    return cardNumber.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
  },
});
