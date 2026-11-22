const { PAYMENT_STATUS } = require('../config/settings');

module.exports = (db) => ({
  // Uma consulta só: cursos com receita agregada no banco e uma linha por matrícula.
  async financialRows() {
    return db.allAsync(`
      SELECT c.id AS course_id,
             c.title,
             SUM(CASE WHEN p.status = ? THEN p.amount ELSE 0 END) OVER (PARTITION BY c.id) AS revenue,
             e.id AS enrollment_id,
             u.name AS student,
             p.amount
      FROM courses c
      LEFT JOIN enrollments e ON e.course_id = c.id
      LEFT JOIN users u ON u.id = e.user_id
      LEFT JOIN payments p ON p.enrollment_id = e.id
      ORDER BY c.id, e.id`, [PAYMENT_STATUS.PAID]);
  },
});
