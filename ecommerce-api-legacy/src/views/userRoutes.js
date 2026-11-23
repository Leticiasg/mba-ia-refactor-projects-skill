const express = require('express');
const asyncHandler = require('../middlewares/asyncHandler');
const requireAdmin = require('../middlewares/requireAdmin');

module.exports = (userController) => {
  const router = express.Router();

  router.delete('/api/users/:id', requireAdmin, asyncHandler(async (req, res) => {
    res.send(await userController.deleteUser(req.params.id));
  }));

  return router;
};
