const express = require('express');
const asyncHandler = require('../middlewares/asyncHandler');
const requireAdmin = require('../middlewares/requireAdmin');

module.exports = (reportController) => {
  const router = express.Router();

  router.get('/api/admin/financial-report', requireAdmin, asyncHandler(async (req, res) => {
    res.json(await reportController.financialReport());
  }));

  return router;
};
