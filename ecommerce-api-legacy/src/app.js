// Composition root: cria o banco, liga models, services, controllers e rotas, e sobe o servidor.
const express = require('express');
const settings = require('./config/settings');
const logger = require('./config/logger');
const { createDatabase, createSchema } = require('./models/database');
const { seed } = require('./models/seed');
const createUserModel = require('./models/userModel');
const createCourseModel = require('./models/courseModel');
const createEnrollmentModel = require('./models/enrollmentModel');
const createPaymentModel = require('./models/paymentModel');
const createAuditLogModel = require('./models/auditLogModel');
const createReportModel = require('./models/reportModel');
const createPaymentService = require('./services/paymentService');
const createCheckoutController = require('./controllers/checkoutController');
const createReportController = require('./controllers/reportController');
const createUserController = require('./controllers/userController');
const checkoutRoutes = require('./views/checkoutRoutes');
const reportRoutes = require('./views/reportRoutes');
const userRoutes = require('./views/userRoutes');
const createRequireAdmin = require('./middlewares/requireAdmin');
const errorHandler = require('./middlewares/errorHandler');

async function start() {
  const db = createDatabase(settings.dbPath);
  await createSchema(db);
  await seed(db);

  const models = {
    userModel: createUserModel(db),
    courseModel: createCourseModel(db),
    enrollmentModel: createEnrollmentModel(db),
    paymentModel: createPaymentModel(db),
    auditLogModel: createAuditLogModel(db),
    reportModel: createReportModel(db),
  };
  const paymentService = createPaymentService({ gatewayKey: settings.paymentGatewayKey, logger });

  const checkoutController = createCheckoutController({ db, ...models, paymentService, logger });
  const reportController = createReportController(models);
  const userController = createUserController({ db, ...models });

  if (!settings.adminToken) logger.warn('ADMIN_TOKEN não definido; rotas administrativas ficam bloqueadas.');
  const requireAdmin = createRequireAdmin(settings.adminToken);

  const app = express();
  app.use(express.json());
  app.use(checkoutRoutes(checkoutController));
  app.use(reportRoutes(reportController, requireAdmin));
  app.use(userRoutes(userController, requireAdmin));
  app.use(errorHandler);

  app.listen(settings.port, () => {
    logger.info(`LMS API rodando na porta ${settings.port}`);
  });
}

start().catch((err) => {
  logger.error('Falha ao iniciar a aplicação', err);
  process.exit(1);
});
