const Hapi = require('@hapi/hapi');
const jwt = require('hapi-auth-jwt2'); // Tambahkan ini
const routes = require('../routes/routes');
require('dotenv').config(); // Tambahkan untuk membaca file .env

// Fungsi validasi JWT
const validate = async (decoded, request, h) => {
    if (!decoded.userId) {
        return { isValid: false };
    }
    return { isValid: true };
};

const init = async () => {
    const server = Hapi.server({
        port: 5000,
        host: '0.0.0.0',
        routes: {
            cors: {
                origin: ['*'],
            },
        },
    });

    try {
        // Registrasi plugin hapi-auth-jwt2
        await server.register(jwt);

        // Tambahkan strategi autentikasi JWT
        server.auth.strategy('jwt', 'jwt', {
            key: process.env.JWT_SECRET, // Secret key dari .env
            validate, // Fungsi validasi
            verifyOptions: { algorithms: ['HS256'] },
        });

        // Jadikan strategi JWT sebagai default
        server.auth.default('jwt');

        // Tambahkan rute
        server.route(routes);
    } catch (error) {
        console.error('Error saat menambahkan rute:', error.message);
        process.exit(1);
    }

    try {
        await server.start();
        console.log(`Server berjalan pada ${server.info.uri}`);
    } catch (error) {
        console.error('Error saat memulai server:', error.message);
        process.exit(1);
    }
};

process.on('unhandledRejection', (err) => {
    console.error('Unhandled Rejection:', err);
    process.exit(1);
});

init();
