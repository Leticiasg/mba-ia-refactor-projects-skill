const { ValidationError, NotFoundError, PaymentDeniedError } = require('../middlewares/errors');
const { PAYMENT_STATUS, generateRandomPassword } = require('../config/settings');
const { hashPassword } = require('../utils/password');

const isFilledString = (value) => typeof value === 'string' && value.trim() !== '';
const isPositiveId = (value) => /^\d+$/.test(String(value)) && Number(value) > 0;

function validate({ name, email, password, courseId, cardNumber }) {
  if (!isFilledString(name) || !isFilledString(email) || !isFilledString(cardNumber) || !isPositiveId(courseId)) {
    throw new ValidationError();
  }
  if (password !== undefined && password !== null && typeof password !== 'string') {
    throw new ValidationError();
  }
}

module.exports = ({ db, userModel, courseModel, enrollmentModel, paymentModel, auditLogModel, paymentService }) => ({
  async checkout(input) {
    validate(input);
    const { name, email, password, cardNumber } = input;
    const courseId = Number(input.courseId);

    const course = await courseModel.findActiveById(courseId);
    if (!course) throw new NotFoundError('Curso não encontrado');

    const status = paymentService.charge({ cardNumber, amount: course.price });
    if (status !== PAYMENT_STATUS.PAID) throw new PaymentDeniedError();

    const enrollmentId = await db.transaction(async () => {
      const existing = await userModel.findIdByEmail(email);
      const userId = existing
        ? existing.id
        : await userModel.create({ name, email, passwordHash: hashPassword(password || generateRandomPassword()) });

      const newEnrollmentId = await enrollmentModel.create({ userId, courseId });
      await paymentModel.create({ enrollmentId: newEnrollmentId, amount: course.price, status });
      await auditLogModel.record(`Checkout curso ${courseId} por ${userId}`);
      return newEnrollmentId;
    });

    return { enrollmentId };
  },
});
