const { PAYMENT_STATUS } = require('../config/constants');

module.exports = (db) => ({
  // Receita por curso calculada no banco (uma consulta, sem N+1).
  revenueByCourse: () =>
    db.allAsync(`
      SELECT c.id AS course_id, c.title,
             COALESCE(SUM(CASE WHEN p.status = ? THEN p.amount ELSE 0 END), 0) AS revenue
      FROM courses c
      LEFT JOIN enrollments e ON e.course_id = c.id
      LEFT JOIN payments p ON p.enrollment_id = e.id
      GROUP BY c.id, c.title
      ORDER BY c.id`, [PAYMENT_STATUS.PAID]),

  // Alunos de cada curso com o valor pago (uma consulta).
  studentsByCourse: () =>
    db.allAsync(`
      SELECT e.course_id, u.name AS student, p.amount
      FROM enrollments e
      LEFT JOIN users u ON u.id = e.user_id
      LEFT JOIN payments p ON p.enrollment_id = e.id
      ORDER BY e.course_id, e.id`),
});
