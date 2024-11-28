const jwt = require('jsonwebtoken');

const verifyToken = (req, res, next) => {
    const authHeader = req.headers.authorization;

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return res.status(401).json({ status: 'fail', message: 'Unauthorized' });
    }

    const token = authHeader.split(' ')[1];

    try {
        const decodedToken = jwt.verify(token, process.env.JWT_SECRET);
        req.user = { userId: decodedToken.userId, username: decodedToken.username }; // Pastikan token berisi `username`
        next();
    } catch (error) {
        console.error('Token verification failed:', error.message);
        return res.status(401).json({ status: 'fail', message: 'Invalid token' });
    }
};

module.exports = verifyToken;
