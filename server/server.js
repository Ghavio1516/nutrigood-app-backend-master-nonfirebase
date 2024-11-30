const Hapi = require('@hapi/hapi');
const routes = require('../routes/routes');

const init = async () => {
    const server = Hapi.server({
        port: 5000,
        host: '0.0.0.0',
        routes: {
            cors: {
                origin: ['*'], 
            },
            payload: {
                maxBytes: 10485760 // 10 MB
            }
        },
    });

    try {
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
