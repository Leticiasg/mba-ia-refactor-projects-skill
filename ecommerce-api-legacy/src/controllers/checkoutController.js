const { PAYMENT_STATUS } = require('../config/constants');
const { ValidationError, UnauthorizedError, NotFoundError } = require('../middlewares/errors');
const { hashPassword, verifyPassword, randomPassword } = require('../utils/password');

function isNonEmptyString(value) {
  return typeof value === 'string' && value.trim().length > 0;
}

// c_id inválido segue a resposta original de curso inexistente (404).
function parseCourseId(rawId) {
  const courseId = Number(rawId);
  if ((typeof rawId !== 'number' && typeof rawId !== 'string') || !Number.isInteger(courseId) || courseId <= 0) {
    throw new NotFoundError('Curso não encontrado');
  }
  return courseId;
}

function validateCheckout({ name, email, password, courseId, card }) {
  if (!name || !email || !courseId || !card) throw new ValidationError('Bad Request');
  if (!isNonEmptyString(name) || !isNonEmptyString(email) || !isNonEmptyString(card)) {
    throw new ValidationError('Bad Request');
  }
  if (password !== undefined && password !== null && typeof password !== 'string') {
    throw new ValidationError('Bad Request');
  }
}

module.exports = ({ db, courseModel, userModel, enrollmentModel, paymentModel, auditLogModel, paymentService, logger }) => ({
  async checkout(input) {
    validateCheckout(input);
    const { name, email, password, courseId, card } = input;

    const course = await courseModel.findActiveById(parseCourseId(courseId));
    if (!course) throw new NotFoundError('Curso não encontrado');

    const existingUser = await userModel.findByEmail(email);
    if (existingUser && !verifyPassword(password, existingUser.pass)) {
      throw new UnauthorizedError('Não autorizado');
    }

    const status = await paymentService.charge(card, course.price);
    if (status === PAYMENT_STATUS.DENIED) throw new ValidationError('Pagamento recusado');

    const enrollmentId = await db.withTransaction(async () => {
      let userId = existingUser && existingUser.id;
      if (!userId) {
        // O contrato aceita checkout sem senha: gera uma senha aleatória em vez de uma fixa.
        const plainPassword = password || randomPassword();
        userId = await userModel.create({ name, email, passwordHash: hashPassword(plainPassword) });
      }
      const newEnrollmentId = await enrollmentModel.create(userId, course.id);
      await paymentModel.create(newEnrollmentId, course.price, status);
      await auditLogModel.record(`Checkout curso ${course.id} por ${userId}`);
      return newEnrollmentId;
    });

    logger.debug(`Checkout concluído: matrícula ${enrollmentId} no curso "${course.title}"`);
    return { enrollmentId };
  },
});
