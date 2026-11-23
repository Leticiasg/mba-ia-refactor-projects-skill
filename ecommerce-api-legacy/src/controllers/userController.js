const { ValidationError, NotFoundError } = require('../middlewares/errors');

module.exports = ({ db, userModel, enrollmentModel, paymentModel }) => ({
  async deleteUser(rawId) {
    const userId = Number(rawId);
    if (!Number.isInteger(userId) || userId <= 0) throw new ValidationError('Bad Request');

    await db.withTransaction(async () => {
      await paymentModel.deleteByUserId(userId);
      await enrollmentModel.deleteByUserId(userId);
      const deleted = await userModel.deleteById(userId);
      if (deleted === 0) throw new NotFoundError('Usuário não encontrado');
    });
    return 'Usuário deletado, com suas matrículas e pagamentos.';
  },
});
