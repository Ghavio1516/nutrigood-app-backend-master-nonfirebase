const jwt = require('jsonwebtoken');

// Middleware untuk memverifikasi token JWT
const verifyToken = async (request, h) => {
    const authHeader = request.headers.authorization;

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return h.response({ status: 'fail', message: 'Unauthorized' }).code(401).takeover();
    }

    const token = authHeader.split(' ')[1];

    try {
        // Verifikasi token menggunakan secret key
        const decodedToken = jwt.verify(token, process.env.JWT_SECRET);
        request.auth = { userId: decodedToken.userId }; // Set userId ke request.auth
        return h.continue;
    } catch (error) {
        console.error('Token verification failed:', error.message);
        return h.response({ status: 'fail', message: 'Invalid token' }).code(401).takeover();
    }
};

module.exports = verifyToken;
