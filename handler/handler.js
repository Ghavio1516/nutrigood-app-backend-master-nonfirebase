const data = require('../database/database');
const bcrypt = require('bcrypt');
const crypto = require('crypto');
const jwt = require('jsonwebtoken');

// Fungsi untuk menghasilkan SHA-256 hash
function generateUniqueId(email) {
    return crypto.createHash('sha256').update(email).digest('hex');
}

const addProductHandler = async (request, h) => {
    const { userId } = request.auth; // Mendapatkan userId dari token JWT
    const { namaProduct, valueProduct } = request.payload;

    const createdAt = new Date().toISOString().slice(0, 19).replace('T', ' ');

    console.log('Add Product Params:', { userId, namaProduct, valueProduct, createdAt });

    try {
        const [result] = await data.query(
            'INSERT INTO products (userId, namaProduct, valueProduct, createdAt) VALUES (?, ?, ?, ?)',
            [userId, namaProduct, valueProduct, createdAt]
        );

        return h.response({
            status: 'success',
            message: 'Product added successfully',
            data: { id: result.insertId },
        }).code(201);
    } catch (error) {
        console.error('Error adding product:', error.message);
        return h.response({ status: 'fail', message: 'Failed to add product' }).code(500);
    }
};


// Handler untuk mendapatkan semua produk
const getProductsHandler = async (request, h) => {
    const { userId } = request.auth;

    try {
        const [rows] = await data.query(
            'SELECT * FROM products WHERE userId = ? ORDER BY createdAt DESC',
            [userId]
        );
        return h.response({
            status: 'success',
            data: rows,
        }).code(200);
    } catch (error) {
        console.error(error);
        return h.response({ status: 'fail', message: 'Failed to fetch products' }).code(500);
    }
};

// Handler untuk mendapatkan produk berdasarkan ID
const getProductByIdHandler = async (request, h) => {
    const { id } = request.params;

    try {
        const [rows] = await data.query(
            'SELECT * FROM products WHERE id = ?',
            [id]
        );

        if (rows.length === 0) {
            return h.response({ status: 'fail', message: 'Product not found' }).code(404);
        }

        return h.response({
            status: 'success',
            data: rows[0],
        }).code(200);
    } catch (error) {
        console.error(error);
        return h.response({ status: 'fail', message: 'Failed to fetch product' }).code(500);
    }
};

// Handler untuk menghapus produk berdasarkan ID
const deleteProductByIdHandler = async (request, h) => {
    const { id } = request.params;

    try {
        const [result] = await data.query(
            'DELETE FROM products WHERE id = ?',
            [id]
        );

        if (result.affectedRows === 0) {
            return h.response({ status: 'fail', message: 'Product not found' }).code(404);
        }

        return h.response({ status: 'success', message: 'Product deleted successfully' }).code(200);
    } catch (error) {
        console.error(error);
        return h.response({ status: 'fail', message: 'Failed to delete product' }).code(500);
    }
};

// Handler untuk mendapatkan produk hari ini
const getTodayProductsHandler = async (request, h) => {
    const { userId } = request.auth;
    const today = new Date().toISOString().slice(0, 10);

    try {
        const [rows] = await data.query(
            'SELECT * FROM products WHERE userId = ? AND DATE(createdAt) = ? ORDER BY createdAt DESC',
            [userId, today]
        );

        return h.response({
            status: 'success',
            data: rows,
        }).code(200);
    } catch (error) {
        console.error(error);
        return h.response({ status: 'fail', message: 'Failed to fetch today\'s products' }).code(500);
    }
};

module.exports = {
    addProductHandler,
    registerUserHandler,
    loginUserHandler,
    getProductsHandler,
    getProductByIdHandler,
    deleteProductByIdHandler,
    getTodayProductsHandler,
};
