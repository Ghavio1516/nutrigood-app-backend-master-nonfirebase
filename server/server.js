const Hapi = require('@hapi/hapi');
const routes = require('../routes/routes'); // Pastikan file ini ada dan isinya benar

const init = async () => {
    const server = Hapi.server({
        port: 8080,
        host: '127.0.0.1',
        routes: {
            cors: {
                origin: ['*'], // Mengizinkan CORS dari semua origin
            },
        },
    });

    // Menambahkan rute dari file routes
    try {
        server.route(routes);
    } catch (error) {
        console.error('Error saat menambahkan rute:', error.message);
        process.exit(1);
    }

    // Menjalankan server
    try {
        await server.start();
        console.log(`Server berjalan pada ${server.info.uri}`);
    } catch (error) {
        console.error('Error saat memulai server:', error.message);
        process.exit(1);
    }
};

// Tangkap unhandled rejection
process.on('unhandledRejection', (err) => {
    console.error('Unhandled Rejection:', err);
    process.exit(1);
});

init();
