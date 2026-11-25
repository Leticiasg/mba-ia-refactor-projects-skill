const { PAYMENT_STATUS, APPROVED_CARD_PREFIX, CARD_DIGITS_IN_LOG } = require('../config/constants');

// Gateway de pagamento simulado. A chave vem da config e nunca vai para o log.
module.exports = ({ gatewayKey, logger }) => ({
  async charge(cardNumber, amount) {
    if (!gatewayKey) logger.debug('PAYMENT_GATEWAY_KEY não definida; usando gateway simulado.');
    logger.info(`Processando cartão final ${cardNumber.slice(-CARD_DIGITS_IN_LOG)} no valor ${amount}`);
    return cardNumber.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
  },
});
