const verifyToken = require('../middleware/auth');

const {
    addProductHandler,
    registerUserHandler,
    loginUserHandler,
    getProductsHandler,
    getProductByIdHandler,
    deleteProductByIdHandler,
    getTodayProductsHandler,
} = require('../handler/handler');

const routes = [
    {
        method: 'POST',
        path: '/products',
        handler: addProductHandler,
        options: { pre: [{ method: verifyToken }] },
    },
    {
        method: 'GET',
        path: '/products',
        handler: getProductsHandler, // Tambahkan handler ini ke handler.js
        options: { pre: [{ method: verifyToken }] },
    },
    {
        method: 'GET',
        path: '/products/{id}',
        handler: getProductByIdHandler,
        options: { pre: [{ method: verifyToken }] },
    },
    {
        method: 'DELETE',
        path: '/products/{id}',
        handler: deleteProductByIdHandler,
        options: { pre: [{ method: verifyToken }] },
    },
    {
        method: 'GET',
        path: '/products/today',
        handler: getTodayProductsHandler,
        options: { pre: [{ method: verifyToken }] },
    },
    {
        method: 'POST',
        path: '/users/register',
        handler: registerUserHandler,
    },
    {
        method: 'POST',
        path: '/users/login',
        handler: loginUserHandler,
    },
];

module.exports = routes;
