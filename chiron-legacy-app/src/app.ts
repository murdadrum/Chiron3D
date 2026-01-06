import express from 'express';
import { json } from 'body-parser';
import { someMiddleware } from './middleware';
import { someRoute } from './routes';

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware setup
app.use(json());
app.use(someMiddleware);

// Route setup
app.use('/api', someRoute);

// Start the application
app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});