const verifyToken = require('../middleware/auth');

const {
  addProductHandler,
  registerUserHandler,
  loginUserHandler,
  getProductsHandler,
  getProductByIdHandler,
  deleteProductByIdHandler,
  getTodayProductsHandler,
  getUserDetailsHandler,
  uploadPhotoHandler
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
        handler: getProductsHandler,
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
    {
      method: 'GET',
      path: '/users/details',
      handler: getUserDetailsHandler, 
      options: { pre: [{ method: verifyToken }] },
    },
    {
        method: 'POST',
        path: '/upload-photo',
        handler: uploadPhotoHandler, // Tambahkan handler ini di langkah berikutnya
        options: {
            pre: [{ method: verifyToken }], // Gunakan middleware untuk autentikasi
            payload: {
                maxBytes: 10 * 1024 * 1024, // Maksimal ukuran file 10 MB
                output: 'data',
                parse: true,
            },
        },
    },
    
];

module.exports = routes;
