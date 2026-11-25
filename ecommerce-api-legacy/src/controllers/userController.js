const { ValidationError } = require('../middlewares/errors');

module.exports = ({ db, userModel, enrollmentModel, paymentModel }) => ({
  // Remove o usuário junto com as matrículas e os pagamentos dele.
  async deleteUser(rawId) {
    const userId = Number(rawId);
    if (!Number.isInteger(userId) || userId <= 0) throw new ValidationError('Bad Request');

    await db.withTransaction(async () => {
      await paymentModel.deleteByUserId(userId);
      await enrollmentModel.deleteByUserId(userId);
      await userModel.deleteById(userId);
    });
    return 'Usuário deletado';
  },
});
