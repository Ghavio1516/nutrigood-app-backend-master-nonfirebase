const data = require('../database/database');
const bcrypt = require('bcrypt');
const crypto = require('crypto');
const jwt = require('jsonwebtoken');

// Fungsi untuk menghasilkan SHA-256 hash
function generateUniqueId(email) {
    return crypto.createHash('sha256').update(email).digest('hex');
}

// Handler untuk menambahkan produk
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
    console.log('Fetching products for userId:', userId); // Log userId untuk debugging
    try {
        const [rows] = await data.query(
            'SELECT * FROM products WHERE userId = ? ORDER BY createdAt DESC',
            [userId]
        );

        console.log('Fetched products:', rows);

        return h.response({
            status: 'success',
            data: {
                products: rows, // Bungkus data dalam objek `products`
            },
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

// Handler untuk registrasi user
const registerUserHandler = async (request, h) => {
    const { email, password, name, age, diabetes } = request.payload;

    // Validasi input
    if (!email || !password || !name || typeof age === 'undefined') {
        console.error('Missing fields:', { email, password, name, age });
        return h.response({
            status: 'fail',
            message: 'All fields (email, password, name, age) are required',
        }).code(400);
    }

    if (diabetes && !['yes', 'no'].includes(diabetes.toLowerCase())) {
        console.error('Invalid diabetes value:', diabetes);
        return h.response({
            status: 'fail',
            message: 'Diabetes must be either "yes" or "no"',
        }).code(400);
    }

    // Hash password
    const saltRounds = 10;
    const hashedPassword = await bcrypt.hash(password, saltRounds);

    // Generate unique identifier from email
    const userId = generateUniqueId(email);
    const createdAt = new Date().toISOString().slice(0, 19).replace('T', ' ');

    // Tetapkan nilai diabetes sebagai string
    const diabetesValue = diabetes ? diabetes.toLowerCase() === 'yes' ? 'Yes' : 'No' : 'No';

    console.log('Register User Params:', {
        userId,
        email,
        hashedPassword,
        name,
        age,
        diabetesValue,
        createdAt,
    });

    try {
        await data.query(
            'INSERT INTO users (id, email, password, name, age, diabetes, createdAt) VALUES (?, ?, ?, ?, ?, ?, ?)',
            [userId, email, hashedPassword, name, age, diabetesValue, createdAt]
        );

        return h.response({
            status: 'success',
            message: 'User registered successfully',
            data: { userId },
        }).code(201);
    } catch (error) {
        if (error.code === 'ER_DUP_ENTRY') {
            console.error('Error: Duplicate entry');
            return h.response({
                status: 'fail',
                message: 'User already exists',
            }).code(409);
        }

        console.error('Error registering user:', error.message);
        return h.response({ status: 'fail', message: `Failed to register user: ${error.message}` }).code(500);
    }
};

const getUserDetailsHandler = async (request, h) => {
    const token = request.headers.authorization?.split(' ')[1];
    if (!token) {
        return h.response({ status: 'fail', message: 'Token is missing' }).code(401);
    }

    try {
        const decoded = jwt.verify(token, process.env.JWT_SECRET);
        const userId = decoded.userId;

        console.log("Decoded UserID:", userId);

        const [rows] = await data.query('SELECT name AS username, email FROM users WHERE id = ?', [userId]);
        console.log("Database Query Result:", rows);

        if (rows.length === 0) {
            return h.response({ status: 'fail', message: 'User not found' }).code(404);
        }

        const response = {
            username: rows[0].username,
            email: rows[0].email,
        };

        return h.response(response).code(200);
    } catch (error) {
        console.error('Error fetching user details:', error.message);
        return h.response({ status: 'fail', message: 'Invalid or expired token' }).code(401);
    }
};




// Handler untuk login user
const loginUserHandler = async (request, h) => {
    const { email, password } = request.payload;

    try {
        const [rows] = await data.query(
            'SELECT * FROM users WHERE email = ?',
            [email]
        );

        if (rows.length === 0) {
            return h.response({
                status: 'fail',
                message: 'User not found',
            }).code(404);
        }

        const user = rows[0];

        // Compare hashed password
        const isValidPassword = await bcrypt.compare(password, user.password);
        if (!isValidPassword) {
            return h.response({
                status: 'fail',
                message: 'Invalid password',
            }).code(401);
        }

        // Generate token
        const token = jwt.sign(
            { userId: user.id },
            process.env.JWT_SECRET,
            { expiresIn: '1h' } // Token berlaku selama 1 jam
        );
        console.log("Generated token:", token);

        return h.response({
            status: 'success',
            message: 'Login successful',
            data: { token },
        }).code(200);
    } catch (error) {
        console.error(error);
        return h.response({ status: 'fail', message: `Failed to login: ${error.message}` }).code(500);
    }
};

const fs = require('fs');
const path = require('path');
const tf = require('@tensorflow/tfjs-node'); // TensorFlow.js untuk Node.js

// Fungsi untuk memuat model TensorFlow (dari .h5)
const loadModel = async (modelPath) => {
    return await tf.node.loadLayersModel(`file://${modelPath}`);
};

// Fungsi untuk memproses gambar menjadi tensor
const preprocessImage = (imageBuffer) => {
    return tf.node
        .decodeImage(imageBuffer, 3) // 3 channel untuk RGB
        .resizeBilinear([128, 128]) // Sesuaikan ukuran input dengan model Anda
        .toFloat()
        .div(255.0) // Normalisasi ke [0, 1]
        .expandDims(0); // Tambahkan batch dimension
};

// Handler upload foto dan prediksi dengan model
const uploadPhotoHandler = async (request, h) => {
    const { userId } = request.auth; // Dapatkan userId dari token JWT
    const { base64Image } = request.payload;

    if (!base64Image) {
        return h.response({
            status: 'fail',
            message: 'Missing base64Image',
        }).code(400);
    }

    // Validasi format Base64 untuk JPEG
    if (!base64Image.startsWith('data:image/jpeg;base64,')) {
        return h.response({
            status: 'fail',
            message: 'Invalid image format. Only JPEG is supported.',
        }).code(400);
    }

    try {
        // Dekode Base64 ke buffer
        const base64Data = base64Image.split(',')[1];
        const buffer = Buffer.from(base64Data, 'base64');

        // Tentukan folder penyimpanan
        const savedFolder = path.join(__dirname, '../saved_photos');
        if (!fs.existsSync(savedFolder)) {
            fs.mkdirSync(savedFolder, { recursive: true });
        }

        // Format nama file
        const now = new Date();
        const time = now.toTimeString().split(' ')[0].replace(/:/g, ''); // HHMMSS
        const date = now.toISOString().slice(0, 10).replace(/-/g, '').slice(2); // DDMMYY
        const finalFileName = `${userId}_${time}-${date}.jpg`;
        const filePath = path.join(savedFolder, finalFileName);

        // Simpan file ke folder
        fs.writeFileSync(filePath, buffer);

        console.log(`Photo saved at ${filePath}`);

        // Path model
        const modelPath = path.join(__dirname, '../model/CustomCnn_model.h5');

        // Muat model
        console.log('Loading model...');
        const model = await loadModel(modelPath);

        console.log('Model loaded. Preprocessing image...');
        const tensor = preprocessImage(buffer);

        console.log('Predicting with model...');
        const predictions = model.predict(tensor).arraySync();

        console.log('Prediction result:', predictions);

        // Mengubah output prediksi menjadi string teks (sesuaikan dengan model Anda)
        const nutritionText = predictions
            .map((line) => line.join(' ')) // Menggabungkan teks pada setiap baris
            .join('\n'); // Tambahkan newline antar baris

        return h.response({
            status: 'success',
            message: 'Photo uploaded and processed successfully',
            data: {
                filePath,
                nutritionFacts: nutritionText,
            },
        }).code(201);
    } catch (error) {
        console.error('Error uploading and processing photo:', error.message);
        return h.response({
            status: 'fail',
            message: 'Failed to upload and process photo',
        }).code(500);
    }
};

// Ekspor semua handler
module.exports = {
    addProductHandler,
    registerUserHandler,
    loginUserHandler,
    getProductsHandler,
    getProductByIdHandler,
    deleteProductByIdHandler,
    getTodayProductsHandler,
    getUserDetailsHandler,
    uploadPhotoHandler,
};
