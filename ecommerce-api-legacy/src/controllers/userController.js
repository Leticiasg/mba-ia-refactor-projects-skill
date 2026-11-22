const { ValidationError } = require('../middlewares/errors');

// Mensagem mantida idêntica à original para não quebrar o contrato da API.
const DELETE_MESSAGE = 'Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.';

module.exports = ({ db, userModel, enrollmentModel, paymentModel }) => ({
  async deleteUser(rawId) {
    if (!/^\d+$/.test(String(rawId))) throw new ValidationError();
    const userId = Number(rawId);
    await db.transaction(async () => {
      await paymentModel.deleteByUserId(userId);
      await enrollmentModel.deleteByUserId(userId);
      await userModel.deleteById(userId);
    });
    return DELETE_MESSAGE;
  },
});
