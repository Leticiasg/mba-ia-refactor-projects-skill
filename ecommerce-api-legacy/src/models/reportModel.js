const { PAYMENT_STATUS } = require('../config/settings');

module.exports = (db) => ({
  async financialReport() {
    const rows = await db.allAsync(`
      SELECT c.id AS course_id, c.title, e.id AS enrollment_id, u.name AS student, p.amount, p.status
      FROM courses c
      LEFT JOIN enrollments e ON e.course_id = c.id
      LEFT JOIN users u ON u.id = e.user_id
      LEFT JOIN payments p ON p.enrollment_id = e.id
      ORDER BY c.id, e.id`);

    const report = new Map();
    for (const row of rows) {
      if (!report.has(row.course_id)) report.set(row.course_id, { course: row.title, revenue: 0, students: [] });
      const entry = report.get(row.course_id);
      if (row.enrollment_id === null) continue;
      if (row.status === PAYMENT_STATUS.PAID) entry.revenue += row.amount;
      entry.students.push({ student: row.student || 'Unknown', paid: row.amount || 0 });
    }
    return [...report.values()];
  },
});
