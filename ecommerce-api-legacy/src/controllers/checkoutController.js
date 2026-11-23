const { ValidationError, NotFoundError } = require('../middlewares/errors');
const { PAYMENT_STATUS, CARD_NUMBER_PATTERN } = require('../config/settings');
const { hashPassword, randomPassword } = require('../utils/password');

function isNonEmptyString(value) {
  return typeof value === 'string' && value.trim() !== '';
}

function validateCheckout({ name, email, password, courseId, cardNumber }) {
  const courseIdNumber = Number(courseId);
  const valid = isNonEmptyString(name)
    && isNonEmptyString(email) && email.includes('@')
    && (password === undefined || password === null || typeof password === 'string')
    && Number.isInteger(courseIdNumber) && courseIdNumber > 0
    && typeof cardNumber === 'string' && CARD_NUMBER_PATTERN.test(cardNumber);
  if (!valid) throw new ValidationError('Bad Request');
  return courseIdNumber;
}

module.exports = ({ db, userModel, courseModel, enrollmentModel, paymentModel, auditLogModel, paymentService }) => ({
  async checkout(input) {
    const courseId = validateCheckout(input);
    const { name, email, password, cardNumber } = input;

    const course = await courseModel.findActiveById(courseId);
    if (!course) throw new NotFoundError('Curso não encontrado');

    const status = paymentService.authorize({ cardNumber });
    if (status !== PAYMENT_STATUS.PAID) throw new ValidationError('Pagamento recusado');

    return db.withTransaction(async () => {
      const user = await userModel.findByEmail(email);
      // O contrato aceita checkout sem senha: nesse caso a conta nasce com senha aleatória.
      const userId = user
        ? user.id
        : await userModel.create({ name, email, passwordHash: hashPassword(password || randomPassword()) });

      const enrollmentId = await enrollmentModel.create(userId, course.id);
      await paymentModel.create(enrollmentId, course.price, status);
      await auditLogModel.record(`Checkout curso ${course.id} por ${userId}`);
      return { enrollmentId };
    });
  },
});
