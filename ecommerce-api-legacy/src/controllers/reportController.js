module.exports = ({ reportModel }) => ({
  async financialReport() {
    const rows = await reportModel.financialRows();
    const report = new Map();
    for (const row of rows) {
      if (!report.has(row.course_id)) {
        report.set(row.course_id, { course: row.title, revenue: row.revenue || 0, students: [] });
      }
      if (row.enrollment_id !== null) {
        report.get(row.course_id).students.push({ student: row.student || 'Unknown', paid: row.amount || 0 });
      }
    }
    return [...report.values()];
  },
});
