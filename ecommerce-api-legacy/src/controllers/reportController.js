module.exports = ({ reportModel }) => ({
  async financialReport() {
    const [courses, students] = await Promise.all([
      reportModel.revenueByCourse(),
      reportModel.studentsByCourse(),
    ]);

    const report = new Map(courses.map((course) => [
      course.course_id,
      { course: course.title, revenue: course.revenue, students: [] },
    ]));

    for (const row of students) {
      const entry = report.get(row.course_id);
      if (!entry) continue;
      entry.students.push({ student: row.student || 'Unknown', paid: row.amount || 0 });
    }

    return [...report.values()];
  },
});
